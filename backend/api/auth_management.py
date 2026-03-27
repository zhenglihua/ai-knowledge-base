"""
权限管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import bcrypt

from backend.models.database import get_db
from backend.models.auth_models import User, Role, Permission, Department, AuditLog, UserStatus, DataLevel
from backend.core.security import get_current_user, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["权限管理"])


# ============ Pydantic Schemas ============

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    real_name: Optional[str] = None
    password: str
    role_ids: List[int] = []
    department_ids: List[int] = []
    data_level: str = "internal"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    status: Optional[str] = None
    role_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    data_level: Optional[str] = None


class RoleCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    permission_ids: List[int] = []
    data_level: str = "internal"


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    is_enabled: Optional[bool] = None
    data_level: Optional[str] = None


class PermissionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    resource_type: str = "api"
    resource_path: Optional[str] = None
    http_method: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str
    code: str
    parent_id: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


# ============ 用户管理API ============

@router.get("/users", summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    role_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取用户列表，支持分页、搜索、筛选"""
    query = db.query(User).filter(User.is_deleted == False)
    
    if keyword:
        query = query.filter(
            or_(
                User.username.contains(keyword),
                User.real_name.contains(keyword),
                User.email.contains(keyword)
            )
        )
    
    if status:
        query = query.filter(User.status == status)
    
    if role_id:
        query = query.filter(User.roles.any(Role.id == role_id))
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "data": {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "phone": u.phone,
                    "real_name": u.real_name,
                    "status": u.status.value if u.status else None,
                    "data_level": u.data_level.value if u.data_level else None,
                    "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in u.roles],
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/users", summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """创建新用户"""
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # 密码哈希
    password_hash = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode()
    
    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        real_name=user_data.real_name,
        password_hash=password_hash,
        data_level=DataLevel(user_data.data_level),
        created_by=current_user.id
    )
    
    # 关联角色
    if user_data.role_ids:
        roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        user.roles = roles
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        resource_name=user.username,
        is_success=True
    )
    db.add(audit)
    db.commit()
    
    return {"code": 200, "message": "用户创建成功", "data": {"id": user.id}}


@router.put("/users/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新字段
    if user_data.email is not None:
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = user_data.email
    
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.real_name is not None:
        user.real_name = user_data.real_name
    if user_data.status is not None:
        user.status = UserStatus(user_data.status)
    if user_data.data_level is not None:
        user.data_level = DataLevel(user_data.data_level)
    
    # 更新角色
    if user_data.role_ids is not None:
        roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        user.roles = roles
    
    db.commit()
    
    return {"code": 200, "message": "用户更新成功"}


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """软删除用户"""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.is_system:
        raise HTTPException(status_code=400, detail="系统内置用户不能删除")
    
    user.is_deleted = True
    db.commit()
    
    return {"code": 200, "message": "用户删除成功"}


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详细信息"""
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "real_name": user.real_name,
            "status": user.status.value if user.status else None,
            "data_level": user.data_level.value if user.data_level else None,
            "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in user.roles],
            "departments": [{"id": d.id, "name": d.name, "code": d.code} for d in user.departments],
            "permissions": list(set([p.code for r in user.roles for p in r.permissions if p.is_enabled])),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    }


# ============ 角色管理API ============

