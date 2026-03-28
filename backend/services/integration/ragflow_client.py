"""
RAGFlow 集成服务
v0.8.1 (修复认证)
集成 RAGFlow 实现专业 RAG 问答
"""
import requests
import secrets
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RAGFlowConfig:
    """RAGFlow 配置"""
    base_url: str = "http://localhost:9380"
    api_token: str = ""  # API Token (Bearer token)
    timeout: int = 60


class RAGFlowService:
    """RAGFlow 服务 - 使用 API Token 认证"""

    def __init__(self, config: RAGFlowConfig = None):
        self.config = config or RAGFlowConfig()
        self.session = requests.Session()
        self._headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, **kwargs) -> Dict:
        """发送 API 请求"""
        url = f"{self.config.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._headers)
        
        response = self.session.request(
            method, url, headers=headers, timeout=self.config.timeout, **kwargs
        )
        return response.json()

    def get(self, path: str, **kwargs) -> Dict:
        """GET 请求"""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Dict:
        """POST 请求"""
        return self._request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Dict:
        """DELETE 请求"""
        return self._request("DELETE", path, **kwargs)

    def health_check(self) -> bool:
        """健康检查"""
        try:
            result = self.get("/v1/system/status")
            return result.get("code") == 0
        except:
            return False

    def list_datasets(self) -> List[Dict]:
        """列出数据集"""
        result = self.get("/api/v1/datasets")
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def create_dataset(self, name: str, description: str = "", 
                       chunk_method: str = "naive", 
                       permission: str = "me") -> Dict:
        """创建数据集"""
        result = self.post("/api/v1/datasets", json={
            "name": name,
            "description": description,
            "chunk_method": chunk_method,
            "permission": permission
        })
        return result

    def get_dataset(self, dataset_id: str) -> Dict:
        """获取数据集详情"""
        result = self.get(f"/api/v1/datasets/{dataset_id}")
        return result

    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集"""
        result = self.delete(f"/api/v1/datasets/{dataset_id}")
        return result.get("code") == 0

    def upload_document(self, dataset_id: str, file_path: str, chunk_method: str = "naive") -> Dict:
        """上传文档"""
        url = f"{self.config.base_url}/api/v1/datasets/{dataset_id}/documents"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'chunk_method': chunk_method}
            headers = {"Authorization": f"Bearer {self.config.api_token}"}
            response = self.session.post(url, files=files, data=data, headers=headers, timeout=self.config.timeout)
        
        return response.json()

    def list_documents(self, dataset_id: str) -> List[Dict]:
        """列出数据集中的文档"""
        result = self.get(f"/api/v1/datasets/{dataset_id}/documents")
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def delete_document(self, dataset_id: str, document_id: str) -> bool:
        """删除文档"""
        result = self.delete(f"/api/v1/datasets/{dataset_id}/documents/{document_id}")
        return result.get("code") == 0

    def retrievals(self, dataset_ids: List[str], query: str, top_k: int = 5) -> List[Dict]:
        """RAG 检索"""
        result = self.post("/api/v1/retrieval", json={
            "dataset_ids": dataset_ids,
            "question": query,
            "top_k": top_k
        })
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def chat(self, dataset_ids: List[str], query: str, top_k: int = 5) -> Dict:
        """RAG 对话"""
        result = self.post("/api/v1/chat", json={
            "dataset_ids": dataset_ids,
            "question": query,
            "top_k": top_k
        })
        return result


def create_api_token(tenant_id: str, token: str = None) -> str:
    """在数据库中创建 API Token"""
    import pymysql
    import os
    
    if token is None:
        token = secrets.token_hex(32)
    
    conn = pymysql.connect(
        host=os.environ.get('RAGFLOW_MYSQL_HOST', 'mysql'),
        user='root',
        password=os.environ.get('RAGFLOW_MYSQL_PASSWORD', 'infini_rag_flow'),
        database='rag_flow',
        port=3306
    )
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_token (tenant_id, token, source, create_time, update_time, create_date, update_date)
        VALUES (%s, %s, %s, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), NOW(), NOW())
    ''', (tenant_id, token, 'ai-knowledge-base'))
    conn.commit()
    conn.close()
    
    return token


# 便捷函数
_ragflow_service: Optional[RAGFlowService] = None


def get_ragflow_service(api_token: str = None) -> RAGFlowService:
    """获取 RAGFlow 服务实例"""
    global _ragflow_service
    
    if _ragflow_service is None or api_token:
        config = RAGFlowConfig(api_token=api_token)
        _ragflow_service = RAGFlowService(config)
    
    return _ragflow_service


def is_ragflow_available() -> bool:
    """检查 RAGFlow 是否可用"""
    try:
        service = get_ragflow_service()
        return service.health_check()
    except:
        return False
