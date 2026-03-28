"""
混合检索引擎
v0.3.0
结合向量检索和关键词检索，使用 Reranking 优化排序
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

from services.vector_store import VectorStore


@dataclass
class SearchResult:
    """检索结果"""
    chunk_id: str
    document_id: str
    content: str
    score: float
    vector_score: float = 0.0
    keyword_score: float = 0.0
    metadata: Dict[str, Any] = None


class HybridRetrievalService:
    """混合检索服务 - 向量 + BM25 + Reranking"""

    def __init__(self, vector_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        初始化混合检索服务

        Args:
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        """
        self.vector_store = VectorStore()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

        # BM25 参数
        self.k1 = 1.5  # 词频饱和度
        self.b = 0.75  # 文档长度归一化

    async def search(
        self,
        query: str,
        top_k: int = 20,
        rerank: bool = True,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        混合检索入口

        Args:
            query: 查询文本
            top_k: 返回结果数
            rerank: 是否使用 Reranking
            filter_dict: 过滤条件

        Returns:
            排序后的检索结果
        """
        # 1. 向量检索
        vector_results = await self._vector_search(query, top_k * 2, filter_dict)

        # 2. BM25 关键词检索
        keyword_results = await self._bm25_search(query, top_k * 2, filter_dict)

        # 3. 分数融合
        fused_results = self._fuse_scores(vector_results, keyword_results)

        # 4. Reranking（如果启用）
        if rerank:
            fused_results = await self._rerank(query, fused_results, top_k)
        else:
            fused_results = fused_results[:top_k]

        # 5. 更新 rank
        for i, result in enumerate(fused_results):
            result.score = fused_results[i].score if i < len(fused_results) else 0.0

        return fused_results[:top_k]

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, SearchResult]:
        """向量检索"""
        query_embedding = await self.vector_store.embed_text(query)

        results = await self.vector_store.search(
            query_embedding,
            filter_dict=filter_dict,
            top_k=top_k
        )

        vector_results = {}
        for i, result in enumerate(results):
            chunk_id = result.get("id", f"chunk_{i}")
            score = result.get("score", 0.0)

            # 将余弦相似度转换为 0-1 分数
            normalized_score = (score + 1) / 2

            vector_results[chunk_id] = SearchResult(
                chunk_id=chunk_id,
                document_id=result.get("metadata", {}).get("document_id", ""),
                content=result.get("content", ""),
                score=normalized_score,
                vector_score=normalized_score,
                keyword_score=0.0,
                metadata=result.get("metadata", {})
            )

        return vector_results

    async def _bm25_search(
        self,
        query: str,
        top_k: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, SearchResult]:
        """
        BM25 关键词检索

        注意：这里使用简化的 BM25 实现
        实际生产环境建议使用 Elasticsearch 或 Whoosh
        """
        # 分词
        query_terms = self._tokenize(query)

        if not query_terms:
            return {}

        # 从向量存储获取所有文档片段（简化实现）
        # 实际应该用专门的全文索引
        results = await self.vector_store.get_all_chunks(filter_dict)

        bm25_scores = {}
        doc_lengths = {}
        avg_doc_length = 0

        # 计算文档长度
        for result in results:
            chunk_id = result.get("id", "")
            content = result.get("content", "")
            doc_length = len(content)
            doc_lengths[chunk_id] = doc_length
            avg_doc_length += doc_length

        if results:
            avg_doc_length /= len(results)

        # 计算 BM25 分数
        for result in results:
            chunk_id = result.get("id", "")
            content = result.get("content", "")
            doc_length = doc_lengths.get(chunk_id, 0)
            content_terms = self._tokenize(content)

            # 统计词频
            term_freq = {}
            for term in query_terms:
                term_freq[term] = content_terms.count(term)

            # 计算 BM25
            score = 0.0
            for term in query_terms:
                tf = term_freq.get(term, 0)
                if tf > 0:
                    # 简化的 IDF（实际应该用 log(N/n)）
                    idf = 1.0
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
                    score += idf * numerator / denominator

            if score > 0:
                # 归一化到 0-1
                normalized_score = min(1.0, score / 10.0)
                bm25_scores[chunk_id] = SearchResult(
                    chunk_id=chunk_id,
                    document_id=result.get("metadata", {}).get("document_id", ""),
                    content=result.get("content", ""),
                    score=normalized_score,
                    vector_score=0.0,
                    keyword_score=normalized_score,
                    metadata=result.get("metadata", {})
                )

        return bm25_scores

    def _fuse_scores(
        self,
        vector_results: Dict[str, SearchResult],
        keyword_results: Dict[str, SearchResult]
    ) -> List[SearchResult]:
        """融合向量和关键词分数"""
        all_chunk_ids = set(vector_results.keys()) | set(keyword_results.keys())
        fused_results = []

        for chunk_id in all_chunk_ids:
            vector_result = vector_results.get(chunk_id)
            keyword_result = keyword_results.get(chunk_id)

            vector_score = vector_result.score if vector_result else 0.0
            keyword_score = keyword_result.score if keyword_result else 0.0

            # 加权融合
            fused_score = (
                vector_score * self.vector_weight +
                keyword_score * self.keyword_weight
            )

            # 使用向量结果作为基础
            if vector_result:
                result = SearchResult(
                    chunk_id=chunk_id,
                    document_id=vector_result.document_id,
                    content=vector_result.content,
                    score=fused_score,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    metadata=vector_result.metadata
                )
            else:
                result = SearchResult(
                    chunk_id=chunk_id,
                    document_id=keyword_result.document_id,
                    content=keyword_result.content,
                    score=fused_score,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                    metadata=keyword_result.metadata
                )

            fused_results.append(result)

        # 按融合分数排序
        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results

    async def _rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        使用 Cross-Encoder 进行 Reranking

        TODO: 接入真实的 Cross-Encoder 模型
        目前使用简化的相关性计算
        """
        query_terms = set(self._tokenize(query))

        reranked_results = []
        for result in results:
            content_terms = set(self._tokenize(result.content))

            # 计算词重叠率
            overlap = len(query_terms & content_terms)
            total = len(query_terms | content_terms)
            overlap_score = overlap / total if total > 0 else 0

            # 结合原始分数和相关性分数
            rerank_score = result.score * 0.7 + overlap_score * 0.3
            result.score = rerank_score
            reranked_results.append(result)

        reranked_results.sort(key=lambda x: x.score, reverse=True)
        return reranked_results[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        import re
        # 简单的中英文分词
        text = text.lower()
        # 按非字母数字分割
        tokens = re.split(r'[^a-z0-9\u4e00-\u9fff]+', text)
        return [t for t in tokens if t]


class Reranker:
    """
    Reranking 器
    使用 Cross-Encoder 思想优化排序
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None  # 延迟加载

    def load_model(self):
        """加载模型"""
        # TODO: 接入真实的 Cross-Encoder 模型
        # 示例: from sentence_transformers import CrossEncoder
        # self.model = CrossEncoder(self.model_name)
        pass

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Rerank 检索结果

        Args:
            query: 查询文本
            results: 初始检索结果
            top_k: 返回数量

        Returns:
            Reranked 结果
        """
        if not results:
            return []

        # 如果模型未加载，使用简化版本
        if self.model is None:
            return await self._simple_rerank(query, results, top_k)

        # 使用真实模型
        pairs = [(query, r.content) for r in results]
        scores = self.model.predict(pairs)

        for i, result in enumerate(results):
            result.score = float(scores[i])

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    async def _simple_rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """简化版 Rerank"""
        query_terms = set(self._tokenize(query))

        for result in results:
            content_terms = set(self._tokenize(result.content))
            overlap = len(query_terms & content_terms)
            total = len(query_terms | content_terms)
            result.score = result.score * 0.6 + (overlap / total if total > 0 else 0) * 0.4

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        import re
        text = text.lower()
        tokens = re.split(r'[^a-z0-9\u4e00-\u9fff]+', text)
        return [t for t in tokens if t]


# 单例
hybrid_retrieval_service = HybridRetrievalService()
reranker = Reranker()
