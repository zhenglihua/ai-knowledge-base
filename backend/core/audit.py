"""
审计日志中间件和服务
记录所有API请求和用户操作
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi import Request, Response
from sqlalchemy.orm import Session

from models.database import get_db_session
from models.auth_models import AuditLog, DocumentAccessLog


class AuditService:
    """审计日志服务"""
    
    @staticmethod
    def log_action(
        user_id: Optional[str],
        username: Optional[str],
        action: str,
        module: str = "",
        resource_type: str = "",
        resource_id: str = "",
        description: str = "",
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: str = "",
        user_agent: str = "",
        request_method: str = "",
        request_path: str = "",
        request_params: Optional[Dict] = None,
        status: str = "success",
        error_message: str = ""
    ):
        """记录操作日志"""
        db = get_db_session()
        try:
            log = AuditLog(
                user_id=user_id,
                username=username or "anonymous",
                action=action,
                module=module,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                old_values=json.dumps(old_values, ensure_ascii=False) if old_values else None,
                new_values=json.dumps(new_values, ensure_ascii=False) if new_values else None,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                request_params=json.dumps(request_params, ensure_ascii=False) if request_params else None,
                status=status,
                error_message=error_message
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def log_document_access(
        user_id: Optional[str],
        username: Optional[str],
        document_id: str,
        document_title: str,
        document_classification: int,
        action: str,
        ip_address: str = "",
        user_agent: str = ""
    ):
        """记录文档访问日志"""
        db = get_db_session()
        try:
            log = DocumentAccessLog(
                user_id=user_id,
                username=username or "anonymous",
                document_id=document_id,
                document_title=document_title,
                document_classification=document_classification,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """查询审计日志"""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if module:
            query = query.filter(AuditLog.module == module)
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
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
        }
    
    @staticmethod
    def get_document_access_logs(
        db: Session,
        user_id: Optional[str] = None,
        document_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """查询文档访问日志"""
        query = db.query(DocumentAccessLog)
        
        if user_id:
            query = query.filter(DocumentAccessLog.user_id == user_id)
        if document_id:
            query = query.filter(DocumentAccessLog.document_id == document_id)
        if action:
            query = query.filter(DocumentAccessLog.action == action)
        
        total = query.count()
        logs = query.order_by(DocumentAccessLog.created_at.desc()).offset(offset).limit(limit).all()
        
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
                    "action": log.action,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
        }


async def audit_middleware(request: Request, call_next):
    """审计日志中间件"""
    start_time = datetime.now()
    
    # 获取请求信息
    client_host = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    
    # 执行请求
    response = await call_next(request)
    
    # 记录关键操作的审计日志
    path = request.url.path
    method = request.method
    
    # 需要审计的路径
    audit_paths = [
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/register",
        "/api/users",
        "/api/roles",
        "/api/documents",
        "/api/documents/upload",
    ]
    
    should_audit = any(path.startswith(audit_path) for audit_path in audit_paths)
    
    if should_audit and method in ["POST", "PUT", "DELETE", "PATCH"]:
        # 尝试获取用户信息
        user_id = None
        username = "anonymous"
        
        # 这里简化处理，实际需要解析JWT
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from core.security import decode_token
            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub")
        
        AuditService.log_action(
            user_id=user_id,
            username=username,
            action=f"{method.lower()}_{path.split('/')[-1]}",
            module=path.split('/')[2] if len(path.split('/')) > 2 else "",
            ip_address=client_host,
            user_agent=user_agent,
            request_method=method,
            request_path=path,
            status="success" if response.status_code < 400 else "failure"
        )
    
    return response
