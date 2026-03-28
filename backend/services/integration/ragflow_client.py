"""
RAGFlow 集成服务
v0.8.0
集成 RAGFlow 实现专业 RAG 问答
RAGFlow: https://github.com/infiniflow/ragflow
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
import json
import time


class RAGFlowConfig:
    """RAGFlow 配置"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:9380",
        api_key: str = "",
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout


class DocumentStatus(Enum):
    """文档状态"""
    UPLOADING = "uploading"
    PARSING = "parsing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class RAGFlowDataset:
    """数据集"""
    id: str
    name: str
    description: str
    document_count: int
    created_at: str


@dataclass
class RAGFlowDocument:
    """文档"""
    id: str
    name: str
    dataset_id: str
    status: DocumentStatus
    size: int
    created_at: str


@dataclass
class RAGFlowChunk:
    """文档片段"""
    id: str
    document_id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class RAGFlowMessage:
    """对话消息"""
    id: str
    role: str  # "user" | "assistant"
    content: str
    citation: Optional[Dict] = None


class RAGFlowService:
    """
    RAGFlow 服务集成
    
    RAGFlow API 端点:
    - POST /api/v1/datasets - 创建数据集
    - GET /api/v1/datasets - 获取数据集列表
    - DELETE /api/v1/datasets/{id} - 删除数据集
    - POST /api/v1/datasets/{id}/documents - 上传文档
    - GET /api/v1/datasets/{id}/documents - 获取文档列表
    - DELETE /api/v1/datasets/{id}/documents/{doc_id} - 删除文档
    - POST /api/v1/retrieval - 检索
    - POST /api/v1/chat - 对话
    """

    def __init__(self, config: RAGFlowConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
        self._base_url = config.base_url

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送请求"""
        url = f"{self._base_url}{path}"
        
        try:
            if files:
                # 文件上传
                files_data = {"file": files}
                response = self.session.request(
                    method, url, data=data, files=files, timeout=self.config.timeout
                )
            else:
                response = self.session.request(
                    method, url, json=data, timeout=self.config.timeout
                )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"code": 500, "message": str(e)}

    # ========== 数据集管理 ==========

    def create_dataset(
        self,
        name: str,
        description: str = "",
        embedding_model: str = "BAAI/bge-large-zh-v1.5"
    ) -> RAGFlowDataset:
        """
        创建数据集
        
        Args:
            name: 数据集名称
            description: 数据集描述
            embedding_model: 嵌入模型
        
        Returns:
            RAGFlowDataset 对象
        """
        data = {
            "name": name,
            "description": description,
            "embedding_model": embedding_model
        }
        result = self._request("POST", "/api/v1/datasets", data)
        
        if result.get("code") == 0:
            d = result["data"]
            return RAGFlowDataset(
                id=d["id"],
                name=d["name"],
                description=d.get("description", ""),
                document_count=d.get("document_count", 0),
                created_at=d.get("create_date", "")
            )
        raise Exception(result.get("message", "创建数据集失败"))

    def list_datasets(self) -> List[RAGFlowDataset]:
        """获取数据集列表"""
        result = self._request("GET", "/api/v1/datasets")
        
        datasets = []
        if result.get("code") == 0:
            for d in result.get("data", []):
                datasets.append(RAGFlowDataset(
                    id=d["id"],
                    name=d["name"],
                    description=d.get("description", ""),
                    document_count=d.get("document_count", 0),
                    created_at=d.get("create_date", "")
                ))
        return datasets

    def get_dataset(self, dataset_id: str) -> RAGFlowDataset:
        """获取数据集详情"""
        result = self._request("GET", f"/api/v1/datasets/{dataset_id}")
        
        if result.get("code") == 0:
            d = result["data"]
            return RAGFlowDataset(
                id=d["id"],
                name=d["name"],
                description=d.get("description", ""),
                document_count=d.get("document_count", 0),
                created_at=d.get("create_date", "")
            )
        raise Exception(result.get("message", "获取数据集失败"))

    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集"""
        result = self._request("DELETE", f"/api/v1/datasets/{dataset_id}")
        return result.get("code") == 0

    # ========== 文档管理 ==========

    def upload_document(
        self,
        dataset_id: str,
        file_path: str,
        chunk_method: str = "naive"
    ) -> RAGFlowDocument:
        """
        上传文档到数据集
        
        Args:
            dataset_id: 数据集ID
            file_path: 文件路径
            chunk_method: 分块方法 (naive/parent_child/summary)
        
        Returns:
            RAGFlowDocument 对象
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            data = {"chunk_method": chunk_method}
            result = self._request(
                "POST",
                f"/api/v1/datasets/{dataset_id}/documents",
                data=data,
                files=files
            )
        
        if result.get("code") == 0:
            d = result["data"]
            return RAGFlowDocument(
                id=d["id"],
                name=d["name"],
                dataset_id=dataset_id,
                status=DocumentStatus(d.get("status", "uploading")),
                size=d.get("size", 0),
                created_at=d.get("create_date", "")
            )
        raise Exception(result.get("message", "上传文档失败"))

    def list_documents(self, dataset_id: str) -> List[RAGFlowDocument]:
        """获取数据集文档列表"""
        result = self._request("GET", f"/api/v1/datasets/{dataset_id}/documents")
        
        documents = []
        if result.get("code") == 0:
            for d in result.get("data", []):
                documents.append(RAGFlowDocument(
                    id=d["id"],
                    name=d["name"],
                    dataset_id=dataset_id,
                    status=DocumentStatus(d.get("status", "uploading")),
                    size=d.get("size", 0),
                    created_at=d.get("create_date", "")
                ))
        return documents

    def get_document(self, dataset_id: str, doc_id: str) -> RAGFlowDocument:
        """获取文档详情"""
        result = self._request(
            "GET",
            f"/api/v1/datasets/{dataset_id}/documents/{doc_id}"
        )
        
        if result.get("code") == 0:
            d = result["data"]
            return RAGFlowDocument(
                id=d["id"],
                name=d["name"],
                dataset_id=dataset_id,
                status=DocumentStatus(d.get("status", "uploading")),
                size=d.get("size", 0),
                created_at=d.get("create_date", "")
            )
        raise Exception(result.get("message", "获取文档失败"))

    def delete_document(self, dataset_id: str, doc_id: str) -> bool:
        """删除文档"""
        result = self._request(
            "DELETE",
            f"/api/v1/datasets/{dataset_id}/documents/{doc_id}"
        )
        return result.get("code") == 0

    def parse_document(self, dataset_id: str, doc_id: str) -> bool:
        """触发文档解析"""
        result = self._request(
            "POST",
            f"/api/v1/datasets/{dataset_id}/documents/{doc_id}/parse"
        )
        return result.get("code") == 0

    def wait_document_ready(
        self,
        dataset_id: str,
        doc_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> bool:
        """等待文档解析完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            doc = self.get_document(dataset_id, doc_id)
            if doc.status == DocumentStatus.DONE:
                return True
            if doc.status == DocumentStatus.FAILED:
                return False
            time.sleep(poll_interval)
        return False

    # ========== RAG 检索与问答 ==========

    def retrieval(
        self,
        dataset_ids: List[str],
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        RAG 检索
        
        Args:
            dataset_ids: 数据集ID列表
            query: 查询文本
            top_k: 返回数量
            similarity_threshold: 相似度阈值
        
        Returns:
            检索结果列表
        """
        data = {
            "dataset_ids": dataset_ids,
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
        result = self._request("POST", "/api/v1/retrieval", data)
        
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def chat(
        self,
        dataset_ids: List[str],
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.5,
        temperature: float = 0.1,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        RAG 对话问答
        
        Args:
            dataset_ids: 数据集ID列表
            query: 查询文本
            top_k: 检索数量
            similarity_threshold: 相似度阈值
            temperature: 生成温度
            stream: 是否流式返回
        
        Returns:
            {
                "answer": "回答内容",
                "references": [{"content": "...", "source": "...", "score": 0.9}],
                "conversation_id": "xxx"
            }
        """
        data = {
            "dataset_ids": dataset_ids,
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "temperature": temperature,
            "stream": stream
        }
        result = self._request("POST", "/api/v1/chat", data)
        
        if result.get("code") == 0:
            return result.get("data", {})
        return {"answer": "", "references": []}

    def direct_chat(
        self,
        knowledgebases: List[str],
        question: str,
        system_prompt: str = ""
    ) -> str:
        """
        直接对话（无需先创建数据集）
        
        Args:
            knowledgebases: 知识库ID列表
            question: 问题
            system Prompt: 系统提示
        
        Returns:
            回答内容
        """
        data = {
            "question": question,
            "knowledgebases": knowledgebases,
            "system_prompt": system_prompt
        }
        result = self._request("POST", "/api/v1/chat", data)
        
        if result.get("code") == 0:
            return result.get("answer", "")
        return ""

    # ========== 健康检查 ==========

    def health_check(self) -> bool:
        """检查 RAGFlow 服务健康状态"""
        try:
            result = self._request("GET", "/health")
            return result.get("code") == 0
        except:
            return False

    def get_version(self) -> str:
        """获取 RAGFlow 版本"""
        try:
            result = self._request("GET", "/api/v1/version")
            if result.get("code") == 0:
                return result.get("data", {}).get("version", "unknown")
        except:
            pass
        return "unknown"


# 单例
_ragflow_service: Optional[RAGFlowService] = None


def get_ragflow_service(
    base_url: str = None,
    api_key: str = None
) -> RAGFlowService:
    """获取 RAGFlow 服务实例"""
    global _ragflow_service
    
    if _ragflow_service is None:
        # 从配置加载
        from dotenv import load_dotenv
        load_dotenv()
        import os
        
        config = RAGFlowConfig(
            base_url=base_url or os.getenv("RAGFLOW_URL", "http://localhost:9380"),
            api_key=api_key or os.getenv("RAGFLOW_API_KEY", ""),
            timeout=int(os.getenv("RAGFLOW_TIMEOUT", "60"))
        )
        _ragflow_service = RAGFlowService(config)
    
    return _ragflow_service


def is_ragflow_available() -> bool:
    """检查 RAGFlow 是否可用"""
    try:
        service = get_ragflow_service()
        return service.health_check()
    except:
        return False
