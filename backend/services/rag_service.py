"""
增强版RAG服务 - 优化检索和上下文处理
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity

# 尝试导入sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    chunk_id: str
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    rank: int

@dataclass
class RAGContext:
    """RAG上下文数据结构"""
    query: str
    search_results: List[SearchResult]
    context_text: str
    total_chunks: int
    total_docs: int

class EnhancedVectorStore:
    """增强版向量存储服务"""
    
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.documents = {}  # doc_id -> {chunks: [], metadata: {}}
        self.chunks = {}     # chunk_id -> {doc_id, content, embedding, metadata}
        self.model = None
        self.model_name = model_name
        self._load_model()
        self._load_from_disk()
    
    def _load_model(self):
        """加载Embedding模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️ sentence_transformers未安装，使用简单向量化")
            self.model = None
            return
        
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Embedding模型加载成功: {self.model_name}")
        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}，使用降级方案")
            self.model = None
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本向量"""
        if self.model:
            return self.model.encode(text, convert_to_numpy=True)
        else:
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的词频向量（降级方案）"""
        vector = np.zeros(256)
        for char in text[:1000]:
            idx = ord(char) % 256
            vector[idx] += 1
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any], 
                     chunk_size: int = 500, chunk_overlap: int = 50):
        """添加文档到向量库（带智能分块）"""
        # 分段处理
        chunks = self._split_text(content, chunk_size, chunk_overlap)
        
        # 存储文档信息
        self.documents[doc_id] = {
            'metadata': metadata,
            'chunk_count': len(chunks),
            'content_length': len(content)
        }
        
        # 存储每个块
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            embedding = self._get_embedding(chunk_text)
            
            self.chunks[chunk_id] = {
                'doc_id': doc_id,
                'content': chunk_text,
                'embedding': embedding,
                'metadata': metadata,
                'chunk_index': i
            }
        
        self._save_to_disk()
        return len(chunks)
    
    def _split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """智能文本分块"""
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # 保留重叠
                    current_chunk = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                current_chunk += para + "\n\n"
            else:
                current_chunk += para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def search(self, query: str, top_k: int = 10, 
               filter_doc_ids: Optional[List[str]] = None) -> List[SearchResult]:
        """语义搜索（支持文档过滤）"""
        if not self.chunks:
            return []
        
        query_embedding = self._get_embedding(query)
        
        # 计算相似度
        results = []
        for chunk_id, chunk_data in self.chunks.items():
            # 过滤文档
            if filter_doc_ids and chunk_data['doc_id'] not in filter_doc_ids:
                continue
            
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                chunk_data['embedding'].reshape(1, -1)
            )[0][0]
            
            results.append(SearchResult(
                chunk_id=chunk_id,
                doc_id=chunk_data['doc_id'],
                content=chunk_data['content'],
                metadata=chunk_data['metadata'],
                score=float(similarity),
                rank=0  # 稍后设置
            ))
        
        # 排序并设置排名
        results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1
        
        return results[:top_k]
    
    def search_with_rerank(self, query: str, top_k: int = 10, 
                          rerank_top_n: int = 5) -> List[SearchResult]:
        """带重排序的搜索"""
        # 首先获取更多候选结果
        candidates = self.search(query, top_k=top_k * 2)
        
        if len(candidates) <= rerank_top_n:
            return candidates[:top_k]
        
        # 简单的重排序：根据关键词匹配度调整分数
        query_keywords = set(query.lower().split())
        
        for result in candidates:
            content_lower = result.content.lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower)
            # 结合语义相似度和关键词匹配
            result.score = result.score * 0.7 + (keyword_matches / len(query_keywords)) * 0.3
        
        # 重新排序
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(candidates[:top_k]):
            result.rank = i + 1
        
        return candidates[:top_k]
    
    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取指定文档的所有块"""
        return [
            {'chunk_id': k, **v}
            for k, v in self.chunks.items()
            if v['doc_id'] == doc_id
        ]
    
    def delete_document(self, doc_id: str):
        """删除文档"""
        chunk_ids = [k for k in self.chunks.keys() if self.chunks[k]['doc_id'] == doc_id]
        for chunk_id in chunk_ids:
            del self.chunks[chunk_id]
        
        if doc_id in self.documents:
            del self.documents[doc_id]
        
        self._save_to_disk()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            'total_documents': len(self.documents),
            'total_chunks': len(self.chunks),
            'model_loaded': self.model is not None,
            'model_name': self.model_name if self.model else 'simple_embedding'
        }
    
    def _save_to_disk(self):
        """保存到磁盘"""
        try:
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            
            save_data = {
                'documents': self.documents,
                'chunks': {
                    k: {**v, 'embedding': v['embedding'].tolist()}
                    for k, v in self.chunks.items()
                }
            }
            
            with open(f"{data_dir}/vector_store_enhanced.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存向量数据失败: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载"""
        try:
            data_file = "data/vector_store_enhanced.json"
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    load_data = json.load(f)
                
                self.documents = load_data.get('documents', {})
                for k, v in load_data.get('chunks', {}).items():
                    self.chunks[k] = {
                        'doc_id': v['doc_id'],
                        'content': v['content'],
                        'embedding': np.array(v['embedding']),
                        'metadata': v['metadata'],
                        'chunk_index': v['chunk_index']
                    }
                print(f"已加载 {len(self.documents)} 个文档，{len(self.chunks)} 个片段")
        except Exception as e:
            print(f"加载向量数据失败: {e}")


