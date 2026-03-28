"""
对比分析 API
v0.3.0
支持多文档对比分析
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.database import get_db_session, Document
from services.multi_doc_rag import multi_doc_rag_service
from core.security import get_current_user


router = APIRouter(prefix="/api/comparison", tags=["comparison"])


class ComparisonRequest(BaseModel):
    """对比请求"""
    document_ids: List[str] = Field(..., min_length=2, max_length=4,
                                     description="要对比的文档ID列表（2-4个）")
    dimensions: Optional[List[str]] = Field(None,
                                           description="对比维度列表")
    query: Optional[str] = Field(None, description="对比分析的问题")


class ComparisonResult(BaseModel):
    """对比结果项"""
    document_id: str
    title: str
    content_preview: str
    metadata: Dict[str, Any]
    matched_dimensions: Dict[str, Any]


class ComparisonResponse(BaseModel):
    """对比响应"""
    comparison_id: str
    created_at: str
    documents: List[ComparisonResult]
    comparison_table: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None


@router.post("/analyze", response_model=ComparisonResponse)
async def compare_documents(
    request: ComparisonRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    对比分析多个文档

    支持 2-4 个文档的对比分析，可以指定对比维度或提出对比问题
    """
    try:
        # 获取文档信息
        db = get_db_session()
        try:
            docs = db.query(Document).filter(
                Document.id.in_(request.document_ids)
            ).all()

            if len(docs) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="至少需要2个有效文档进行对比"
                )

            if len(docs) != len(request.document_ids):
                raise HTTPException(
                    status_code=400,
                    detail="部分文档ID无效"
                )

            # 构建对比结果
            comparison_results = []
            for doc in docs:
                result = ComparisonResult(
                    document_id=doc.id,
                    title=doc.title,
                    content_preview=doc.content[:500] if doc.content else "",
                    metadata={
                        "file_type": doc.file_type,
                        "category": doc.category,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                        "size": len(doc.content) if doc.content else 0
                    },
                    matched_dimensions={}
                )
                comparison_results.append(result)

            # 如果提供了查询，进行深度对比
            comparison_table = None
            summary = None

            if request.query:
                # 使用 RAG 进行深度对比分析
                rag_result = await multi_doc_rag_service.query_across_documents(
                    question=request.query,
                    document_ids=request.document_ids,
                    top_k=5
                )
                summary = rag_result.get("answer", "")

            return ComparisonResponse(
                comparison_id=f"cmp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                created_at=datetime.now().isoformat(),
                documents=comparison_results,
                comparison_table=comparison_table,
                summary=summary
            )
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dimensions")
async def get_comparison_dimensions(
    current_user: dict = Depends(get_current_user)
):
    """
    获取预定义的对比维度

    返回半导体行业常用的对比维度
    """
    return {
        "dimensions": [
            {
                "id": "specs",
                "name": "规格参数",
                "description": "设备或材料的规格和技术参数"
            },
            {
                "id": "process",
                "name": "工艺兼容性",
                "description": "与现有工艺流程的兼容性"
            },
            {
                "id": "performance",
                "name": "性能指标",
                "description": "产能、良率、精度等性能表现"
            },
            {
                "id": "cost",
                "name": "成本分析",
                "description": "采购、维护、运营成本对比"
            },
            {
                "id": "supplier",
                "name": "供应商信息",
                "description": "供应商资质、交货能力、服务支持"
            },
            {
                "id": "safety",
                "name": "安全合规",
                "description": "安全标准和合规性"
            }
        ]
    }


@router.get("/history")
async def get_comparison_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对比历史记录

    返回用户最近的对比分析历史
    """
    # TODO: 实现历史记录存储和查询
    return {
        "history": [],
        "total": 0,
        "message": "历史记录功能开发中"
    }
