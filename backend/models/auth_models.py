"""
权限管理系统 - 数据库模型
基于RBAC模型的完整权限设计
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
import enum


class DataLevel(str, enum.Enum):
    """数据分级枚举"""
    PUBLIC = "public"       # 公开
    INTERNAL = "internal"    # 内部
    CONFIDENTIAL = "confidential"  # 机密
    TOP_SECRET = "top_secret"      # 绝密


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


# 用户-角色关联表
user_roles = Table(
    'sys_user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('sys_users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('sys_roles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, server_default=func.now()),
)

# 角色-权限关联表
role_permissions = Table(
    'sys_role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('sys_roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('sys_permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, server_default=func.now()),
)

# 用户-部门关联表
user_departments = Table(
    'sys_user_departments',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('sys_users.id', ondelete='CASCADE'), primary_key=True),
    Column('department_id', Integer, ForeignKey('sys_departments.id', ondelete='CASCADE'), primary_key=True),
    Column('is_primary', Boolean, default=True),  # 是否主要部门
    Column('created_at', DateTime, server_default=func.now()),
)


class User(Base):
    """用户表"""
    __tablename__ = 'sys_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, index=True, comment='邮箱')
    phone = Column(String(20), nullable=True, comment='手机号')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    real_name = Column(String(100), nullable=True, comment='真实姓名')
    avatar = Column(String(500), nullable=True, comment='头像URL')
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, comment='状态')
    data_level = Column(Enum(DataLevel), default=DataLevel.INTERNAL, comment='用户数据权限等级')
    last_login_at = Column(DateTime, nullable=True, comment='最后登录时间')
    last_login_ip = Column(String(50), nullable=True, comment='最后登录IP')
    password_changed_at = Column(DateTime, nullable=True, comment='密码修改时间')
    must_change_password = Column(Boolean, default=False, comment='下次登录必须修改密码')
    remark = Column(Text, nullable=True, comment='备注')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(Integer, ForeignKey('sys_users.id'), nullable=True, comment='创建人')
    
    # 关系
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    departments = relationship('Department', secondary=user_departments, back_populates='users')
    created_users = relationship('User', backref='creator', remote_side=[id])
    audit_logs = relationship('AuditLog', back_populates='user', foreign_keys='AuditLog.user_id')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        if self.status != UserStatus.ACTIVE:
            return False
        for role in self.roles:
            for permission in role.permissions:
                if permission.code == permission_code and permission.is_enabled:
                    return True
        return False
    
    def has_role(self, role_code: str) -> bool:
        """检查用户是否有指定角色"""
        for role in self.roles:
            if role.code == role_code and role.is_enabled:
                return True
        return False


class Role(Base):
    """角色表"""
    __tablename__ = 'sys_roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='角色名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='角色代码')
    description = Column(String(255), nullable=True, comment='角色描述')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    is_system = Column(Boolean, default=False, comment='是否系统内置（系统内置不可删除）')
    data_level = Column(Enum(DataLevel), default=DataLevel.INTERNAL, comment='角色默认数据权限等级')
    sort_order = Column(Integer, default=0, comment='排序')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(Integer, ForeignKey('sys_users.id'), nullable=True, comment='创建人')
    
    # 关系
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')
    creator = relationship('User')
    
    def __repr__(self):
        return f'<Role {self.code}>'


class Permission(Base):
    """权限表"""
    __tablename__ = 'sys_permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='权限名称')
    code = Column(String(100), unique=True, nullable=False, index=True, comment='权限代码')
    description = Column(String(255), nullable=True, comment='权限描述')
    resource_type = Column(String(20), nullable=True, comment='资源类型: menu, button, api, data')
    resource_path = Column(String(255), nullable=True, comment='资源路径')
    http_method = Column(String(10), nullable=True, comment='HTTP方法: GET, POST, PUT, DELETE')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(Integer, ForeignKey('sys_users.id'), nullable=True, comment='创建人')
    
    # 关系
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')
    creator = relationship('User')
    
    def __repr__(self):
        return f'<Permission {self.code}>'


class Department(Base):
    """部门表"""
    __tablename__ = 'sys_departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='部门名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='部门代码')
    parent_id = Column(Integer, ForeignKey('sys_departments.id', ondelete='SET NULL'), nullable=True, comment='上级部门')
    leader = Column(String(50), nullable=True, comment='部门负责人')
    phone = Column(String(20), nullable=True, comment='联系电话')
    email = Column(String(100), nullable=True, comment='部门邮箱')
    sort_order = Column(Integer, default=0, comment='排序')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    is_deleted = Column(Boolean, default=False, comment='软删除标记')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    parent = relationship('Department', remote_side=[id], backref='children')
    users = relationship('User', secondary=user_departments, back_populates='departments')
    
    def __repr__(self):
        return f'<Department {self.code}>'
    
    def get_all_children(self):
        """获取所有子部门"""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_all_children())
        return children


class DocumentAccessLog(Base):
    """文档访问日志表"""
    __tablename__ = 'sys_document_access_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('sys_users.id', ondelete='SET NULL'), nullable=True, comment='用户ID')
    document_id = Column(String(100), nullable=True, comment='文档ID')
    document_title = Column(String(255), nullable=True, comment='文档标题')
    action = Column(String(50), nullable=False, comment='操作类型: view, download, search, chat')
    ip_address = Column(String(50), nullable=True, comment='IP地址')
    user_agent = Column(String(500), nullable=True, comment='User-Agent')
    search_query = Column(Text, nullable=True, comment='搜索关键词')
    chat_query = Column(Text, nullable=True, comment='聊天问题')
    chat_answer = Column(Text, nullable=True, comment='AI回答')
    created_at = Column(DateTime, server_default=func.now(), index=True, comment='访问时间')
    
    def __repr__(self):
        return f'<DocumentAccessLog {self.action} on {self.document_id}>'


class RefreshToken(Base):
    """刷新令牌表"""
    __tablename__ = 'sys_refresh_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('sys_users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    token = Column(String(500), unique=True, nullable=False, index=True, comment='刷新令牌')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    is_revoked = Column(Boolean, default=False, comment='是否已撤销')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    revoked_at = Column(DateTime, nullable=True, comment='撤销时间')
    ip_address = Column(String(50), nullable=True, comment='IP地址')
    user_agent = Column(String(500), nullable=True, comment='User-Agent')
    
    # 关系
    user = relationship('User', backref='refresh_tokens')
    
    def __repr__(self):
        return f'<RefreshToken for user {self.user_id}>'


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = 'sys_audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('sys_users.id', ondelete='SET NULL'), nullable=True, comment='用户ID')
    username = Column(String(50), nullable=True, comment='用户名')
    action = Column(String(50), nullable=False, comment='操作类型: login, logout, create, update, delete, query, export, download')
    resource_type = Column(String(50), nullable=True, comment='资源类型')
    resource_id = Column(String(100), nullable=True, comment='资源ID')
    resource_name = Column(String(255), nullable=True, comment='资源名称')
    request_method = Column(String(10), nullable=True, comment='请求方法')
    request_path = Column(String(500), nullable=True, comment='请求路径')
    request_params = Column(Text, nullable=True, comment='请求参数')
    request_body = Column(Text, nullable=True, comment='请求体')
    response_code = Column(String(10), nullable=True, comment='响应码')
    response_message = Column(String(500), nullable=True, comment='响应消息')
    ip_address = Column(String(50), nullable=True, comment='IP地址')
    user_agent = Column(String(500), nullable=True, comment='User-Agent')
    is_success = Column(Boolean, default=True, comment='是否成功')
    error_message = Column(Text, nullable=True, comment='错误信息')
    duration_ms = Column(Integer, nullable=True, comment='耗时毫秒')
    created_at = Column(DateTime, server_default=func.now(), index=True, comment='操作时间')
    
    # 关系
    user = relationship('User', back_populates='audit_logs', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.username}>'