@router.get("/roles", summary="获取角色列表")
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有角色"""
    roles = db.query(Role).filter(Role.is_deleted == False).order_by(Role.sort_order).all()
    return {
        "code": 200,
        "data": [
            {
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "description": r.description,
                "is_enabled": r.is_enabled,
                "is_system": r.is_system,
                "data_level": r.data_level.value if r.data_level else None,
                "permission_count": len(r.permissions),
                "user_count": len(r.users),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in roles
        ]
    }


@router.post("/roles", summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """创建新角色"""
    existing = db.query(Role).filter(Role.code == role_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色代码已存在")
    
    role = Role(
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
        data_level=DataLevel(role_data.data_level),
        created_by=current_user.id
    )
    
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
        role.permissions = permissions
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {"code": 200, "message": "角色创建成功", "data": {"id": role.id}}


@router.put("/roles/{role_id}", summary="更新角色")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新角色"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_deleted == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不能修改")
    
    if role_data.name is not None:
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.is_enabled is not None:
        role.is_enabled = role_data.is_enabled
    if role_data.data_level is not None:
        role.data_level = DataLevel(role_data.data_level)
    
    if role_data.permission_ids is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
        role.permissions = permissions
    
    db.commit()
    return {"code": 200, "message": "角色更新成功"}


@router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_deleted == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不能删除")
    
    if role.users:
        raise HTTPException(status_code=400, detail="该角色已有用户关联，请先移除关联用户")
    
    role.is_deleted = True
    db.commit()
    
    return {"code": 200, "message": "角色删除成功"}


@router.get("/roles/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色的所有权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return {
        "code": 200,
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "resource_type": p.resource_type,
                "resource_path": p.resource_path,
                "http_method": p.http_method,
            }
            for p in role.permissions
        ]
    }


# ============ 权限管理API ============

@router.get("/permissions", summary="获取权限列表")
async def get_permissions(
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有权限"""
    query = db.query(Permission).filter(Permission.is_deleted == False)
    
    if resource_type:
        query = query.filter(Permission.resource_type == resource_type)
    
    permissions = query.order_by(Permission.resource_type, Permission.code).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "description": p.description,
                "resource_type": p.resource_type,
                "resource_path": p.resource_path,
                "http_method": p.http_method,
                "is_enabled": p.is_enabled,
            }
            for p in permissions
        ]
    }


@router.post("/permissions", summary="创建权限")
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """创建新权限"""
    existing = db.query(Permission).filter(Permission.code == permission_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="权限代码已存在")
    
    permission = Permission(
        name=permission_data.name,
        code=permission_data.code,
        description=permission_data.description,
        resource_type=permission_data.resource_type,
        resource_path=permission_data.resource_path,
        http_method=permission_data.http_method,
        created_by=current_user.id
    )
    
    db.add(permission)
    db.commit()
    
    return {"code": 200, "message": "权限创建成功", "data": {"id": permission.id}}


# ============ 部门管理API ============

@router.get("/departments", summary="获取部门列表")
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有部门（树形结构）"""
    departments = db.query(Department).filter(
        Department.is_deleted == False,
        Department.parent_id == None
    ).order_by(Department.sort_order).all()
    
    def build_tree(dept):
        return {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "parent_id": dept.parent_id,
            "leader": dept.leader,
            "phone": dept.phone,
            "email": dept.email,
            "is_enabled": dept.is_enabled,
            "children": [build_tree(c) for c in dept.children if not c.is_deleted]
        }
    
    return {"code": 200, "data": [build_tree(d) for d in departments]}


@router.post("/departments", summary="创建部门")
async def create_department(
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """创建新部门"""
    existing = db.query(Department).filter(Department.code == dept_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="部门代码已存在")
    
    department = Department(
        name=dept_data.name,
        code=dept_data.code,
        parent_id=dept_data.parent_id,
        leader=dept_data.leader,
        phone=dept_data.phone,
        email=dept_data.email
    )
    
    db.add(department)
    db.commit()
    
    return {"code": 200, "message": "部门创建成功", "data": {"id": department.id}}


# ============ 审计日志API ============

@router.get("/audit-logs", summary="获取审计日志")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取审计日志"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "data": {
            "items": [
                {
                    "id": log.id,
                    "username": log.username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_name": log.resource_name,
                    "ip_address": log.ip_address,
                    "is_success": log.is_success,
                    "duration_ms": log.duration_ms,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


# ============ 当前用户信息API ============

@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    return {
        "code": 200,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "phone": current_user.phone,
            "real_name": current_user.real_name,
            "avatar": current_user.avatar,
            "status": current_user.status.value if current_user.status else None,
            "data_level": current_user.data_level.value if current_user.data_level else None,
            "roles": [{"id": r.id, "name": r.name, "code": r.code} for r in current_user.roles],
            "permissions": list(set([p.code for r in current_user.roles for p in r.permissions if p.is_enabled])),
        }
    }


@router.post("/me/password", summary="修改密码")
async def change_password(
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改当前用户密码"""
    if not bcrypt.checkpw(old_password.encode(), current_user.password_hash.encode()):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    current_user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    current_user.password_changed_at = datetime.now()
    current_user.must_change_password = False
    db.commit()
    
    return {"code": 200, "message": "密码修改成功"}
