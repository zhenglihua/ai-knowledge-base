"""
CIM数据连接器基类
支持数据库直连和API接入
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

class BaseConnector(ABC):
    """数据连接器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
        self.last_error = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass
    
    @abstractmethod
    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取数据"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取连接器状态"""
        return {
            "is_connected": self.is_connected,
            "last_error": self.last_error,
            "config": {k: v for k, v in self.config.items() if k not in ['password', 'secret']}
        }