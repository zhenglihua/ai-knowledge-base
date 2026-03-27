"""
文档分类和标签管理 API
提供分类CRUD、标签CRUD、智能分类和标签提取功能
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import datetime

from models.database import get_db, Document, Category, Tag, DocumentTag
from services.classification_service import (
    get_classifier, classify_document, extract_document_tags, 
    analyze_document, PRESET_CATEGORIES
)

router = APIRouter(prefix="/api/categories", tags=["分类和标签管理"])

# ============= 数据模型 =============

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "blue"
    icon: Optional[str] = "📄"
    sort_order: Optional[int] = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    color: str
    icon: str
    sort_order: int
    is_preset: bool
    document_count: int
    created_at: str

    class Config:
        from_attributes = True

class TagCreate(BaseModel):
    name: str
    tag_type: Optional[str] = "custom"
    description: Optional[str] = None
    color: Optional[str] = "default"

class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class TagResponse(BaseModel):
    id: str
    name: str
    tag_type: str
    description: Optional[str]
    color: str
    usage_count: int
    created_at: str

    class Config:
        from_attributes = True

class DocumentClassifyRequest(BaseModel):
    document_id: str
    auto_apply: bool = False  # 是否自动应用分类结果

class DocumentClassifyResponse(BaseModel):
    document_id: str
    suggested_category: str
    confidence: float
    reason: str
    tags: List[dict]
    applied: bool

class BatchClassifyRequest(BaseModel):
    document_ids: List[str]
    auto_apply: bool = False

# ============= 分类管理 API =============

@router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    categories = db.query(Category).order_by(Category.sort_order).all()
    
    # 统计每个分类的文档数量
    doc_counts = dict(
        db.query(Document.category, func.count(Document.id))
        .group_by(Document.category)
        .all()
    )
    
    result = []
    for cat in categories:
        result.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            color=cat.color,
            icon=cat.icon,
            sort_order=cat.sort_order,
            is_preset=bool(cat.is_preset),
            document_count=doc_counts.get(cat.name, 0),
            created_at=cat.created_at.isoformat()
        ))
    
    return result

@router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """创建新分类"""
    # 检查名称是否已存在
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    
    new_category = Category(
        id=str(uuid.uuid4()),
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        sort_order=category.sort_order,
        is_preset=0
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return CategoryResponse(
        id=new_category.id,
        name=new_category.name,
        description=new_category.description,
        color=new_category.color,
        icon=new_category.icon,
        sort_order=new_category.sort_order,
        is_preset=False,
        document_count=0,
        created_at=new_category.created_at.isoformat()
    )

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    """获取分类详情"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    doc_count = db.query(Document).filter(Document.category == category.name).count()
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        sort_order=category.sort_order,
        is_preset=bool(category.is_preset),
        document_count=doc_count,
        created_at=category.created_at.isoformat()
    )

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: str, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    """更新分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 预设分类不允许修改名称
    if category.is_preset and category_update.name and category_update.name != category.name:
        raise HTTPException(status_code=400, detail="预设分类不允许修改名称")
    
    # 检查新名称是否冲突
    if category_update.name and category_update.name != category.name:
        existing = db.query(Category).filter(Category.name == category_update.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="分类名称已存在")
    
    # 更新字段
    if category_update.name:
        category.name = category_update.name
    if category_update.description is not None:
        category.description = category_update.description
    if category_update.color:
        category.color = category_update.color
    if category_update.icon:
        category.icon = category_update.icon
    if category_update.sort_order is not None:
        category.sort_order = category_update.sort_order
    
    db.commit()
    db.refresh(category)
    
    doc_count = db.query(Document).filter(Document.category == category.name).count()
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        sort_order=category.sort_order,
        is_preset=bool(category.is_preset),
        document_count=doc_count,
        created_at=category.created_at.isoformat()
    )

@router.delete("/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    """删除分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 预设分类不允许删除
    if category.is_preset:
        raise HTTPException(status_code=400, detail="预设分类不允许删除")
    
    # 检查是否有文档使用此分类
    doc_count = db.query(Document).filter(Document.category == category.name).count()
    if doc_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下有 {doc_count} 个文档，请先移动或删除这些文档")
    
    db.delete(category)
    db.commit()
    
    return {"message": "删除成功", "id": category_id}

