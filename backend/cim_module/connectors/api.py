"""
API连接器 - 支持RESTful API接入
"""
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging
import urllib.request
import urllib.error

from .base import BaseConnector

logger = logging.getLogger(__name__)

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not installed, API connector will use synchronous requests")

class APIConnector(BaseConnector):
    """API连接器 - 支持RESTful API接入"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session: Optional[Any] = None
        self.base_url = config.get('base_url', '').rstrip('/')
        self.auth_type = config.get('auth_type', 'none')  # none, basic, bearer, apikey
        self.timeout = config.get('timeout', 30)
    
    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = self.config.get('headers', {}).copy()
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        
        # 根据认证类型添加认证信息
        if self.auth_type == 'basic':
            import base64
            credentials = f"{self.config.get('username')}:{self.config.get('password')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
        
        elif self.auth_type == 'bearer':
            token = self.config.get('token') or self.config.get('api_key')
            headers['Authorization'] = f'Bearer {token}'
        
        elif self.auth_type == 'apikey':
            api_key = self.config.get('api_key')
            key_header = self.config.get('api_key_header', 'X-API-Key')
            headers[key_header] = api_key
        
        return headers
    
    async def connect(self) -> bool:
        """创建HTTP会话"""
        try:
            if HAS_AIOHTTP:
                connector = aiohttp.TCPConnector(
                    limit=self.config.get('connection_limit', 100),
                    ttl_dns_cache=300
                )
                
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=self._get_headers()
                )
            
            self.is_connected = True
            logger.info(f"API会话创建成功: {self.base_url}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"创建API会话失败: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """关闭HTTP会话"""
        try:
            if HAS_AIOHTTP and self.session:
                await self.session.close()
                self.session = None
            self.is_connected = False
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"关闭API会话失败: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            # 使用健康检查端点或GET根路径
            test_endpoint = self.config.get('health_endpoint', '/health')
            url = f"{self.base_url}{test_endpoint}"
            
            if HAS_AIOHTTP and self.session:
                async with self.session.get(url) as response:
                    status = response.status
                    
                    if status == 200:
                        try:
                            data = await response.json()
                        except:
                            data = await response.text()
                        
                        return {
                            "success": True,
                            "status_code": status,
                            "response": data
                        }
                    else:
                        return {
                            "success": False,
                            "status_code": status,
                            "error": f"HTTP {status}"
                        }
            else:
                # 使用同步请求
                req = urllib.request.Request(url, headers=self._get_headers())
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    status = response.status
                    if status == 200:
                        return {"success": True, "status_code": status}
                    else:
                        return {"success": False, "status_code": status}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从API获取数据
        
        query格式:
        {
            "endpoint": "/api/workorders",  # API端点
            "method": "GET",                 # HTTP方法
            "params": {"status": "active"}, # URL参数
            "body": {...},                   # 请求体(POST/PUT)
            "headers": {...},                # 额外请求头
            "extract_path": "data.items"     # 提取数据的路径
        }
        """
        try:
            if not self.is_connected:
                await self.connect()
            
            endpoint = query.get('endpoint', '/')
            method = query.get('method', 'GET').upper()
            
            url = f"{self.base_url}{endpoint}"
            
            # 准备请求参数
            request_kwargs = {}
            
            if 'params' in query:
                request_kwargs['params'] = query['params']
            
            if 'headers' in query:
                headers = self._get_headers()
                headers.update(query['headers'])
                request_kwargs['headers'] = headers
            
            if 'body' in query and method in ['POST', 'PUT', 'PATCH']:
                request_kwargs['json'] = query['body']
            
            # 发送请求
            async with self.session.request(method, url, **request_kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"API错误 {response.status}: {error_text}")
                
                # 解析响应
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    data = await response.json()
                else:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                    except:
                        data = {"raw_text": text}
                
                # 根据提取路径提取数据
                extract_path = query.get('extract_path')
                if extract_path:
                    data = self._extract_by_path(data, extract_path)
                
                # 确保返回列表
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    return [{"value": data}]
                    
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise
    
    def _extract_by_path(self, data: Any, path: str) -> Any:
        """根据路径提取嵌套数据"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    async def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """GET请求"""
        return await self.fetch_data({
            "endpoint": endpoint,
            "method": "GET",
            "params": params,
            "headers": headers
        })
    
    async def post(self, endpoint: str, body: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """POST请求"""
        result = await self.fetch_data({
            "endpoint": endpoint,
            "method": "POST",
            "body": body,
            "headers": headers
        })
        return result[0] if result else {}
    
    async def put(self, endpoint: str, body: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT请求"""
        result = await self.fetch_data({
            "endpoint": endpoint,
            "method": "PUT",
            "body": body,
            "headers": headers
        })
        return result[0] if result else {}
    
    async def delete(self, endpoint: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """DELETE请求"""
        result = await self.fetch_data({
            "endpoint": endpoint,
            "method": "DELETE",
            "headers": headers
        })
        return result[0] if result else {}