"""
知识图谱API路由
提供实体抽取、关系抽取、图谱查询、文档推荐等接口
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from models.database import get_db, Document
from kg_module.models.entity import EntityType, RelationType
from kg_module.models.graph_store import get_graph_store, KnowledgeGraphStore
from kg_module.services.entity_extraction import get_entity_extractor
from kg_module.services.relation_extraction import get_relation_extractor
from kg_module.services.kg_builder import get_kg_builder
from kg_module.services.recommendation import get_recommender


router = APIRouter(prefix="/api/kg", tags=["knowledge_graph"])


# ========== 请求/响应模型 ==========

class EntityExtractionRequest(BaseModel):
    text: str
    min_confidence: float = 0.5

class EntityExtractionResponse(BaseModel):
    entities: List[dict]
    processing_time_ms: float

class RelationExtractionRequest(BaseModel):
    text: str
    entities: List[dict]
    min_confidence: float = 0.3

class RelationExtractionResponse(BaseModel):
    relations: List[dict]

class DocumentKGProcessRequest(BaseModel):
    doc_id: str

class DocumentKGProcessResponse(BaseModel):
    doc_id: str
    extracted_entities: int
    extracted_relations: int
    added_entities: int
    added_relations: int
    processing_time_ms: float

class EntitySearchRequest(BaseModel):
    keyword: str
    entity_type: Optional[str] = None
    limit: int = 20

class EntityNeighborsRequest(BaseModel):
    entity_id: str
    relation_type: Optional[str] = None
    depth: int = 1

class PathFindRequest(BaseModel):
    source_id: str
    target_id: str
    max_depth: int = 5

class RecommendRequest(BaseModel):
    doc_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    limit: int = 5
    method: str = "hybrid"


# ========== API端点 ==========

@router.post("/extract/entities", response_model=EntityExtractionResponse)
async def extract_entities(request: EntityExtractionRequest):
    """
    从文本中抽取实体
    
    - **text**: 待抽取的文本内容
    - **min_confidence**: 最小置信度阈值（默认0.5）
    """
    try:
        extractor = get_entity_extractor()
        result = extractor.extract(
            text=request.text,
            min_confidence=request.min_confidence
        )
        
        return EntityExtractionResponse(
            entities=[e.to_dict() for e in result.entities],
            processing_time_ms=result.processing_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/relations", response_model=RelationExtractionResponse)
async def extract_relations(request: RelationExtractionRequest):
    """
    从文本中抽取实体间关系
    
    - **text**: 待抽取的文本内容
    - **entities**: 已抽取的实体列表
    - **min_confidence**: 最小置信度阈值（默认0.3）
    """
    try:
        from kg_module.models.entity import ExtractedEntity, EntityType
        
        # 转换实体列表
        entities = []
        for e in request.entities:
            entity = ExtractedEntity(
                text=e["text"],
                type=EntityType(e["type"]),
                start=e.get("start", 0),
                end=e.get("end", 0),
                confidence=e.get("confidence", 1.0),
                properties=e.get("properties", {})
            )
            entities.append(entity)
        
        extractor = get_relation_extractor()
        relations = extractor.extract_relations(
            text=request.text,
            entities=entities,
            min_confidence=request.min_confidence
        )
        
        return RelationExtractionResponse(
            relations=[r.to_dict() for r in relations]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{doc_id}/process", response_model=DocumentKGProcessResponse)
async def process_document_kg(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    处理文档并构建知识图谱
    
    - **doc_id**: 文档ID
    """
    try:
        # 获取文档内容
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 构建知识图谱
        builder = get_kg_builder()
        result = builder.process_document(
            doc_id=doc_id,
            text=doc.content,
            title=doc.title
        )
        
        return DocumentKGProcessResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}/knowledge")
