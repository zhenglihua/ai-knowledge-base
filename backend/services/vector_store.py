import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity

# 尝试导入sentence_transformers，失败则使用降级方案
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence_transformers未安装，使用降级方案")

class VectorStore:
    """简化的向量存储服务 - 使用内存存储"""
    
    def __init__(self):
        self.documents = {}  # doc_id -> {content, embedding, metadata}
        self.model = None
        self._load_model()
        
        # 尝试加载已有数据
        self._load_from_disk()
    
    def _load_model(self):
        """加载Embedding模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️ sentence_transformers未安装，使用简单向量化")
            self.model = None
            return
        
        try:
            # 使用轻量级中文模型
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ Embedding模型加载成功")
        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}，使用降级方案")
            self.model = None
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本向量"""
        if self.model:
            return self.model.encode(text)
        else:
            # 降级方案：使用简单的词频向量
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的词频向量（降级方案）"""
        # 创建一个简单的基于字符的向量
        vector = np.zeros(256)
        for char in text[:1000]:  # 限制长度
            idx = ord(char) % 256
            vector[idx] += 1
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """添加文档到向量库"""
        # 分段存储（每段500字）
        chunk_size = 500
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            embedding = self._get_embedding(chunk)
            self.documents[chunk_id] = {
                "doc_id": doc_id,
                "content": chunk,
                "embedding": embedding,
                "metadata": metadata,
                "chunk_index": i
            }
        
        # 保存到磁盘
        self._save_to_disk()
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """语义搜索"""
        if not self.documents:
            return []
        
        # 获取查询向量
        query_embedding = self._get_embedding(query)
        
        # 计算相似度
        results = []
        for chunk_id, doc in self.documents.items():
            doc_embedding = doc["embedding"]
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                doc_embedding.reshape(1, -1)
            )[0][0]
            
            results.append({
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": float(similarity)
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def delete_document(self, doc_id: str):
        """删除文档的所有分段"""
        chunk_ids = [k for k in self.documents.keys() if k.startswith(f"{doc_id}_chunk_")]
        for chunk_id in chunk_ids:
            del self.documents[chunk_id]
        self._save_to_disk()
    
    def _save_to_disk(self):
        """保存到磁盘"""
        try:
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            
            # 保存为JSON（embedding转为列表）
            save_data = {}
            for k, v in self.documents.items():
                save_data[k] = {
                    "doc_id": v["doc_id"],
                    "content": v["content"],
                    "embedding": v["embedding"].tolist(),
                    "metadata": v["metadata"],
                    "chunk_index": v["chunk_index"]
                }
            
            with open(f"{data_dir}/vector_store.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存向量数据失败: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载"""
        try:
            data_file = "data/vector_store.json"
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    load_data = json.load(f)
                
                for k, v in load_data.items():
                    self.documents[k] = {
                        "doc_id": v["doc_id"],
                        "content": v["content"],
                        "embedding": np.array(v["embedding"]),
                        "metadata": v["metadata"],
                        "chunk_index": v["chunk_index"]
                    }
                print(f"已加载 {len(self.documents)} 个文档片段")
        except Exception as e:
            print(f"加载向量数据失败: {e}")
