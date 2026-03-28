"""
第三方系统集成模块
v0.8.0
"""
from .ragflow_client import (
    RAGFlowService,
    RAGFlowConfig,
    RAGFlowDataset,
    RAGFlowDocument,
    RAGFlowChunk,
    RAGFlowMessage,
    DocumentStatus,
    get_ragflow_service,
    is_ragflow_available
)

__all__ = [
    "RAGFlowService",
    "RAGFlowConfig", 
    "RAGFlowDataset",
    "RAGFlowDocument",
    "RAGFlowChunk",
    "RAGFlowMessage",
    "DocumentStatus",
    "get_ragflow_service",
    "is_ragflow_available"
]
