"""
对话历史API - 保存、获取、删除对话
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
import json
import time
from datetime import datetime

from models.database import get_db, Conversation, ChatMessage, UserActivity
from services.rag_service import EnhancedRAGService, EnhancedVectorStore
from services.ai_service import AIService
from services.vector_store import VectorStore

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# 数据模型
class ConversationCreate(BaseModel):
    title: Optional[str] = "新对话"
    user_id: Optional[str] = "anonymous"

class MessageCreate(BaseModel):
    content: str
    role: str = "user"

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    stream: bool = False

class ConversationResponse(BaseModel):
    id: str
    title: str
    user_id: str
    created_at: str
    updated_at: str
    message_count: int

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: str
    latency_ms: int

# 初始化服务
vector_store = EnhancedVectorStore()
ai_service = AIService()
rag_service = EnhancedRAGService(vector_store, ai_service)

def get_or_create_conversation(db: Session, conversation_id: Optional[str], user_id: str = "anonymous"):
    """获取或创建对话"""
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            return conv
    
    # 创建新对话
    conv = Conversation(
        id=str(uuid.uuid4()),
        title="新对话",
        user_id=user_id
    )
    db.add(conv)
    db.commit()
    return conv

def log_activity(db: Session, user_id: str, activity_type: str, details: dict):
    """记录用户活动"""
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        details=json.dumps(details, ensure_ascii=False)
    )
    db.add(activity)
    db.commit()

# ==================== 对话管理API ====================

@router.post("", response_model=ConversationResponse)
def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    """创建新对话"""
    conv = Conversation(
        id=str(uuid.uuid4()),
        title=request.title,
        user_id=request.user_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    
    log_activity(db, request.user_id, "create_conversation", {"conversation_id": conv.id})
    
    return {
        "id": conv.id,
        "title": conv.title,
        "user_id": conv.user_id,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "message_count": 0
    }

@router.get("")
def get_conversations(
    user_id: Optional[str] = Query(default="anonymous"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: Session = Depends(get_db)
):
    """获取对话列表"""
    query = db.query(Conversation).filter(Conversation.user_id == user_id)
    total = query.count()
    
    conversations = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "user_id": c.user_id,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "message_count": len(c.messages)
            }
            for c in conversations
        ]
    }

@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """获取对话详情及消息列表"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "id": conv.id,
        "title": conv.title,
        "user_id": conv.user_id,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources) if m.sources else None,
                "created_at": m.created_at.isoformat(),
                "latency_ms": m.latency_ms
            }
            for m in messages
        ]
    }

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """删除对话及其消息"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db.delete(conv)
    db.commit()
    
    log_activity(db, conv.user_id, "delete_conversation", {"conversation_id": conversation_id})
    
    return {"message": "删除成功", "id": conversation_id}

@router.patch("/{conversation_id}")
def update_conversation_title(
    conversation_id: str,
    title: str,
    db: Session = Depends(get_db)
):
    """更新对话标题"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conv.title = title
    conv.updated_at = datetime.now()
    db.commit()
    
    return {
        "id": conv.id,
        "title": conv.title,
        "updated_at": conv.updated_at.isoformat()
    }

# ==================== 消息API ====================

@router.post("/{conversation_id}/messages")
def add_message(
    conversation_id: str,
    request: MessageCreate,
    db: Session = Depends(get_db)
):
    """添加消息到对话"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=request.role,
        content=request.content
    )
    db.add(message)
    
    # 更新对话时间
    conv.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat()
    }

# ==================== AI问答API (支持流式) ====================

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """AI问答（非流式）"""
    start_time = time.time()
    
    # 获取或创建对话
    conv = get_or_create_conversation(db, request.conversation_id)
    
    # 获取历史消息
    history_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conv.id
    ).order_by(ChatMessage.created_at).all()
    
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages[-5:]  # 最近5轮
    ]
    
    # 保存用户消息
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=request.query
    )
    db.add(user_message)
    
    # 生成回答
    result = rag_service.chat(request.query, chat_history)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # 保存助手消息
    assistant_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="assistant",
        content=result['answer'],
        sources=json.dumps(result.get('sources', []), ensure_ascii=False),
        latency_ms=latency_ms
    )
    db.add(assistant_message)
    
    # 更新对话时间
    conv.updated_at = datetime.now()
    
    # 更新标题（如果是第一轮对话）
    if len(history_messages) == 0:
        conv.title = request.query[:30] + "..." if len(request.query) > 30 else request.query
    
    db.commit()
    
    # 记录活动
    log_activity(db, conv.user_id, "chat", {
        "conversation_id": conv.id,
        "query": request.query,
        "latency_ms": latency_ms
    })
    
    return {
        "conversation_id": conv.id,
        "message_id": assistant_message.id,
        "answer": result['answer'],
        "sources": result.get('sources', []),
        "latency_ms": latency_ms
    }

@router.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """AI问答（流式SSE）"""
    start_time = time.time()
    
    # 获取或创建对话
    conv = get_or_create_conversation(db, request.conversation_id)
    
    # 获取历史消息
    history_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conv.id
    ).order_by(ChatMessage.created_at).all()
    
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages[-5:]  # 最近5轮
    ]
    
    # 保存用户消息
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=request.query
    )
    db.add(user_message)
    db.commit()
    
    def generate():
        """生成流式响应"""
        full_answer = ""
        message_id = str(uuid.uuid4())
        
        # 首先发送消息ID
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id}, ensure_ascii=False)}\n\n"
        
        # 检索相关文档
        context = rag_service.retrieve(request.query)
        
        # 模拟流式生成（使用本地模式分词）
        answer = result = rag_service.generate_answer(request.query, context)
        answer_text = answer['answer']
        
        # 按句子分割并流式发送
        import re
        sentences = re.split(r'([。！？\.\n])', answer_text)
        
        for sentence in sentences:
            if sentence.strip():
                full_answer += sentence
                yield f"data: {json.dumps({'type': 'content', 'text': sentence}, ensure_ascii=False)}\n\n"
                time.sleep(0.05)  # 模拟延迟
        
        # 保存完整回答到数据库
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 需要在生成器外保存，使用上下文管理器
        assistant_message = ChatMessage(
            id=message_id,
            conversation_id=conv.id,
            role="assistant",
            content=full_answer,
            sources=json.dumps(answer.get('sources', []), ensure_ascii=False),
            latency_ms=latency_ms
        )
        
        # 使用新的会话保存
        from models.database import get_db_session
        db_session = get_db_session()
        try:
            db_session.add(assistant_message)
            
            # 更新对话
            conv_update = db_session.query(Conversation).filter(Conversation.id == conv.id).first()
            conv_update.updated_at = datetime.now()
            if len(history_messages) == 0:
                conv_update.title = request.query[:30] + "..." if len(request.query) > 30 else request.query
            
            db_session.commit()
        finally:
            db_session.close()
        
        # 发送完成消息
        end_data = json.dumps({
            'type': 'end',
            'message_id': message_id,
            'sources': answer.get('sources', []),
            'latency_ms': latency_ms
        }, ensure_ascii=False)
        yield f"data: {end_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )