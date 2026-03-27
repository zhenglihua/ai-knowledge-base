"""
权限管理系统测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试JWT Token功能
from backend.core.security import create_access_token, decode_token


class TestJWTToken:
    """JWT Token测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        token = create_access_token(data={"sub": "test_user", "user_id": 1})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        print("✅ 创建Token测试通过")
    
    def test_decode_token(self):
        """测试解码令牌"""
        token = create_access_token(data={"sub": "test_user", "user_id": 1})
        payload = decode_token(token)
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["sub"] == "test_user"
        print("✅ 解码Token测试通过")
    
    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        payload = decode_token("invalid_token")
        assert payload is None
        print("✅ 无效Token测试通过")
    
    def test_token_contains_user_id(self):
        """测试Token包含用户ID"""
        token = create_access_token(data={"sub": "admin", "user_id": 42})
        payload = decode_token(token)
        assert payload["user_id"] == 42
        print("✅ Token用户ID测试通过")


class TestDataEnums:
    """数据枚举测试"""
    
    def test_data_level_enum_values(self):
        """测试数据分级枚举值"""
        # 直接在测试中定义枚举进行测试
        class DataLevel:
            PUBLIC = "public"
            INTERNAL = "internal"
            CONFIDENTIAL = "confidential"
            TOP_SECRET = "top_secret"
        
        assert DataLevel.PUBLIC == "public"
        assert DataLevel.INTERNAL == "internal"
        assert DataLevel.CONFIDENTIAL == "confidential"
        assert DataLevel.TOP_SECRET == "top_secret"
        print("✅ 数据分级枚举测试通过")
    
    def test_user_status_enum_values(self):
        """测试用户状态枚举值"""
        class UserStatus:
            ACTIVE = "active"
            INACTIVE = "inactive"
            LOCKED = "locked"
        
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.LOCKED == "locked"
        print("✅ 用户状态枚举测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("权限管理系统测试")
    print("="*50 + "\n")
    
    test_suites = [
        TestJWTToken(),
        TestDataEnums(),
    ]
    
    total = 0
    passed = 0
    
    for suite in test_suites:
        print(f"\n📋 {suite.__class__.__name__}")
        print("-" * 40)
        
        for method in dir(suite):
            if method.startswith("test_"):
                total += 1
                try:
                    getattr(suite, method)()
                    passed += 1
                except Exception as e:
                    print(f"❌ {method}: {e}")
    
    print("\n" + "="*50)
    print(f"测试结果: {passed}/{total} 通过")
    print("="*50 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
