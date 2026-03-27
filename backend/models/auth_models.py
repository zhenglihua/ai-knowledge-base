"""
用户认证与授权的数据库模型
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base

# 用户-角色关联表（多对多）
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('role_id', String, ForeignKey('roles.id'))
)

# 角色-权限关联表（多对多）
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.id')),
    Column('permission_id', String, ForeignKey('permissions.id'))
)


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # 用户信息
    full_name = Column(String)
    phone = Column(String)
    department = Column(String)
    avatar = Column(String)  # 头像URL
    
    # 角色与状态
    role = Column(String, default="visitor")  # super_admin/dept_admin/engineer/visitor
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 安全相关
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.now)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    """角色表"""
    __tablename__ = 'roles'
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # 角色级别（用于权限继承）
    level = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统预设角色不可删除
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """权限表"""
    __tablename__ = 'permissions'
    
    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # 权限代码，如 doc:view
    name = Column(String, nullable=False)  # 权限名称
    description = Column(Text)
    module = Column(String)  # 所属模块，如 document, user, system
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class RefreshToken(Base):
    """刷新Token表（用于Token刷新和撤销）"""
    __tablename__ = 'refresh_tokens'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    
    # Token状态
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    
    # 设备信息
    device_info = Column(String)  # 设备标识
    ip_address = Column(String)
    user_agent = Column(String)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    last_used_at = Column(DateTime)
    
    # 关联
    user = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(String, ForeignKey('users.id'))
    username = Column(String)
    
    # 操作信息
    action = Column(String, nullable=False, index=True)  # 操作类型
    module = Column(String)  # 操作模块
    resource_type = Column(String)  # 资源类型（document, user等）
    resource_id = Column(String)  # 资源ID
    
    # 详细内容
    description = Column(Text)  # 操作描述
    old_values = Column(Text)  # 修改前的值（JSON）
    new_values = Column(Text)  # 修改后的值（JSON）
    
    # 访问信息
    ip_address = Column(String)
    user_agent = Column(String)
    request_method = Column(String)
    request_path = Column(String)
    request_params = Column(Text)  # 请求参数（JSON）
    
    # 结果
    status = Column(String, default="success")  # success/failure
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # 关联
    user = relationship("User", back_populates="audit_logs")


class DocumentAccessLog(Base):
    """文档访问日志表（专门记录文档相关操作）"""
    __tablename__ = 'document_access_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(String, ForeignKey('users.id'))
    username = Column(String)
    
    # 文档信息
    document_id = Column(String)  # 文档ID
    document_title = Column(String)
    document_classification = Column(Integer)  # 文档密级
    
    # 操作类型
    action = Column(String, nullable=False)  # view/download/edit/delete/upload
    
    # 访问信息
    ip_address = Column(String)
    user_agent = Column(String)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, index=True)


class Department(Base):
    """部门表"""
    __tablename__ = 'departments'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # 层级关系
    parent_id = Column(String, ForeignKey('departments.id'))
    level = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    children = relationship("Department", backref="parent", remote_side=[id])
