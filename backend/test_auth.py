"""
用户权限管理模块 - 测试用例
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from models.database import Base, get_db
from models.auth_models import User, Role, Permission, AuditLog, RefreshToken
from core.security import get_password_hash, verify_password, create_access_token, decode_token, Role as RoleEnum, Permission as PermissionCode, Classification

# 测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

# 创建测试数据库表
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============ 基础工具函数测试 ============

def test_password_hash():
    """测试密码加密与验证"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token():
    """测试JWT Token创建与解码"""
    data = {"sub": "test-user-id", "username": "testuser", "role": "visitor"}
    token = create_access_token(data)
    
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test-user-id"
    assert payload["username"] == "testuser"
    assert payload["role"] == "visitor"
    assert payload["type"] == "access"


# ============ 认证API测试 ============

class TestAuthAPI:
    """认证API测试类"""
    
    def test_register(self):
        """测试用户注册"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpass123",
            "full_name": "测试用户"
        })
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "注册成功"
    
    def test_register_duplicate_username(self):
        """测试重复用户名注册"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dupuser1@example.com",
            "password": "testpass123"
        })
        
        # 重复注册应该失败
        response = client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dupuser2@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 400
        assert "用户名或邮箱已存在" in response.json()["detail"]
    
    def test_login_success(self):
        """测试登录成功"""
        # 先注册
        client.post("/api/auth/register", json={
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "testpass123"
        })
        
        # 登录
        response = client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        response = client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_get_current_user(self):
        """测试获取当前用户信息"""
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": "meuser",
            "email": "meuser@example.com",
            "password": "testpass123"
        })
        
        login_resp = client.post("/api/auth/login", json={
            "username": "meuser",
            "password": "testpass123"
        })
        token = login_resp.json()["access_token"]
        
        # 获取用户信息
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["role"] == "visitor"
    
    def test_change_password(self):
        """测试修改密码"""
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": "pwduser",
            "email": "pwduser@example.com",
            "password": "oldpass123"
        })
        
        login_resp = client.post("/api/auth/login", json={
            "username": "pwduser",
            "password": "oldpass123"
        })
        token = login_resp.json()["access_token"]
        
        # 修改密码
        response = client.post("/api/auth/change-password", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "old_password": "oldpass123",
            "new_password": "newpass123"
        })
        assert response.status_code == 200
        
        # 用新密码登录
        login_resp2 = client.post("/api/auth/login", json={
            "username": "pwduser",
            "password": "newpass123"
        })
        assert login_resp2.status_code == 200


# ============ 用户管理API测试 ============

class TestUserAPI:
    """用户管理API测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        """设置管理员并获取Token"""
        db = TestingSessionLocal()
        try:
            # 创建管理员
            admin = User(
                id="admin-test-id",
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="管理员",
                role=RoleEnum.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            
            self.admin_token = create_access_token({
                "sub": "admin-test-id",
                "username": "admin",
                "role": RoleEnum.SUPER_ADMIN
            })
        finally:
            db.close()
    
    def test_create_user_as_admin(self):
        """管理员创建用户"""
        response = client.post("/api/users", headers={
            "Authorization": f"Bearer {self.admin_token}"
        }, json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "userpass123",
            "full_name": "新用户",
            "role": "engineer"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "engineer"
    
    def test_list_users(self):
        """获取用户列表"""
        response = client.get("/api/users", headers={
            "Authorization": f"Bearer {self.admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data


# ============ 权限控制测试 ============

def test_role_permissions():
    """测试角色权限定义"""
    # 超级管理员有所有权限
    admin_perms = ROLE_PERMISSIONS[RoleEnum.SUPER_ADMIN]
    assert PermissionCode.DOC_VIEW in admin_perms
    assert PermissionCode.DOC_DELETE in admin_perms
    assert PermissionCode.USER_CREATE in admin_perms
    assert PermissionCode.SYS_CONFIG in admin_perms
    
    # 访客只有查看权限
    visitor_perms = ROLE_PERMISSIONS[RoleEnum.VISITOR]
    assert PermissionCode.DOC_VIEW in visitor_perms
    assert PermissionCode.DOC_UPLOAD not in visitor_perms
    assert PermissionCode.USER_VIEW not in visitor_perms


def test_classification_levels():
    """测试密级定义"""
    assert Classification.PUBLIC == 1
    assert Classification.INTERNAL == 2
    assert Classification.CONFIDENTIAL == 3
    assert Classification.SECRET == 4
    
    # 测试密级访问权限
    from core.security import can_access_classification
    assert can_access_classification(Classification.SECRET, Classification.PUBLIC) is True
    assert can_access_classification(Classification.SECRET, Classification.SECRET) is True
    assert can_access_classification(Classification.PUBLIC, Classification.INTERNAL) is False
    assert can_access_classification(Classification.ENGINEER, Classification.CONFIDENTIAL) is False


# ============ 审计日志测试 ============

def test_audit_log_creation():
    """测试审计日志创建"""
    from core.audit import AuditService
    
    AuditService.log_action(
        user_id="test-user",
        username="testuser",
        action="test_action",
        module="test",
        description="测试日志记录"
    )
    
    # 验证日志已记录
    db = TestingSessionLocal()
    try:
        log = db.query(AuditLog).filter(AuditLog.action == "test_action").first()
        assert log is not None
        assert log.username == "testuser"
        assert log.module == "test"
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
