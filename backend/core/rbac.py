"""
RBAC Core - 权限控制核心
v0.2.0
包含 @require_permission 装饰器
"""
import functools
from typing import Callable, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database import get_db
from backend.models.rbac_models import User, Permission

security = HTTPBearer()


def decode_token(token: str) -> dict:
    """解码JWT Token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从Token中获取当前用户"""
    payload = decode_token(credentials.credentials)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user


def require_permission(
    permission_code: Union[str, list[str]],
    require_all: bool = False,
):
    """
    权限校验装饰器

    用法:
        @router.get("/documents")
        @require_permission("document:read")
        async def list_documents(user: User = Depends(get_current_user)):
            ...

        # 满足任一权限即可
        @router.delete("/documents/{id}")
        @require_permission(["document:delete", "document:update"])
        async def delete_document(user: User = Depends(get_current_user)):
            ...

        # 需要满足所有权限
        @router.post("/documents/batch")
        @require_permission(["document:create", "document:read"], require_all=True)
        async def batch_create(user: User = Depends(get_current_user)):
            ...

    参数:
        permission_code: 单个权限码或权限码列表
        require_all: False=满足任一权限(OR), True=满足所有权限(AND)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中获取 get_current_user 依赖注入的 user
            user: Optional[User] = kwargs.get("user")
            if user is None:
                # 尝试从Depends注入的参数中获取
                for arg in args:
                    if isinstance(arg, User):
                        user = arg
                        break

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证",
                )

            # 检查超级管理员
            if user.is_superuser:
                return await func(*args, **kwargs)

            codes = [permission_code] if isinstance(permission_code, str) else permission_code

            for code in codes:
                if code == "*":
                    return await func(*args, **kwargs)

            if require_all:
                # 需满足所有权限
                missing = [c for c in codes if not user.has_permission(c)]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要权限: {', '.join(missing)}",
                    )
            else:
                # 满足任一权限即可
                has_any = any(user.has_permission(c) for c in codes)
                if not has_any:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"权限不足，需要以下任一权限: {', '.join(codes)}",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_code: Union[str, list[str]], require_all: bool = False):
    """
    角色校验装饰器

    用法:
        @router.delete("/users/{id}")
        @require_role("admin")
        async def delete_user(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            user: Optional[User] = kwargs.get("user")
            if user is None:
                for arg in args:
                    if isinstance(arg, User):
                        user = arg
                        break

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证",
                )

            if user.is_superuser:
                return await func(*args, **kwargs)

            roles = [role_code] if isinstance(role_code, str) else role_code

            if require_all:
                missing = [r for r in roles if not user.has_role(r)]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要角色: {', '.join(missing)}",
                    )
            else:
                has_any = any(user.has_role(r) for r in roles)
                if not has_any:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"角色不足，需要以下任一角色: {', '.join(roles)}",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """
    FastAPI 依赖项方式的权限检查器

    用法 (作为 Depends):
        @router.get("/documents", dependencies=[Depends(PermissionChecker("document:read"))])
        async def list_documents():
            ...
    """

    def __init__(self, permission_code: Union[str, list[str]], require_all: bool = False):
        self.permission_codes = [permission_code] if isinstance(permission_code, str) else permission_code
        self.require_all = require_all

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user

        for code in self.permission_codes:
            if code == "*":
                return user

        if self.require_all:
            missing = [c for c in self.permission_codes if not user.has_permission(c)]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要权限: {', '.join(missing)}",
                )
        else:
            has_any = any(user.has_permission(c) for c in self.permission_codes)
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任一权限: {', '.join(self.permission_codes)}",
                )
        return user


async def init_default_rbac(db: Session):
    """
    初始化默认 RBAC 数据（角色和权限）
    在系统首次启动时调用
    """
    from backend.models.rbac_models import DEFAULT_PERMISSIONS, DEFAULT_ROLES, Permission, Role

    # 创建默认权限
    existing_codes = {p.code for p in db.query(Permission).all()}
    for perm_data in DEFAULT_PERMISSIONS:
        if perm_data["code"] not in existing_codes:
            perm = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                resource_type=perm_data["resource_type"],
                action=perm_data["action"],
            )
            db.add(perm)

    db.flush()

    # 创建默认角色
    existing_role_codes = {r.code for r in db.query(Role).all()}
    for role_data in DEFAULT_ROLES:
        if role_data["code"] not in existing_role_codes:
            role = Role(
                code=role_data["code"],
                name=role_data["name"],
                description=role_data["description"],
                is_system=role_data["is_system"],
            )
            db.add(role)
            db.flush()

            # 关联权限
            perm_codes = role_data["permissions"]
            if "*" in perm_codes:
                all_perms = db.query(Permission).all()
                role.permissions = all_perms
            else:
                perms = db.query(Permission).filter(
                    Permission.code.in_(perm_codes)
                ).all()
                role.permissions = perms

    db.commit()