async def get_document_knowledge(doc_id: str):
    """
    获取文档的知识图谱表示
    
    - **doc_id**: 文档ID
    """
    try:
        builder = get_kg_builder()
        result = builder.get_document_knowledge(doc_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/search")
async def search_entities(
    keyword: str = Query(..., description="搜索关键词"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    搜索实体
    
    - **keyword**: 搜索关键词
    - **entity_type**: 可选的实体类型过滤
    - **limit**: 返回结果数量限制
    """
    try:
        store = get_graph_store()
        
        # 转换实体类型
        etype = None
        if entity_type:
            try:
                etype = EntityType(entity_type)
            except ValueError:
                pass
        
        entities = store.search_entities(keyword, etype, limit)
        
        return {
            "keyword": keyword,
            "total": len(entities),
            "entities": [e.to_dict() for e in entities]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """
    获取实体详情
    
    - **entity_id**: 实体ID
    """
    try:
        store = get_graph_store()
        entity = store.get_entity(entity_id)
        
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        # 获取相关关系
        relations_out = store.get_relations_by_entity(entity_id, "out")
        relations_in = store.get_relations_by_entity(entity_id, "in")
        
        return {
            "entity": entity.to_dict(),
            "relations_out": [
                {"relation": r.to_dict(), "target": e.to_dict()}
                for r, e in relations_out
            ],
            "relations_in": [
                {"relation": r.to_dict(), "source": e.to_dict()}
                for r, e in relations_in
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/{entity_id}/neighbors")
async def get_entity_neighbors(request: EntityNeighborsRequest):
    """
    获取实体的邻居节点
    
    - **entity_id**: 实体ID
    - **relation_type**: 可选的关系类型过滤
    - **depth**: 搜索深度（默认1）
    """
    try:
        store = get_graph_store()
        
        # 转换关系类型
        rel_type = None
        if request.relation_type:
            try:
                rel_type = RelationType(request.relation_type)
            except ValueError:
                pass
        
        neighbors = store.get_neighbors(
            request.entity_id,
            rel_type,
            request.depth
        )
        
        return {
            "entity_id": request.entity_id,
            "neighbors": neighbors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/path/find")
async def find_path(request: PathFindRequest):
    """
    查找两个实体之间的路径
    
    - **source_id**: 源实体ID
    - **target_id**: 目标实体ID
    - **max_depth**: 最大搜索深度（默认5）
    """
    try:
        store = get_graph_store()
        path = store.find_path(
            request.source_id,
            request.target_id,
            request.max_depth
        )
        
        if path is None:
            return {
                "found": False,
                "message": "未找到路径"
            }
        
        return {
            "found": True,
            "path": path,
            "path_length": len(path) - 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_graph_statistics():
    """获取知识图谱统计信息"""
    try:
        store = get_graph_store()
        stats = store.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/documents")
async def recommend_documents(request: RecommendRequest):
    """
    推荐相关文档
    
    - **doc_id**: 参考文档ID（可选）
    - **keywords**: 关键词列表（可选）
    - **limit**: 返回结果数量
    - **method**: 推荐方法（content/collaborative/hybrid）
    """
    try:
        recommender = get_recommender()
        
        if request.doc_id:
            results = recommender.recommend_documents(
                request.doc_id,
                request.limit,
                request.method
            )
        elif request.keywords:
            results = recommender.recommend_by_keywords(
                request.keywords,
                request.limit
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="需要提供doc_id或keywords"
            )
        
        return {
            "recommendations": results,
            "total": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/recommend")
async def recommend_entities(
    entity_id: str,
    relation_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """
    推荐相关实体
    
    - **entity_id**: 种子实体ID
    - **relation_type**: 可选的关系类型过滤
    - **limit**: 返回结果数量
    """
    try:
        recommender = get_recommender()
        
        # 转换关系类型
        rel_type = None
        if relation_type:
            try:
                rel_type = RelationType(relation_type)
            except ValueError:
                pass
        
        results = recommender.recommend_entities(
            entity_id,
            rel_type,
            limit
        )
        
        return {
            "entity_id": entity_id,
            "recommendations": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending/entities")
async def get_trending_entities(
    entity_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """
    获取热门实体
    
    - **entity_type**: 可选的实体类型过滤
    - **limit**: 返回结果数量
    """
    try:
        recommender = get_recommender()
        
        # 转换实体类型
        etype = None
        if entity_type:
            try:
                etype = EntityType(entity_type)
            except ValueError:
                pass
        
        results = recommender.get_trending_entities(etype, limit)
        
        return {
            "trending": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_graph(filepath: str = "data/kg_export.json"):
    """导出知识图谱"""
    try:
        store = get_graph_store()
        store.export_to_json(filepath)
        return {
            "message": "知识图谱导出成功",
            "filepath": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_graph(filepath: str = "data/kg_export.json"):
    """导入知识图谱"""
    try:
        store = get_graph_store()
        store.import_from_json(filepath)
        store.save()
        return {
            "message": "知识图谱导入成功",
            "filepath": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))