class EnhancedRAGService:
    """增强版RAG服务"""
    
    def __init__(self, vector_store: EnhancedVectorStore, ai_service=None):
        self.vector_store = vector_store
        self.ai_service = ai_service
    
    def retrieve(self, query: str, top_k: int = 5, 
                 use_rerank: bool = True) -> RAGContext:
        """检索相关文档"""
        if use_rerank:
            results = self.vector_store.search_with_rerank(query, top_k=top_k)
        else:
            results = self.vector_store.search(query, top_k=top_k)
        
        # 构建上下文文本
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"【文档{i+1}】{result.content}")
        
        context_text = "\n\n".join(context_parts)
        
        # 统计信息
        doc_ids = set(r.doc_id for r in results)
        
        return RAGContext(
            query=query,
            search_results=results,
            context_text=context_text,
            total_chunks=len(results),
            total_docs=len(doc_ids)
        )
    
    def generate_answer(self, query: str, context: RAGContext = None,
                       use_sources: bool = True) -> Dict[str, Any]:
        """生成回答"""
        if context is None:
            context = self.retrieve(query)
        
        # 构建提示词
        prompt = self._build_prompt(query, context)
        
        # 生成回答
        if self.ai_service:
            answer = self.ai_service.generate_answer(query, context.context_text)
        else:
            answer = self._simple_answer(query, context)
        
        result = {
            'query': query,
            'answer': answer,
            'sources': [
                {
                    'doc_id': r.doc_id,
                    'content': r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    'score': r.score,
                    'rank': r.rank,
                    'metadata': r.metadata
                }
                for r in context.search_results[:3]
            ] if use_sources else [],
            'context_stats': {
                'total_chunks': context.total_chunks,
                'total_docs': context.total_docs
            }
        }
        
        return result
    
    def _build_prompt(self, query: str, context: RAGContext) -> str:
        """构建提示词"""
        return f"""基于以下参考文档回答问题：

参考文档：
{context.context_text}

用户问题：{query}

请根据参考文档内容给出准确、简洁的回答。如果文档中没有相关信息，请明确说明。"""
    
    def _simple_answer(self, query: str, context: RAGContext) -> str:
        """简单回答生成（无AI服务时使用）"""
        if not context.search_results:
            return "抱歉，知识库中暂无相关信息。"
        
        # 提取最相关的片段
        top_contents = [r.content for r in context.search_results[:3]]
        
        answer = "根据知识库资料：\n\n"
        for i, content in enumerate(top_contents, 1):
            answer += f"{i}. {content[:300]}...\n\n" if len(content) > 300 else f"{i}. {content}\n\n"
        
        return answer
    
    def chat(self, query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """对话模式（支持历史上下文）"""
        # 检索相关文档
        context = self.retrieve(query)
        
        # 构建包含历史的提示词
        if chat_history:
            history_text = "\n".join([
                f"用户: {h.get('query', '')}\n助手: {h.get('answer', '')}"
                for h in chat_history[-3:]  # 只取最近3轮
            ])
            enhanced_query = f"对话历史：\n{history_text}\n\n当前问题：{query}"
        else:
            enhanced_query = query
        
        return self.generate_answer(enhanced_query, context)
