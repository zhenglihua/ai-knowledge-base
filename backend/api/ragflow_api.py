"""
RAGFlow 集成 API
v0.8.0
专业 RAG 问答接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import tempfile

from services.integration import (
    get_ragflow_service,
    is_ragflow_available,
    RAGFlowDataset,
    RAGFlowDocument
)


router = APIRouter(prefix="/api/ragflow", tags=["RAGFlow专业RAG"])


# ========== 请求/响应模型 ==========

class DatasetCreateRequest(BaseModel):
    """创建数据集请求"""
    name: str
    description: str = ""
    embedding_model: str = "BAAI/bge-large-zh-v1.5"


class ChatRequest(BaseModel):
    """对话请求"""
    dataset_ids: List[str]
    query: str
    top_k: int = 10
    similarity_threshold: float = 0.5
    temperature: float = 0.1


class RetrievalRequest(BaseModel):
    """检索请求"""
    dataset_ids: List[str]
    query: str
    top_k: int = 10
    similarity_threshold: float = 0.5


# ========== 状态接口 ==========

@router.get("/status")
async def get_status():
    """获取 RAGFlow 连接状态"""
    available = is_ragflow_available()
    
    if available:
        try:
            service = get_ragflow_service()
            version = service.get_version()
            datasets = service.list_datasets()
            return {
                "status": "connected",
                "version": version,
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
        dataset = service.create_dataset(
            name=request.name,
            description=request.description,
            embedding_model=request.embedding_model
        )
        return {
            "success": True,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "document_count": dataset.document_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets():
    """获取数据集列表"""
    try:
        service = get_ragflow_service()
        datasets = service.list_datasets()
        return {
            "datasets": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "document_count": d.document_count,
                    "created_at": d.created_at
                }
                for d in datasets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取数据集详情"""
    try:
        service = get_ragflow_service()
        dataset = service.get_dataset(dataset_id)
        return {
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "document_count": dataset.document_count,
                "created_at": dataset.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


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
            doc = service.upload_document(dataset_id, tmp_path, chunk_method)
            
            return {
                "success": True,
                "document": {
                    "id": doc.id,
                    "name": doc.name,
                    "status": doc.status.value,
                    "size": doc.size
                }
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
            "documents": [
                {
                    "id": d.id,
                    "name": d.name,
                    "status": d.status.value,
                    "size": d.size,
                    "created_at": d.created_at
                }
                for d in docs
            ]
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


@router.post("/datasets/{dataset_id}/documents/{doc_id}/parse")
async def parse_document(dataset_id: str, doc_id: str):
    """触发文档解析"""
    try:
        service = get_ragflow_service()
        success = service.parse_document(dataset_id, doc_id)
        return {"success": success, "message": "解析任务已提交"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_id}/documents/{doc_id}/wait")
async def wait_document_ready(
    dataset_id: str,
    doc_id: str,
    timeout: int = 300
):
    """等待文档解析完成"""
    try:
        service = get_ragflow_service()
        ready = service.wait_document_ready(dataset_id, doc_id, timeout=timeout)
        
        if ready:
            return {"ready": True, "message": "文档解析完成"}
        else:
            return {"ready": False, "message": "文档解析超时或失败"}
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
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            temperature=request.temperature
        )
        
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "references": result.get("references", []),
            "conversation_id": result.get("conversation_id")
        }
        
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
        
        results = service.retrieval(
            dataset_ids=request.dataset_ids,
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
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
    auto_parse: bool = True


@router.post("/process")
async def process_document(
    request: ProcessDocumentRequest,
    top_k: int = 5,
    similarity_threshold: float = 0.5
):
    """
    一站式文档处理
    
    1. 创建/获取数据集
    2. 上传文档
    3. 解析文档
    4. 返回问答
    """
    try:
        service = get_ragflow_service()
        
        # 1. 获取或创建数据集
        datasets = service.list_datasets()
        dataset = None
        for d in datasets:
            if d.name == request.dataset_name:
                dataset = d
                break
        
        if not dataset:
            dataset = service.create_dataset(name=request.dataset_name)
        
        # 2. 保存上传文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=request.file.filename) as tmp:
            content = await request.file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 3. 上传文档
            doc = service.upload_document(
                dataset.id, tmp_path, request.chunk_method
            )
            
            # 4. 解析文档
            if request.auto_parse:
                service.parse_document(dataset.id, doc.id)
            
            # 5. 返回结果
            return {
                "success": True,
                "dataset": {
                    "id": dataset.id,
                    "name": dataset.name
                },
                "document": {
                    "id": doc.id,
                    "name": doc.name,
                    "status": doc.status.value
                },
                "message": "文档上传成功，正在解析中"
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
