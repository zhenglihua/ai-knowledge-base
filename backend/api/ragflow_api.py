"""
RAGFlow 集成 API
v0.8.1
专业 RAG 问答接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import tempfile

from services.integration import (
    get_ragflow_service,
    is_ragflow_available
)
from services.document_summary_service import get_summary_service


router = APIRouter(prefix="/api/ragflow", tags=["RAGFlow专业RAG"])


# ========== 请求/响应模型 ==========

class DatasetCreateRequest(BaseModel):
    """创建数据集请求"""
    name: str
    description: str = ""
    chunk_method: str = "naive"
    permission: str = "me"


class ChatRequest(BaseModel):
    """对话请求"""
    dataset_ids: List[str]
    query: str
    top_k: int = 10


class RetrievalRequest(BaseModel):
    """检索请求"""
    dataset_ids: List[str]
    query: str
    top_k: int = 10


# ========== 状态接口 ==========

@router.get("/status")
async def get_status():
    """获取 RAGFlow 连接状态"""
    available = is_ragflow_available()
    
    if available:
        try:
            service = get_ragflow_service()
            datasets = service.list_datasets()
            return {
                "status": "connected",
                "dataset_count": len(datasets),
                "message": "RAGFlow 服务正常"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    else:
        return {
            "status": "disconnected",
            "message": "RAGFlow 服务不可用，请检查配置"
        }


@router.get("/config")
async def get_config():
    """获取 RAGFlow 配置信息"""
    from dotenv import load_dotenv
    load_dotenv()
    import os
    
    return {
        "url": os.getenv("RAGFLOW_URL", "http://localhost:9380"),
        "api_key_set": bool(os.getenv("RAGFLOW_API_KEY")),
        "timeout": os.getenv("RAGFLOW_TIMEOUT", "60")
    }


# ========== 数据集管理 ==========

@router.post("/datasets")
async def create_dataset(request: DatasetCreateRequest):
    """创建数据集"""
    try:
        service = get_ragflow_service()
        result = service.create_dataset(
            name=request.name,
            description=request.description,
            chunk_method=request.chunk_method,
            permission=request.permission
        )
        
        if result.get("code") == 0:
            return {
                "success": True,
                "dataset": result.get("data")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets():
    """获取数据集列表"""
    try:
        service = get_ragflow_service()
        datasets = service.list_datasets()
        return {
            "datasets": datasets,
            "count": len(datasets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取数据集详情"""
    try:
        service = get_ragflow_service()
        result = service.get_dataset(dataset_id)
        
        if result.get("code") == 0:
            return {
                "dataset": result.get("data")
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("message"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """删除数据集"""
    try:
        service = get_ragflow_service()
        success = service.delete_dataset(dataset_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 文档管理 ==========

@router.post("/datasets/{dataset_id}/documents")
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(...),
    chunk_method: str = "naive"
):
    """上传文档到数据集"""
    try:
        # 保存上传文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            service = get_ragflow_service()
            result = service.upload_document(dataset_id, tmp_path, chunk_method)
            
            return {
                "success": result.get("code") == 0,
                "document": result.get("data"),
                "message": result.get("message")
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/documents")
async def list_documents(dataset_id: str):
    """获取数据集文档列表"""
    try:
        service = get_ragflow_service()
        docs = service.list_documents(dataset_id)
        return {
            "documents": docs,
            "count": len(docs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_id}/documents/{doc_id}")
async def delete_document(dataset_id: str, doc_id: str):
    """删除文档"""
    try:
        service = get_ragflow_service()
        success = service.delete_document(dataset_id, doc_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== RAG 问答 ==========

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    RAGFlow 专业问答
    
    基于 RAGFlow 实现的高质量 RAG 问答
    """
    try:
        service = get_ragflow_service()
        
        result = service.chat(
            dataset_ids=request.dataset_ids,
            query=request.query,
            top_k=request.top_k
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieval")
async def retrieval(request: RetrievalRequest):
    """
    RAGFlow 检索
    
    仅检索相关文档片段，不生成回答
    """
    try:
        service = get_ragflow_service()
        
        results = service.retrievals(
            dataset_ids=request.dataset_ids,
            query=request.query,
            top_k=request.top_k
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 一站式文档处理 ==========

class ProcessDocumentRequest(BaseModel):
    """一站式文档处理请求"""
    dataset_name: str
    file: UploadFile = File(...)
    chunk_method: str = "naive"


@router.post("/process")
async def process_document(
    request: ProcessDocumentRequest,
    top_k: int = 5
):
    """
    一站式文档处理
    
    1. 创建/获取数据集
    2. 上传文档
    3. 返回结果
    """
    try:
        service = get_ragflow_service()
        
        # 1. 获取或创建数据集
        datasets = service.list_datasets()
        dataset_id = None
        for d in datasets:
            if d.get("name") == request.dataset_name:
                dataset_id = d.get("id")
                break
        
        if not dataset_id:
            result = service.create_dataset(name=request.dataset_name)
            if result.get("code") == 0:
                dataset_id = result.get("data", {}).get("id")
        
        if not dataset_id:
            raise HTTPException(status_code=500, detail="创建数据集失败")
        
        # 2. 保存上传文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=request.file.filename) as tmp:
            content = await request.file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 3. 上传文档
            result = service.upload_document(
                dataset_id, tmp_path, request.chunk_method
            )
            
            return {
                "success": result.get("code") == 0,
                "dataset_id": dataset_id,
                "document": result.get("data"),
                "message": "文档上传成功"
            }
        finally:
            os.unlink(tmp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 文档摘要 ==========

class GenerateSummaryRequest(BaseModel):
    """生成摘要请求"""
    dataset_id: str
    document_id: str


@router.post("/documents/{document_id}/summary")
async def generate_document_summary(
    document_id: str,
    dataset_id: str
):
    """
    为已上传的文档生成摘要卡片

    摘要包含：
    - 文档摘要（100-150字）
    - 主要章节列表
    - 关键工艺参数
    - 关键设备列表
    - 安全注意事项
    - 文档标签
    """
    try:
        service = get_ragflow_service()

        # 获取文档信息
        docs = service.list_documents(dataset_id)
        doc_info = None
        for d in docs:
            if d.get('id') == document_id:
                doc_info = d
                break

        if not doc_info:
            raise HTTPException(status_code=404, detail="文档未找到")

        filename = doc_info.get('name', '')

        # 获取文档内容（RAGFlow检索或本地文件）
        # 优先尝试从 RAGFlow 检索摘要片段
        try:
            retrieval = service.retrievals(
                dataset_ids=[dataset_id],
                query="文档摘要和关键内容",
                top_k=3
            )
            context = "\n".join([r.get('chunk', {}).get('content', '') for r in retrieval[:3] if isinstance(r, dict)])
        except:
            context = ""

        # 生成摘要
        summary_svc = get_summary_service()

        # 对于 RAGFlow 中的文档，我们尝试用检索到的内容生成摘要
        if context:
            from services.ai_service import get_ai_service
            ai = get_ai_service()

            prompt = f"""你是一个专业的半导体工艺文档分析助手。请为以下文档生成一个简明摘要。

文档名称：{filename}

文档内容：
{context[:3000]}

请按以下JSON格式输出摘要（只输出JSON，不要其他内容）：
{{
    "brief_summary": "100-150字的中文摘要，说明文档的核心内容和目的",
    "main_topics": ["主题1", "主题2", "主题3"],
    "difficulty_level": "基础/进阶/高级",
    "target_audience": "目标读者"
}}"""

            try:
                result = ai.generate_answer(prompt)
                import json as _json
                if "{" in result and "}" in result:
                    json_str = result[result.index("{"):result.rindex("}")+1]
                    data = _json.loads(json_str)

                    return {
                        "success": True,
                        "doc_id": document_id,
                        "filename": filename,
                        "summary": data.get('brief_summary', ''),
                        "main_topics": data.get('main_topics', []),
                        "difficulty_level": data.get('difficulty_level', '未知'),
                        "target_audience": data.get('target_audience', ''),
                        "source": "ragflow_retrieval"
                    }
            except Exception as e:
                pass

        # Fallback：返回基本信息
        return {
            "success": True,
            "doc_id": document_id,
            "filename": filename,
            "summary": f"文档 {filename} 已上传至RAGFlow，可在RAGFlow界面中查看解析进度和内容摘要。",
            "main_topics": [],
            "difficulty_level": "未知",
            "target_audience": "半导体工程师",
            "source": "fallback",
            "note": "建议在RAGFlow中完成文档解析后再生成完整摘要"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-with-summary")
async def process_document_with_summary(
    request: ProcessDocumentRequest,
):
    """
    一站式文档处理（含自动摘要）

    1. 创建/获取数据集
    2. 上传文档
    3. 自动生成摘要卡片
    4. 返回结果
    """
    try:
        service = get_ragflow_service()

        # 1. 获取或创建数据集
        datasets = service.list_datasets()
        dataset_id = None
        for d in datasets:
            if d.get("name") == request.dataset_name:
                dataset_id = d.get("id")
                break

        if not dataset_id:
            result = service.create_dataset(name=request.dataset_name)
            if result.get("code") == 0:
                dataset_id = result.get("data", {}).get("id")

        if not dataset_id:
            raise HTTPException(status_code=500, detail="创建数据集失败")

        # 2. 保存上传文件（临时，用于摘要生成）
        with tempfile.NamedTemporaryFile(delete=False, suffix=request.file.filename) as tmp:
            content = await request.file.read()
            tmp.write(content)
            tmp_path = tmp.name
            tmp_filename = request.file.filename

        try:
            # 3. 生成摘要（先于上传，因为文件在本地）
            summary_svc = get_summary_service()
            summary_card = summary_svc.generate_summary(tmp_path, tmp_filename)

            # 4. 上传文档到 RAGFlow
            upload_result = service.upload_document(
                dataset_id, tmp_path, request.chunk_method
            )

            return {
                "success": upload_result.get("code") == 0,
                "dataset_id": dataset_id,
                "document": upload_result.get("data"),
                "summary": summary_card.to_dict(),
                "message": "文档上传成功，摘要已自动生成"
            }
        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
