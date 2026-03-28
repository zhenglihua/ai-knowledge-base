"""
认证与授权模块
提供JWT Token生成、验证和权限控制
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os

from models.database import get_db

# 安全配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# 角色定义
class Role:
    SUPER_ADMIN = "super_admin"      # 超级管理员
    DEPT_ADMIN = "dept_admin"        # 部门管理员
    ENGINEER = "engineer"            # 工程师
    VISITOR = "visitor"              # 访客

# 权限定义
class Permission:
    # 文档权限
    DOC_VIEW = "doc:view"            # 查看文档
    DOC_UPLOAD = "doc:upload"        # 上传文档
    DOC_EDIT = "doc:edit"            # 编辑文档
    DOC_DELETE = "doc:delete"        # 删除文档
    DOC_DOWNLOAD = "doc:download"    # 下载文档
    
    # 用户管理权限
    USER_VIEW = "user:view"          # 查看用户
    USER_CREATE = "user:create"      # 创建用户
    USER_EDIT = "user:edit"          # 编辑用户
    USER_DELETE = "user:delete"      # 删除用户
    
    # 角色管理权限
    ROLE_VIEW = "role:view"          # 查看角色
    ROLE_CREATE = "role:create"      # 创建角色
    ROLE_EDIT = "role:edit"          # 编辑角色
    ROLE_DELETE = "role:delete"      # 删除角色
    
    # 系统权限
    SYS_CONFIG = "sys:config"        # 系统配置
    SYS_AUDIT = "sys:audit"          # 查看审计日志
    SYS_STATS = "sys:stats"          # 查看统计数据

# 角色-权限映射
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    Role.SUPER_ADMIN: [
        Permission.DOC_VIEW, Permission.DOC_UPLOAD, Permission.DOC_EDIT, 
        Permission.DOC_DELETE, Permission.DOC_DOWNLOAD,
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_EDIT, Permission.USER_DELETE,
        Permission.ROLE_VIEW, Permission.ROLE_CREATE, Permission.ROLE_EDIT, Permission.ROLE_DELETE,
        Permission.SYS_CONFIG, Permission.SYS_AUDIT, Permission.SYS_STATS
    ],
    Role.DEPT_ADMIN: [
        Permission.DOC_VIEW, Permission.DOC_UPLOAD, Permission.DOC_EDIT, Permission.DOC_DOWNLOAD,
        Permission.USER_VIEW, Permission.USER_CREATE,
        Permission.SYS_STATS
    ],
    Role.ENGINEER: [
        Permission.DOC_VIEW, Permission.DOC_UPLOAD, Permission.DOC_DOWNLOAD,
    ],
    Role.VISITOR: [
        Permission.DOC_VIEW
    ]
}

# 数据密级定义
class Classification:
    PUBLIC = 1        # 公开
    INTERNAL = 2      # 内部
    CONFIDENTIAL = 3  # 机密
    SECRET = 4        # 绝密

# 用户-密级映射（用户可访问的最高密级）
USER_MAX_CLASSIFICATION: Dict[str, int] = {
    Role.SUPER_ADMIN: Classification.SECRET,
    Role.DEPT_ADMIN: Classification.CONFIDENTIAL,
    Role.ENGINEER: Classification.INTERNAL,
    Role.VISITOR: Classification.PUBLIC
}

# 密级名称映射
CLASSIFICATION_NAMES = {
    Classification.PUBLIC: "公开",
    Classification.INTERNAL: "内部",
    Classification.CONFIDENTIAL: "机密",
    Classification.SECRET: "绝密"
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """获取当前用户（依赖注入）"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户信息
    from models.auth_models import User
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "max_classification": USER_MAX_CLASSIFICATION.get(user.role, Classification.PUBLIC)
    }


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取当前活跃用户"""
    return current_user


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """获取当前管理员用户（仅限管理员角色）"""
    if current_user.get("role") != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_permissions(*permissions: str):
    """权限检查装饰器"""
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", Role.VISITOR)
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        
        # 超级管理员拥有所有权限
        if user_role == Role.SUPER_ADMIN:
            return current_user
        
        # 检查是否有所需权限
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足: 需要 {permission} 权限"
                )
        
        return current_user
    
    return permission_checker


def require_role(*roles: str):
    """角色检查装饰器"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色权限不足"
            )
        return current_user
    
    return role_checker


def can_access_classification(user_classification: int, doc_classification: int) -> bool:
    """检查用户是否有权限访问指定密级的文档"""
    return user_classification >= doc_classification


def check_document_access(user: dict, doc_classification: int, action: str = "view") -> bool:
    """检查用户对文档的访问权限"""
    user_role = user.get("role", Role.VISITOR)
    user_max_classification = user.get("max_classification", Classification.PUBLIC)
    
    # 检查密级权限
    if not can_access_classification(user_max_classification, doc_classification):
        return False
    
    # 检查操作权限
    action_permissions = {
        "view": Permission.DOC_VIEW,
        "upload": Permission.DOC_UPLOAD,
        "edit": Permission.DOC_EDIT,
        "delete": Permission.DOC_DELETE,
        "download": Permission.DOC_DOWNLOAD
    }
    
    required_permission = action_permissions.get(action)
    if required_permission:
        user_permissions = ROLE_PERMISSIONS.get(user_role, [])
        if required_permission not in user_permissions:
            return False
    
    return True
