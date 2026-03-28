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
