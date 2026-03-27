"""
用户权限管理模块 - 初始化脚本
用于初始化数据库、创建默认管理员等
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from models.database import init_db, get_db_session
from models.auth_models import User, Role, Permission
from core.security import get_password_hash, Role as RoleEnum, Permission as PermissionCode, ROLE_PERMISSIONS


def init_database():
    """初始化数据库表"""
    print("初始化数据库表...")
    init_db()
    print("✅ 数据库表初始化完成")


def create_default_admin(db: Session):
    """创建默认管理员账号"""
    # 检查是否已存在超级管理员
    existing = db.query(User).filter(User.role == RoleEnum.SUPER_ADMIN).first()
    if existing:
        print(f"超级管理员已存在: {existing.username}")
        return
    
    # 创建默认管理员
    admin = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),  # 默认密码，建议首次登录后修改
        full_name="系统管理员",
        department="系统管理部",
        role=RoleEnum.SUPER_ADMIN,
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin)
    db.commit()
    print("✅ 默认管理员已创建")
    print("   用户名: admin")
    print("   密码: admin123")
    print("   ⚠️ 请首次登录后立即修改默认密码！")


def create_test_users(db: Session):
    """创建测试用户（仅用于开发环境）"""
    test_users = [
        {
            "username": "deptadmin",
            "email": "deptadmin@example.com",
            "password": "dept123",
            "full_name": "部门管理员",
            "department": "研发部",
            "role": RoleEnum.DEPT_ADMIN
        },
        {
            "username": "engineer",
            "email": "engineer@example.com",
            "password": "eng123",
            "full_name": "工程师张三",
            "department": "研发部",
            "role": RoleEnum.ENGINEER
        },
        {
            "username": "visitor",
            "email": "visitor@example.com",
            "password": "visitor123",
            "full_name": "访客李四",
            "department": "访客部",
            "role": RoleEnum.VISITOR
        }
    ]
    
    for user_data in test_users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            print(f"用户 {user_data['username']} 已存在，跳过")
            continue
        
        user = User(
            id=str(uuid.uuid4()),
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            department=user_data["department"],
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
        print(f"✅ 测试用户已创建: {user_data['username']}")
    
    db.commit()


def main():
    """主函数"""
    print("="*50)
    print("AI知识库 - 用户权限管理模块初始化")
    print("="*50)
    
    # 初始化数据库表
    init_database()
    
    # 创建默认管理员
    db = get_db_session()
    try:
        create_default_admin(db)
        # 可选：创建测试用户（开发环境）
        # create_test_users(db)
    finally:
        db.close()
    
    print("="*50)
    print("初始化完成！")
    print("="*50)


if __name__ == "__main__":
    main()
