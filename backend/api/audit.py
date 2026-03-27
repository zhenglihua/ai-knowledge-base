"""
审计日志API
查询操作日志和文档访问日志
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.auth_models import AuditLog, DocumentAccessLog
from core.security import get_current_user, require_permissions, Permission

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    action: Optional[str] = None,
    module: Optional[str] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    current_user: dict = Depends(require_permissions(Permission.SYS_AUDIT)),
    db: Session = Depends(get_db)
):
    """查询审计日志"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if username:
        query = query.filter(AuditLog.username.contains(username))
    if action:
        query = query.filter(AuditLog.action == action)
    if module:
        query = query.filter(AuditLog.module == module)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if status:
        query = query.filter(AuditLog.status == status)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "module": log.module,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

@router.get("/document-logs")
async def get_document_access_logs(
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
    action: Optional[str] = None,
    classification: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    current_user: dict = Depends(require_permissions(Permission.SYS_AUDIT)),
    db: Session = Depends(get_db)
):
    """查询文档访问日志"""
    query = db.query(DocumentAccessLog)
    
    if user_id:
        query = query.filter(DocumentAccessLog.user_id == user_id)
    if document_id:
        query = query.filter(DocumentAccessLog.document_id == document_id)
    if action:
        query = query.filter(DocumentAccessLog.action == action)
    if classification:
        query = query.filter(DocumentAccessLog.document_classification == classification)
    if start_date:
        query = query.filter(DocumentAccessLog.created_at >= start_date)
    if end_date:
        query = query.filter(DocumentAccessLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(DocumentAccessLog.created_at.desc()).offset(offset).limit(limit).all()
    
    # 密级名称映射
    classification_names = {1: "公开", 2: "内部", 3: "机密", 4: "绝密"}
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "document_id": log.document_id,
                "document_title": log.document_title,
                "document_classification": log.document_classification,
                "classification_name": classification_names.get(log.document_classification, "未知"),
                "action": log.action,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(default=7, le=90),
    current_user: dict = Depends(require_permissions(Permission.SYS_AUDIT)),
    db: Session = Depends(get_db)
):
    """获取审计统计"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 总日志数
    total_logs = db.query(AuditLog).filter(AuditLog.created_at >= start_date).count()
    
    # 按操作类型统计
    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).all()
    
    # 按模块统计
    module_stats = db.query(
        AuditLog.module,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date,
        AuditLog.module.isnot(None)
    ).group_by(AuditLog.module).all()
    
    # 按状态统计
    status_stats = db.query(
        AuditLog.status,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.status).all()
    
    # 活跃用户统计
    active_users = db.query(
        AuditLog.user_id,
        AuditLog.username,
        func.count(AuditLog.id).label('action_count')
    ).filter(
        AuditLog.created_at >= start_date,
        AuditLog.user_id.isnot(None)
    ).group_by(AuditLog.user_id).order_by(func.count(AuditLog.id).desc()).limit(20).all()
    
    # 文档访问统计
    doc_stats = db.query(
        DocumentAccessLog.action,
        func.count(DocumentAccessLog.id).label('count')
    ).filter(
        DocumentAccessLog.created_at >= start_date
    ).group_by(DocumentAccessLog.action).all()
    
    return {
        "period_days": days,
        "total_logs": total_logs,
        "action_distribution": [
            {"action": a.action, "count": a.count}
            for a in action_stats
        ],
        "module_distribution": [
            {"module": m.module, "count": m.count}
            for m in module_stats
        ],
        "status_distribution": [
            {"status": s.status, "count": s.count}
            for s in status_stats
        ],
        "active_users": [
            {"user_id": u.user_id, "username": u.username, "action_count": u.action_count}
            for u in active_users
        ],
        "document_action_distribution": [
            {"action": d.action, "count": d.count}
            for d in doc_stats
        ]
    }
