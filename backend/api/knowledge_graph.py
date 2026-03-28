"""
知识图谱API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models.database import get_db
from services.neo4j_service import get_neo4j_service, Neo4jService
from core.permission import get_current_user

router = APIRouter(prefix="/api/kg", tags=["知识图谱"])


# ============ Schema ============

class EntityCreate(BaseModel):
    label: str
    properties: dict


class EntityUpdate(BaseModel):
    properties: dict


class RelationCreate(BaseModel):
    from_label: str
    from_id: str
    to_label: str
    to_id: str
    rel_type: str
    properties: Optional[dict] = None


# ============ 实体管理 ============

@router.get("/entities", summary="获取实体列表")
async def get_entities(
    label: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """获取实体列表，支持按类型和关键词搜索"""
    try:
        if keyword:
            if not label:
                # 全局搜索
                labels = ["Equipment", "Process", "Material", "Parameter", "Document", "Person", "Fault", "Term"]
                results = []
                for l in labels:
                    entities = neo4j.search_entities(l, keyword, limit)
                    results.extend(entities)
                return {"code": 200, "data": results[:limit]}
            else:
                entities = neo4j.search_entities(label, keyword, limit)
                return {"code": 200, "data": entities}
        else:
            if not label:
                # 返回所有实体统计
                stats = neo4j.get_statistics()
                return {"code": 200, "data": stats}
            else:
                # 按类型查询
                query = f"MATCH (e:{label}) RETURN e ORDER BY e.created_at DESC LIMIT $limit"
                result = neo4j.execute(query, {"limit": limit})
                entities = [dict(r["e"]) for r in result]
                return {"code": 200, "data": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", summary="获取实体详情")
async def get_entity(
    entity_id: str,
    label: str = Query(..., description="实体类型"),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """获取实体详情，包括邻居节点"""
    entity = neo4j.get_entity(label, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    
    neighbors = neo4j.get_neighbors(label, entity_id, depth=1)
    
    return {
        "code": 200,
        "data": {
            "entity": entity,
            "neighbors": neighbors
        }
    }


@router.post("/entities", summary="创建实体")
async def create_entity(
    data: EntityCreate,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """创建新实体"""
    try:
        entity = neo4j.create_entity(data.label, data.properties)
        return {"code": 200, "message": "创建成功", "data": entity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entities/{entity_id}", summary="更新实体")
async def update_entity(
    entity_id: str,
    data: EntityUpdate,
    label: str = Query(...),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """更新实体"""
    try:
        entity = neo4j.update_entity(label, entity_id, data.properties)
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        return {"code": 200, "message": "更新成功", "data": entity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}", summary="删除实体")
async def delete_entity(
    entity_id: str,
    label: str = Query(...),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """删除实体及其关系"""
    try:
        success = neo4j.delete_entity(label, entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="实体不存在")
        return {"code": 200, "message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 关系管理 ============

@router.post("/relations", summary="创建关系")
async def create_relation(
    data: RelationCreate,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """创建实体间的关系"""
    try:
        relation = neo4j.create_relationship(
            data.from_label, data.from_id,
            data.to_label, data.to_id,
            data.rel_type, data.properties
        )
        if not relation:
            raise HTTPException(status_code=400, detail="关系创建失败")
        return {"code": 200, "message": "创建成功", "data": relation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relations", summary="删除关系")
async def delete_relation(
    from_label: str,
    from_id: str,
    to_label: str,
    to_id: str,
    rel_type: str,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """删除关系"""
    try:
        success = neo4j.delete_relationship(
            from_label, from_id, to_label, to_id, rel_type
        )
        if not success:
            raise HTTPException(status_code=404, detail="关系不存在")
        return {"code": 200, "message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 图谱查询 ============

@router.get("/subgraph/{entity_id}", summary="获取子图")
async def get_subgraph(
    entity_id: str,
    label: str = Query(...),
    depth: int = Query(2, ge=1, le=3),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """获取实体为中心的子图"""
    try:
        subgraph = neo4j.get_subgraph(label, entity_id, depth)
        return {"code": 200, "data": subgraph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path/{from_id}/{to_id}", summary="查找最短路径")
async def find_path(
    from_id: str,
    to_id: str,
    from_label: str = Query(...),
    to_label: str = Query(...),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """查找两个实体间的最短路径"""
    try:
        path = neo4j.shortest_path(from_label, from_id, to_label, to_id)
        if not path:
            return {"code": 200, "message": "未找到路径", "data": None}
        return {"code": 200, "data": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{entity_id}", summary="获取邻居节点")
async def get_neighbors(
    entity_id: str,
    label: str = Query(...),
    rel_type: Optional[str] = None,
    direction: str = Query("both", regex="^(outgoing|incoming|both)$"),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """获取实体的邻居节点"""
    try:
        neighbors = neo4j.get_connected_entities(label, entity_id, rel_type, direction)
        return {"code": 200, "data": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 统计 ============

@router.get("/statistics", summary="获取图谱统计")
async def get_statistics(
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """获取图谱统计信息"""
    try:
        stats = neo4j.get_statistics()
        return {"code": 200, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/counts", summary="获取实体和关系数量")
async def get_counts(
    neo4j: Neo4jService = Depends(get_neo4j_service),
    current_user = Depends(get_current_user)
):
    """获取实体和关系的总数量"""
    try:
        entity_count = neo4j.entity_count()
        relation_count = neo4j.relationship_count()
        return {
            "code": 200,
            "data": {
                "entities": entity_count,
                "relationships": relation_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
