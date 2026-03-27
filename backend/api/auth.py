"""
认证API - 登录/注册/登出/Token刷新
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from models.database import get_db
from models.auth_models import User, RefreshToken
from core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    decode_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES,
    Role as RoleEnum, Classification
)
from core.audit import AuditService

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============ 数据模型 ============

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    department: Optional[str]
    role: str
    role_name: str
    max_classification: int
    classification_name: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

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

def get_classification_name(level: int) -> str:
    """获取密级名称"""
    classification_names = {
        Classification.PUBLIC: "公开",
        Classification.INTERNAL: "内部",
        Classification.CONFIDENTIAL: "机密",
        Classification.SECRET: "绝密"
    }
    return classification_names.get(level, "公开")

# ============ API端点 ============

@router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.username)
    ).first()
    
    client = get_client_info(req)
    
    if not user or not verify_password(request.password, user.hashed_password):
        # 记录失败日志
        AuditService.log_action(
            user_id=user.id if user else None,
            username=request.username,
            action="login_failed",
            module="auth",
            description="登录失败：用户名或密码错误",
            ip_address=client["ip"],
            user_agent=client["user_agent"],
            status="failure"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        AuditService.log_action(
            user_id=user.id,
            username=user.username,
            action="login_failed",
            module="auth",
            description="登录失败：账户已被禁用",
            ip_address=client["ip"],
            user_agent=client["user_agent"],
            status="failure"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 检查账户是否被锁定
    if user.locked_until and user.locked_until > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"账户已锁定，请在 {user.locked_until.strftime('%Y-%m-%d %H:%M')} 后重试"
        )
    
    # 重置失败登录次数
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now()
    db.commit()
    
    # 获取用户权限级别
    max_classification = {
        RoleEnum.SUPER_ADMIN: Classification.SECRET,
        RoleEnum.DEPT_ADMIN: Classification.CONFIDENTIAL,
        RoleEnum.ENGINEER: Classification.INTERNAL,
        RoleEnum.VISITOR: Classification.PUBLIC
    }.get(user.role, Classification.PUBLIC)
    
    # 创建Token
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "department": user.department
    }
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token({"sub": user.id})
    
    # 保存刷新Token
    refresh_token_record = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    db.add(refresh_token_record)
    db.commit()
    
    # 记录成功登录
    AuditService.log_action(
        user_id=user.id,
        username=user.username,
        action="login_success",
        module="auth",
        description="登录成功",
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role,
            "role_name": get_role_name(user.role),
            "max_classification": max_classification,
            "classification_name": get_classification_name(max_classification)
        }
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )
    
    client = get_client_info(req)
    
    # 创建用户（默认访客角色）
    user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        department=request.department,
        role=RoleEnum.VISITOR,  # 默认访客角色
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 记录审计日志
    AuditService.log_action(
        user_id=user.id,
        username=user.username,
        action="register",
        module="auth",
        resource_type="user",
        resource_id=user.id,
        description=f"新用户注册: {user.username}",
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {
        "message": "注册成功",
        "user_id": user.id
    }

@router.post("/logout")
async def logout(
    req: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    client = get_client_info(req)
    
    # 撤销该用户的所有刷新Token（可选：也可以只撤销当前Token）
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user["id"]
    ).update({"is_revoked": True})
    
    db.commit()
    
    # 记录审计日志
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="logout",
        module="auth",
        description="用户登出",
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {"message": "登出成功"}

@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问Token"""
    # 验证刷新Token
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新Token"
        )
    
    user_id = payload.get("sub")
    
    # 检查刷新Token是否存在于数据库且未被撤销
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == request.refresh_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新Token已过期或已被撤销"
        )
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新的访问Token
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "department": user.department
    }
    new_access_token = create_access_token(token_data)
    
    # 更新刷新Token最后使用时间
    token_record.last_used_at = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    max_classification = {
        RoleEnum.SUPER_ADMIN: Classification.SECRET,
        RoleEnum.DEPT_ADMIN: Classification.CONFIDENTIAL,
        RoleEnum.ENGINEER: Classification.INTERNAL,
        RoleEnum.VISITOR: Classification.PUBLIC
    }.get(current_user["role"], Classification.PUBLIC)
    
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "department": current_user.get("department"),
        "role": current_user["role"],
        "role_name": get_role_name(current_user["role"]),
        "max_classification": max_classification,
        "classification_name": get_classification_name(max_classification)
    }

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    req: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # 验证旧密码
    if not verify_password(request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    user.hashed_password = get_password_hash(request.new_password)
    user.password_changed_at = datetime.now()
    db.commit()
    
    # 记录审计日志
    client = get_client_info(req)
    AuditService.log_action(
        user_id=current_user["id"],
        username=current_user["username"],
        action="change_password",
        module="auth",
        resource_type="user",
        resource_id=user.id,
        description="用户修改密码",
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    
    return {"message": "密码修改成功"}
