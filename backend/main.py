"""
AI知识库API - 主入口
支持：文档管理、AI问答、对话历史、数据统计
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn
import uuid
import os
import time
import json
from datetime import datetime
from contextlib import asynccontextmanager

from models.database import init_db, get_db, get_db_session, Document, Conversation, ChatMessage, UserActivity, Tag, DocumentTag
from services.document_parser import DocumentParser
from services.vector_store import VectorStore
from services.ai_service import AIService
from services.rag_service import EnhancedRAGService, EnhancedVectorStore
from services.integration.ragflow_client import get_ragflow_service
from services.classification_service import analyze_document, classify_document

# 导入API路由
from api import conversations, stats, ocr, categories, auth, users, audit, auth_management
from api.ragflow_api import router as ragflow_router
from kg_module.api import routes as kg_routes
from cim_module import cim_router, dashboard_router

# 导入权限模块
from core.security import get_current_user, require_permissions, Permission
from core.audit import audit_middleware

# 初始化
init_db()
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

# 初始化CIM数据表
from models.cim_models import init_cim_tables
init_cim_tables()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("🚀 AI知识库服务启动中...")
    
    # 初始化全局服务
    app.state.vector_store = EnhancedVectorStore()
    app.state.ai_service = AIService()
    app.state.rag_service = EnhancedRAGService(app.state.vector_store, app.state.ai_service)
    
    print("✅ 服务初始化完成")
    yield
    # 关闭时执行
    print("🛑 服务关闭中...")

app = FastAPI(
    title="AI知识库API", 
    version="2.0.0",
    description="AI知识库MVP - 支持对话历史、流式响应和数据统计",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册API路由
app.include_router(conversations.router)
app.include_router(stats.router)
app.include_router(ocr.router)
app.include_router(categories.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(audit.router)
# app.include_router(auth_management.router)  # TODO: 修复后启用
app.include_router(kg_routes.router)
app.include_router(cim_router)
app.include_router(dashboard_router)
app.include_router(ragflow_router)  # RAGFlow 集成

# 初始化服务
parser = DocumentParser()
vector_store = VectorStore()
ai_service = AIService()

# 数据模型
class DocumentCreate(BaseModel):
    title: str
    category: Optional[str] = "未分类"
    tags: Optional[str] = ""

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    stream: bool = False

class SearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None
    limit: int = 10

# API端点
@app.get("/")
def root():
    return {"message": "AI知识库API服务运行中", "version": "2.0.0"}

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """健康检查 - 包含数据库状态"""
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # 获取基础统计
    stats = {
        "documents": db.query(Document).count(),
        "conversations": db.query(Conversation).count(),
        "messages": db.query(ChatMessage).count()
    }
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "stats": stats
    }

# 文档上传
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("未分类"),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    try:
        doc_id = str(uuid.uuid4())
        file_path = f"uploads/{doc_id}_{file.filename}"
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 解析文档
        content_text = parser.parse(file_path, file.filename)
        
        # 存入数据库
        doc = Document(
            id=doc_id,
            filename=file.filename,
            title=file.filename.rsplit('.', 1)[0],
            content=content_text,
            category=category,
            tags=tags,
            file_path=file_path,
            file_size=len(content),
            file_type=file.filename.split('.')[-1].lower(),
            status='active'
        )
        db.add(doc)
        db.commit()
        
        # 存入向量库
        app.state.vector_store.add_document(doc_id, content_text, {
            "title": doc.title,
            "category": category,
            "tags": tags
        })
        
        # 记录活动
        activity = UserActivity(
            user_id="anonymous",
            activity_type="upload",
            details=json.dumps({"doc_id": doc_id, "filename": file.filename})
        )
        db.add(activity)
        db.commit()
        
        return {
            "id": doc_id,
            "filename": file.filename,
            "title": doc.title,
            "content_preview": content_text[:200] + "..." if len(content_text) > 200 else content_text,
            "category": category,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 批量上传
@app.post("/api/documents/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """批量上传文档"""
    results = []
    for file in files:
        try:
            doc_id = str(uuid.uuid4())
            file_path = f"uploads/{doc_id}_{file.filename}"
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            content_text = parser.parse(file_path, file.filename)
            
            doc = Document(
                id=doc_id,
                filename=file.filename,
                title=file.filename.rsplit('.', 1)[0],
                content=content_text,
                category="工艺文档",
                file_path=file_path,
                file_size=len(content),
                file_type=file.filename.split('.')[-1].lower(),
                status='active'
            )
            db.add(doc)
            db.commit()
            
            app.state.vector_store.add_document(doc_id, content_text, {
                "title": doc.title,
                "category": "工艺文档"
            })
            
            results.append({
                "id": doc_id,
                "filename": file.filename,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "success": len([r for r in results if r.get("status") == "success"]),
        "results": results
    }

# 获取文档列表
@app.get("/api/documents")
def get_documents(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if category:
        query = query.filter(Document.category == category)
    
    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "title": d.title,
                "category": d.category,
                "tags": d.tags,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "created_at": d.created_at.isoformat(),
                "status": d.status
            }
            for d in docs
        ]
    }

# 获取文档详情
@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "content": doc.content,
        "category": doc.category,
        "tags": doc.tags,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat()
    }

# 搜索
@app.post("/api/search")
def search(request: SearchRequest, db: Session = Depends(get_db)):
    try:
        # 记录搜索活动
        activity = UserActivity(
            user_id="anonymous",
            activity_type="search",
            details=json.dumps({"keyword": request.keyword})
        )
        db.add(activity)
        db.commit()
        
        results = app.state.vector_store.search(request.keyword, request.limit)
        return {
            "keyword": request.keyword,
            "total": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI问答（新增强化版本，支持对话历史）
@app.post("/api/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    # 获取或创建对话
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    
    if not conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=request.query[:30] + "..." if len(request.query) > 30 else request.query
        )
        db.add(conversation)
        db.commit()
    
    # 保存用户消息
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=request.query
    )
    db.add(user_message)
    
    # 获取历史消息
    history = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).order_by(ChatMessage.created_at).all()
    
    chat_history = [
        {"role": h.role, "content": h.content}
        for h in history[-5:]  # 最近5轮
    ]
    
    # 使用增强RAG服务
    result = app.state.rag_service.chat(request.query, chat_history)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # 保存助手消息
    assistant_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=result['answer'],
        sources=json.dumps(result.get('sources', []), ensure_ascii=False),
        latency_ms=latency_ms
    )
    db.add(assistant_message)
    
    # 更新对话时间
    conversation.updated_at = datetime.now()
    
    # 记录用户活动
    activity = UserActivity(
        user_id=conversation.user_id,
        activity_type="chat",
        details=json.dumps({
            "conversation_id": conversation.id,
            "query": request.query,
            "latency_ms": latency_ms
        }, ensure_ascii=False)
    )
    db.add(activity)
    
    db.commit()
    
    return {
        "answer": result['answer'],
        "sources": result.get('sources', []),
        "conversation_id": conversation.id,
        "message_id": assistant_message.id,
        "latency_ms": latency_ms
    }

# 流式AI问答
@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """流式AI问答（SSE）"""
    start_time = time.time()
    
    # 获取或创建对话
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    
    if not conversation:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=request.query[:30] + "..." if len(request.query) > 30 else request.query
        )
        db.add(conversation)
        db.commit()
    
    # 保存用户消息
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=request.query
    )
    db.add(user_message)
    db.commit()
    
    message_id = str(uuid.uuid4())
    
    def generate():
        full_answer = ""
        
        # 发送开始标记
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id}, ensure_ascii=False)}\n\n"
        
        # 检索和生成 - 使用 RAGFlow
        try:
            ragflow_svc = get_ragflow_service()
            ragflow_result = ragflow_svc.chat(
                ["fb6027c82b0411f190880e97cf935568"],  # 默认数据集
                request.query,
                top_k=5
            )
            if ragflow_result.get("code") == 0:
                answer_text = ragflow_result.get("data", {}).get("answer", "")
                # 清理RAGFlow原始标记（如 ##0$$）
                import re
                answer_text = re.sub(r'##\d+\$\$', '', answer_text).strip()
                reference = ragflow_result.get("data", {}).get("reference", {})
                sources = reference.get("chunks", []) if isinstance(reference, dict) else []
            else:
                answer_text = f"RAGFlow错误: {ragflow_result.get('message', '未知错误')}"
                sources = []
            result = {'answer': answer_text, 'sources': sources}
            
            # 按句子分割
            import re
            sentences = re.split(r'([。！？\.\n])', answer_text)
            
            for sentence in sentences:
                if sentence.strip():
                    full_answer += sentence
                    yield f"data: {json.dumps({'type': 'content', 'text': sentence}, ensure_ascii=False)}\n\n"
                    time.sleep(0.03)  # 模拟流式延迟
            
            # 保存完整回答
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 使用新会话保存
            db_session = get_db_session()
            try:
                assistant_message = ChatMessage(
                    id=message_id,
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_answer,
                    sources=json.dumps(sources, ensure_ascii=False),
                    latency_ms=latency_ms
                )
                db_session.add(assistant_message)
                
                conv = db_session.query(Conversation).filter(Conversation.id == conversation.id).first()
                conv.updated_at = datetime.now()
                
                db_session.commit()
            finally:
                db_session.close()
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end', 'sources': sources, 'latency_ms': latency_ms}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# 删除文档
@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    # 删除数据库记录
    db.delete(doc)
    db.commit()
    
    # 删除向量
    app.state.vector_store.delete_document(doc_id)
    
    return {"message": "删除成功", "id": doc_id}

# ========== 新增：表格解析与参数提取 ==========

class TableParseRequest(BaseModel):
    file_path: str
    filename: str

class ParamExtractRequest(BaseModel):
    file_path: str
    filename: str

@app.post("/api/documents/parse-tables")
async def parse_tables(request: TableParseRequest):
    """
    解析文档中的表格
    支持Excel(.xlsx/.xls)和PDF文件
    """
    try:
        parser = DocumentParser()
        result = parser.parse_with_tables(request.file_path, request.filename)
        
        return {
            "success": True,
            "text": result['text'][:5000] if result['text'] else "",
            "tables": result['tables'],
            "table_count": len(result['tables']),
            "metadata": result['metadata']
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/documents/extract-params")
async def extract_params(request: ParamExtractRequest):
    """
    从工艺参数文档中提取结构化参数
    返回: [{param_name, value, unit, param_type, source}]
    """
    try:
        parser = DocumentParser()
        params = parser.extract_params(request.file_path, request.filename)
        
        return {
            "success": True,
            "params": params,
            "param_count": len(params)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)