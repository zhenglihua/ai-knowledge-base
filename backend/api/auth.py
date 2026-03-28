"""
简化版认证 API
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db_session
from models.auth_models import User, RefreshToken, UserStatus
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from core.audit import AuditService

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


def get_client_info(req: Request) -> dict:
    """获取客户端信息"""
    return {
        "ip": req.client.host if req.client else "unknown",
        "user_agent": req.headers.get("user-agent", "unknown")
    }


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login")
async def login(request: LoginRequest, req: Request, db: Session = Depends(get_db_session)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.username)
    ).first()
    
    client = get_client_info(req)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 更新最后登录信息
    user.last_login_at = datetime.now()
    db.commit()
    
    # 创建Token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
    }
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token({"sub": str(user.id)})
    
    # 保存刷新Token
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=7),
        ip_address=client["ip"],
        user_agent=client["user_agent"]
    )
    db.add(refresh_token_record)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }


@router.post("/register")
async def register(request: RegisterRequest, req: Request, db: Session = Depends(get_db_session)):
    """用户注册"""
    # 检查用户名是否存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否存在
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    client = get_client_info(req)
    
    # 创建用户
    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
        real_name=request.full_name,
        status=UserStatus.ACTIVE
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "注册成功",
        "user_id": user.id
    }


@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db_session)):
    """刷新Token"""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新的访问Token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
    }
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db_session)):
    """获取当前用户信息"""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "real_name": user.real_name,
        "status": user.status.value if user.status else None
    }


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db_session)):
    """用户登出"""
    return {"message": "登出成功"}


@router.get("/roles")
async def get_roles(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db_session)):
    """获取角色列表"""
    # 返回默认角色
    return {
        "roles": [
            {"id": 1, "name": "超级管理员", "code": "super_admin", "description": "系统超级管理员", "permissions": []},
            {"id": 2, "name": "管理员", "code": "admin", "description": "普通管理员", "permissions": []},
            {"id": 3, "name": "工程师", "code": "engineer", "description": "普通工程师", "permissions": []},
            {"id": 4, "name": "访客", "code": "visitor", "description": "访客用户", "permissions": []}
        ]
    }
