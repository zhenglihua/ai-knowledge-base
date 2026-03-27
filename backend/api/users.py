"""
用户管理API
提供用户CRUD、角色分配等功能
"""
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.database import get_db
from models.auth_models import User, Role, AuditLog
from core.security import (
    get_password_hash, get_current_user, require_permissions, require_role,
    Role as RoleEnum, Permission, USER_MAX_CLASSIFICATION, Classification, CLASSIFICATION_NAMES
)
from core.audit import AuditService

router = APIRouter(prefix="/api/users", tags=["users"])

# ============ 数据模型 ============

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: str = RoleEnum.VISITOR

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserUpdatePassword(BaseModel):
    new_password: str

class UserListResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    department: Optional[str]
    role: str
    role_name: str
    is_active: bool
    last_login: Optional[str]
    created_at: str

class RoleAssign(BaseModel):
    role_id: str

# ============ 辅助函数 ============

def get_client_info(request: Request):
    """获取客户端信息"""
    return {
        "ip": request.client.host if request.client else "",
        "user_agent": request.headers.get("user-agent", "")
    }

def get_role_name(role_id: str) -> str:
    """获取角色显示名称"""
    role_names = {
        RoleEnum.SUPER_ADMIN: "超级管理员",
        RoleEnum.DEPT_ADMIN: "部门管理员",
        RoleEnum.ENGINEER: "工程师",
        RoleEnum.VISITOR: "访客"
    }
    return role_names.get(role_id, "访客")

# ============ API端点 ============

@router.get("")
async def list_users(
    role: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    current_user: dict = Depends(require_permissions(Permission.USER_VIEW)),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    query = db.query(User)
    
    # 非超级管理员只能看到同部门或更低级别的用户
    if current_user["role"] != RoleEnum.SUPER_ADMIN:
        query = query.filter(
            or_(
                User.department == current_user.get("department"),
                User.role.in_([RoleEnum.ENGINEER, RoleEnum.VISITOR])
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    if department:
        query = query.filter(User.department == department)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                User.username.contains(search),
                User.email.contains(search),
                User.full_name.contains(search)
            )
        )
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "department": u.department,
                "role": u.role,
                "role_name": get_role_name(u.role),
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    req: Request,
    current_user: dict = Depends(require_permissions(Permission.USER_CREATE)),
    db: Session = Depends(get_db)
):
    """创建用户"""
    # 检查权限级别
    current_user_level = USER_MAX_CLASSIFICATION.get(current_user["role"], Classification.PUBLIC)
    new_user_level = USER_MAX_CLASSIFICATION.get(request.role, Classification.PUBLIC)
    
    if new_user_level > current_user_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法创建权限级别高于自己的用户"
        )
    
    # 检查用户名或邮箱是否已存在
    existing = db.query(User).filter(
        or_(User.username == request.username, User.email == request.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    
    # 创建用户
    user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        department=request.department,
        role=request.role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    client = get_client_info(req)
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="create_user",
        module="users",
        resource_type="user",
        resource_id=user.id,
        description=f"创建用户: {user.username}",
        new_values={
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department": user.department
        },
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "department": user.department,
        "role": user.role,
        "role_name": get_role_name(user.role),
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    }

@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_permissions(Permission.USER_VIEW)),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查
    if current_user["role"] != RoleEnum.SUPER_ADMIN:
        if user.department != current_user.get("department") and user.role not in [RoleEnum.ENGINEER, RoleEnum.VISITOR]:
            raise HTTPException(status_code=403, detail="无权查看此用户")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "department": user.department,
        "avatar": user.avatar,
        "role": user.role,
        "role_name": get_role_name(user.role),
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdate,
    req: Request,
    current_user: dict = Depends(require_permissions(Permission.USER_EDIT)),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查
    if current_user["role"] != RoleEnum.SUPER_ADMIN:
        if user.department != current_user.get("department"):
            raise HTTPException(status_code=403, detail="无权修改此用户")
        # 部门管理员不能修改超级管理员
        if user.role == RoleEnum.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="无权修改超级管理员")
    
    # 记录旧值
    old_values = {
        "email": user.email,
        "full_name": user.full_name,
        "department": user.department,
        "role": user.role,
        "is_active": user.is_active
    }
    
    # 更新字段
    if request.email:
        # 检查邮箱是否已被其他用户使用
        existing = db.query(User).filter(
            User.email == request.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = request.email
    
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.department is not None:
        user.department = request.department
    if request.role is not None:
        # 检查角色权限
        current_user_level = USER_MAX_CLASSIFICATION.get(current_user["role"], Classification.PUBLIC)
        new_role_level = USER_MAX_CLASSIFICATION.get(request.role, Classification.PUBLIC)
        if new_role_level > current_user_level:
            raise HTTPException(status_code=403, detail="无法分配高于自己权限的角色")
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active
    
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    client = get_client_info(req)
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="update_user",
        module="users",
        resource_type="user",
        resource_id=user.id,
        description=f"更新用户: {user.username}",
        old_values=old_values,
        new_values={
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role,
            "is_active": user.is_active
        },
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "department": user.department,
        "role": user.role,
        "role_name": get_role_name(user.role),
        "is_active": user.is_active,
        "updated_at": user.updated_at.isoformat()
    }

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    req: Request,
    current_user: dict = Depends(require_permissions(Permission.USER_DELETE)),
    db: Session = Depends(get_db)
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    if user.id == current_user["id"]:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    # 权限检查
    if current_user["role"] != RoleEnum.SUPER_ADMIN:
        if user.department != current_user.get("department"):
            raise HTTPException(status_code=403, detail="无权删除此用户")
        if user.role == RoleEnum.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="无权删除超级管理员")
    
    # 软删除：标记为不活跃
    old_values = {"is_active": user.is_active}
    user.is_active = False
    user.updated_at = datetime.now()
    db.commit()
    
    # 记录审计日志
    client = get_client_info(req)
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="delete_user",
        module="users",
        resource_type="user",
        resource_id=user.id,
        description=f"删除用户: {user.username}",
        old_values=old_values,
        new_values={"is_active": False},
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {"message": "用户已删除", "id": user_id}

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: UserUpdatePassword,
    req: Request,
    current_user: dict = Depends(require_permissions(Permission.USER_EDIT)),
    db: Session = Depends(get_db)
):
    """重置用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查
    if current_user["role"] != RoleEnum.SUPER_ADMIN:
        if user.department != current_user.get("department"):
            raise HTTPException(status_code=403, detail="无权修改此用户密码")
        if user.role == RoleEnum.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="无权修改超级管理员密码")
    
    # 重置密码
    user.hashed_password = get_password_hash(request.new_password)
    user.password_changed_at = datetime.now()
    db.commit()
    
    # 记录审计日志
    client = get_client_info(req)
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="reset_password",
        module="users",
        resource_type="user",
        resource_id=user.id,
        description=f"重置用户密码: {user.username}",
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {"message": "密码已重置", "id": user_id}
