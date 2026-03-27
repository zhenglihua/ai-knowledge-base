"""
权限验证中间件
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import jwt
import time

from backend.models.database import get_db
from backend.models.auth_models import User, Permission, AuditLog

# JWT配置
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


async def get_token_data(request: Request) -> Optional[dict]:
    """从请求中获取Token数据"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    payload = await get_token_data(request)
    if not payload:
        raise HTTPException(status_code=401, detail="未登录或Token无效")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token无效")
    
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已被禁用")
    
    return user


async def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if not current_user.has_role("admin") and not current_user.has_role("super_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def require_permissions(*permission_codes: str):
    """权限验证装饰器"""
    async def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> User:
        # 超级管理员拥有所有权限
        if current_user.has_role("super_admin"):
            return current_user
        
        # 检查权限
        for code in permission_codes:
            if not current_user.has_permission(code):
                raise HTTPException(status_code=403, detail=f"缺少权限: {code}")
        
        return current_user
    
    return permission_checker


def require_roles(*role_codes: str):
    """角色验证装饰器"""
    async def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        for code in role_codes:
            if current_user.has_role(code):
                return current_user
        
        raise HTTPException(status_code=403, detail=f"需要角色: {role_codes}")
    
    return role_checker


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, action: str, resource_type: str = None):
        self.action = action
        self.resource_type = resource_type
    
    async def log(
        self,
        request: Request,
        db: Session,
        user: User,
        resource_id: str = None,
        resource_name: str = None,
        is_success: bool = True,
        error_message: str = None
    ):
        """记录审计日志"""
        start_time = request.state.start_time if hasattr(request.state, 'start_time') else None
        duration_ms = None
        if start_time:
            duration_ms = int((time.time() - start_time) * 1000)
        
        log_entry = AuditLog(
            user_id=user.id,
            username=user.username,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            request_method=request.method,
            request_path=str(request.url.path),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            is_success=is_success,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        db.add(log_entry)
        db.commit()


def create_access_token(user_id: int, username: str, expires_in: int = 86400) -> str:
    """创建JWT Token"""
    import datetime
    
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time())
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码JWT Token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None


# 数据权限过滤
def filter_by_data_level(query, user: User, model_class):
    """根据用户数据权限等级过滤查询结果"""
    if user.has_role("super_admin") or user.has_role("admin"):
        return query  # 管理员不受限制
    
    user_data_level = user.data_level.value if user.data_level else "internal"
    
    # 数据等级映射到数值
    level_map = {
        "public": 0,
        "internal": 1,
        "confidential": 2,
        "top_secret": 3
    }
    
    user_level = level_map.get(user_data_level, 1)
    
    # 过滤条件：只能看到权限等级 <= 自身等级的数据
    if hasattr(model_class, 'data_level'):
        from backend.models.auth_models import DataLevel
        # 这里需要根据实际字段类型调整过滤逻辑
        pass
    
    return query
