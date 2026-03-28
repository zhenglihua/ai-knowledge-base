"""
RBAC Data Models - Role-Based Access Control
v0.2.0
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.database import Base


class ResourceType(str, Enum):
    """资源类型枚举"""
    DOCUMENT = "document"
    GRAPH = "graph"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"
    NRE = "nre"


class ActionType(str, Enum):
    """操作类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"      # 包含所有操作
    EXPORT = "export"
    IMPORT = "import"


# --- 关联表 ---
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles: Mapped[list["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # 系统内置角色不可删除
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users: Mapped[list["User"]] = relationship("User", secondary=user_roles, back_populates="roles")

    def has_permission(self, permission_code: str) -> bool:
        """检查角色是否拥有指定权限"""
        return any(p.code == permission_code for p in self.permissions if p.is_active)

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(Base):
    """用户模型扩展 - RBAC部分"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles: Mapped[list["Role"]] = relationship("Role", secondary=user_roles, back_populates="users")

    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        if self.is_superuser:
            return True
        for role in self.roles:
            if role.is_active and role.has_permission(permission_code):
                return True
        return False

    def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色"""
        return any(role.code == role_code and role.is_active for role in self.roles)

    def get_all_permissions(self) -> set[str]:
        """获取用户所有权限码集合"""
        if self.is_superuser:
            return {"*"}  # 表示所有权限
        permissions = set()
        for role in self.roles:
            if role.is_active:
                for p in role.permissions:
                    if p.is_active:
                        permissions.add(p.code)
        return permissions

    def __repr__(self) -> str:
        return f"<User {self.username}>"


# --- 默认角色 & 权限定义 ---
DEFAULT_PERMISSIONS = [
    # 文档权限
    {"code": "document:create", "name": "创建文档", "resource_type": ResourceType.DOCUMENT, "action": ActionType.CREATE},
    {"code": "document:read", "name": "查看文档", "resource_type": ResourceType.DOCUMENT, "action": ActionType.READ},
    {"code": "document:update", "name": "编辑文档", "resource_type": ResourceType.DOCUMENT, "action": ActionType.UPDATE},
    {"code": "document:delete", "name": "删除文档", "resource_type": ResourceType.DOCUMENT, "action": ActionType.DELETE},
    # 图谱权限
    {"code": "graph:create", "name": "创建图谱", "resource_type": ResourceType.GRAPH, "action": ActionType.CREATE},
    {"code": "graph:read", "name": "查看图谱", "resource_type": ResourceType.GRAPH, "action": ActionType.READ},
    {"code": "graph:update", "name": "编辑图谱", "resource_type": ResourceType.GRAPH, "action": ActionType.UPDATE},
    {"code": "graph:delete", "name": "删除图谱", "resource_type": ResourceType.GRAPH, "action": ActionType.DELETE},
    # 用户管理权限
    {"code": "user:create", "name": "创建用户", "resource_type": ResourceType.USER, "action": ActionType.CREATE},
    {"code": "user:read", "name": "查看用户", "resource_type": ResourceType.USER, "action": ActionType.READ},
    {"code": "user:update", "name": "编辑用户", "resource_type": ResourceType.USER, "action": ActionType.UPDATE},
    {"code": "user:delete", "name": "删除用户", "resource_type": ResourceType.USER, "action": ActionType.DELETE},
    # 角色管理权限
    {"code": "role:create", "name": "创建角色", "resource_type": ResourceType.ROLE, "action": ActionType.CREATE},
    {"code": "role:read", "name": "查看角色", "resource_type": ResourceType.ROLE, "action": ActionType.READ},
    {"code": "role:update", "name": "编辑角色", "resource_type": ResourceType.ROLE, "action": ActionType.UPDATE},
    {"code": "role:delete", "name": "删除角色", "resource_type": ResourceType.ROLE, "action": ActionType.DELETE},
    # NRE权限
    {"code": "nre:execute", "name": "执行NRE", "resource_type": ResourceType.NRE, "action": ActionType.CREATE},
    {"code": "nre:read", "name": "查看NRE结果", "resource_type": ResourceType.NRE, "action": ActionType.READ},
]

DEFAULT_ROLES = [
    {
        "code": "admin",
        "name": "管理员",
        "description": "系统管理员，拥有所有权限",
        "is_system": True,
        "permissions": ["*"],  # * 表示所有权限
    },
    {
        "code": "editor",
        "name": "编辑者",
        "description": "文档和图谱编辑人员",
        "is_system": False,
        "permissions": [
            "document:create", "document:read", "document:update", "document:delete",
            "graph:create", "graph:read", "graph:update", "graph:delete",
            "nre:execute", "nre:read",
        ],
    },
    {
        "code": "viewer",
        "name": "查看者",
        "description": "只读用户",
        "is_system": False,
        "permissions": [
            "document:read", "graph:read", "nre:read",
        ],
    },
]