# ============= 标签管理 API =============

@router.get("/tags/all", response_model=List[TagResponse])
def get_all_tags(tag_type: Optional[str] = None, db: Session = Depends(get_db)):
    """获取所有标签"""
    query = db.query(Tag)
    if tag_type:
        query = query.filter(Tag.tag_type == tag_type)
    
    tags = query.order_by(Tag.usage_count.desc()).all()
    
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            tag_type=tag.tag_type,
            description=tag.description,
            color=tag.color,
            usage_count=tag.usage_count,
            created_at=tag.created_at.isoformat()
        )
        for tag in tags
    ]

@router.get("/tags/popular")
def get_popular_tags(limit: int = 20, db: Session = Depends(get_db)):
    """获取热门标签"""
    tags = db.query(Tag).order_by(Tag.usage_count.desc()).limit(limit).all()
    
    return [
        {
            "id": tag.id,
            "name": tag.name,
            "tag_type": tag.tag_type,
            "usage_count": tag.usage_count
        }
        for tag in tags
    ]

@router.post("/tags", response_model=TagResponse)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """创建新标签"""
    # 检查名称是否已存在
    existing = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签名称已存在")
    
    new_tag = Tag(
        id=str(uuid.uuid4()),
        name=tag.name,
        tag_type=tag.tag_type,
        description=tag.description,
        color=tag.color,
        usage_count=0
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    return TagResponse(
        id=new_tag.id,
        name=new_tag.name,
        tag_type=new_tag.tag_type,
        description=new_tag.description,
        color=new_tag.color,
        usage_count=new_tag.usage_count,
        created_at=new_tag.created_at.isoformat()
    )

@router.put("/tags/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: str, tag_update: TagUpdate, db: Session = Depends(get_db)):
    """更新标签"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 检查新名称是否冲突
    if tag_update.name and tag_update.name != tag.name:
        existing = db.query(Tag).filter(Tag.name == tag_update.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        tag.name = tag_update.name
    
    if tag_update.description is not None:
        tag.description = tag_update.description
    if tag_update.color:
        tag.color = tag_update.color
    
    db.commit()
    db.refresh(tag)
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        tag_type=tag.tag_type,
        description=tag.description,
        color=tag.color,
        usage_count=tag.usage_count,
        created_at=tag.created_at.isoformat()
    )

@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: str, db: Session = Depends(get_db)):
    """删除标签"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 删除关联
    db.query(DocumentTag).filter(DocumentTag.tag_id == tag_id).delete()
    db.delete(tag)
    db.commit()
    
    return {"message": "删除成功", "id": tag_id}

# ============= 智能分类和标签提取 API =============

@router.post("/classify", response_model=DocumentClassifyResponse)
def classify_document_api(request: DocumentClassifyRequest, db: Session = Depends(get_db)):
    """智能分类文档"""
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 使用分类服务
    result = analyze_document(document.content, document.title)
    
    applied = False
    if request.auto_apply:
        # 自动应用分类
        document.category = result["category"]
        
        # 自动应用标签
        for tag_info in result["tags"][:5]:  # 最多应用5个标签
            # 查找或创建标签
            tag = db.query(Tag).filter(Tag.name == tag_info["tag"]).first()
            if not tag:
                tag = Tag(
                    id=str(uuid.uuid4()),
                    name=tag_info["tag"],
                    tag_type=tag_info["type"],
                    usage_count=0
                )
                db.add(tag)
                db.flush()
            
            # 检查是否已关联
            existing = db.query(DocumentTag).filter(
                DocumentTag.document_id == document.id,
                DocumentTag.tag_id == tag.id
            ).first()
            
            if not existing:
                doc_tag = DocumentTag(
                    document_id=document.id,
                    tag_id=tag.id,
                    confidence=tag_info["confidence"]
                )
                db.add(doc_tag)
                tag.usage_count += 1
        
        db.commit()
        applied = True
    
    return DocumentClassifyResponse(
        document_id=document.id,
        suggested_category=result["category"],
        confidence=result["category_confidence"],
        reason=result["category_reason"],
        tags=result["tags"],
        applied=applied
    )

@router.post("/classify/batch")
def batch_classify_documents(request: BatchClassifyRequest, db: Session = Depends(get_db)):
    """批量分类文档"""
    results = []
    
    for doc_id in request.document_ids:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            results.append({
                "document_id": doc_id,
                "status": "error",
                "message": "文档不存在"
            })
            continue
        
        try:
            result = analyze_document(document.content, document.title)
            
            if request.auto_apply:
                document.category = result["category"]
                
                # 应用标签
                for tag_info in result["tags"][:5]:
                    tag = db.query(Tag).filter(Tag.name == tag_info["tag"]).first()
                    if not tag:
                        tag = Tag(
                            id=str(uuid.uuid4()),
                            name=tag_info["tag"],
                            tag_type=tag_info["type"],
                            usage_count=0
                        )
                        db.add(tag)
                        db.flush()
                    
                    existing = db.query(DocumentTag).filter(
                        DocumentTag.document_id == document.id,
                        DocumentTag.tag_id == tag.id
                    ).first()
                    
                    if not existing:
                        doc_tag = DocumentTag(
                            document_id=document.id,
                            tag_id=tag.id,
                            confidence=tag_info["confidence"]
                        )
                        db.add(doc_tag)
                        tag.usage_count += 1
            
            results.append({
                "document_id": doc_id,
                "status": "success",
                "category": result["category"],
                "confidence": result["category_confidence"],
                "tags_count": len(result["tags"])
            })
        except Exception as e:
            results.append({
                "document_id": doc_id,
                "status": "error",
                "message": str(e)
            })
    
    if request.auto_apply:
        db.commit()
    
    return {
        "total": len(request.document_ids),
        "success": len([r for r in results if r["status"] == "success"]),
        "results": results
    }

@router.post("/extract-tags")
def extract_tags_from_document(document_id: str, db: Session = Depends(get_db)):
    """从文档提取标签（不应用）"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    result = analyze_document(document.content, document.title)
    
    return {
        "document_id": document.id,
        "title": document.title,
        "suggested_tags": result["tags"],
        "tag_summary": result["tag_summary"]
    }

@router.get("/preset/list")
def get_preset_categories():
    """获取预设分类列表"""
    return PRESET_CATEGORIES


# ============= 文档标签关联管理 =============

@router.post("/documents/{document_id}/tags")
def add_tag_to_document(document_id: str, tag_id: str, db: Session = Depends(get_db)):
    """为文档添加标签"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 检查是否已关联
    existing = db.query(DocumentTag).filter(
        DocumentTag.document_id == document_id,
        DocumentTag.tag_id == tag_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="文档已拥有此标签")
    
    doc_tag = DocumentTag(
        document_id=document_id,
        tag_id=tag_id,
        confidence=1.0
    )
    db.add(doc_tag)
    tag.usage_count += 1
    db.commit()
    
    return {"message": "添加成功", "document_id": document_id, "tag_id": tag_id}

@router.delete("/documents/{document_id}/tags/{tag_id}")
def remove_tag_from_document(document_id: str, tag_id: str, db: Session = Depends(get_db)):
    """从文档移除标签"""
    doc_tag = db.query(DocumentTag).filter(
        DocumentTag.document_id == document_id,
        DocumentTag.tag_id == tag_id
    ).first()
    
    if not doc_tag:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        tag.usage_count = max(0, tag.usage_count - 1)
    
    db.delete(doc_tag)
    db.commit()
    
    return {"message": "移除成功", "document_id": document_id, "tag_id": tag_id}

@router.get("/documents/{document_id}/tags")
def get_document_tags(document_id: str, db: Session = Depends(get_db)):
    """获取文档的标签"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_tags = db.query(DocumentTag, Tag).join(
        Tag, DocumentTag.tag_id == Tag.id
    ).filter(
        DocumentTag.document_id == document_id
    ).all()
    
    return [
        {
            "tag_id": tag.id,
            "name": tag.name,
            "tag_type": tag.tag_type,
            "confidence": doc_tag.confidence,
            "color": tag.color
        }
        for doc_tag, tag in doc_tags
    ]