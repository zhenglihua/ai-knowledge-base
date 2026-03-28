"""
多文档联合推理 RAG 服务
v0.3.0
支持跨多个文档综合问答和引用追踪
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

from models.database import get_db_session, Document
from services.vector_store import VectorStore
from services.document_parser import DocumentParser


@dataclass
class DocChunk:
    """文档片段"""
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class RetrievedChunk:
    """检索结果"""
    chunk: DocChunk
    score: float
    rank: int


@dataclass
class Citation:
    """引用信息"""
    document_id: str
    document_title: str
    chunk_id: str
    content: str
    start_char: int
    end_char: int


class MultiDocRAGService:
    """多文档联合推理服务"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.parser = DocumentParser()
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def query_across_documents(
        self,
        question: str,
        document_ids: List[str],
        top_k: int = 10,
        include_aggregated_answer: bool = True
    ) -> Dict[str, Any]:
        """
        跨多个文档查询

        Args:
            question: 用户问题
            document_ids: 要查询的文档ID列表
            top_k: 每个文档返回的top结果数
            include_aggregated_answer: 是否包含聚合答案

        Returns:
            包含答案、引用和来源的字典
        """
        # 1. 检索相关片段
        retrieved_chunks = await self._retrieve_chunks(
            question, document_ids, top_k
        )

        # 2. 构建上下文
        context = self._build_context(retrieved_chunks)

        # 3. 生成答案（这里调用LLM服务）
        answer = await self._generate_answer(question, context)

        # 4. 构建引用
        citations = self._extract_citations(retrieved_chunks)

        return {
            "answer": answer,
            "question": question,
            "chunks": retrieved_chunks,
            "citations": citations,
            "num_documents": len(document_ids),
            "num_chunks": len(retrieved_chunks)
        }

    async def _retrieve_chunks(
        self,
        question: str,
        document_ids: List[str],
        top_k: int
    ) -> List[RetrievedChunk]:
        """从多个文档中检索相关片段"""
        all_chunks = []

        # 并行检索多个文档
        tasks = [
            self._retrieve_from_document(question, doc_id, top_k)
            for doc_id in document_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for doc_chunks in results:
            if isinstance(doc_chunks, list):
                all_chunks.extend(doc_chunks)

        # 按分数排序
        all_chunks.sort(key=lambda x: x.score, reverse=True)

        # 重新编号
        for i, chunk in enumerate(all_chunks):
            chunk.rank = i + 1

        return all_chunks[:top_k * 2]

    async def _retrieve_from_document(
        self,
        question: str,
        document_id: str,
        top_k: int
    ) -> List[RetrievedChunk]:
        """从单个文档检索"""
        db = get_db_session()
        try:
            # 获取文档元数据
            doc = db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not doc:
                return []

            # 向量检索
            query_embedding = await self.vector_store.embed_text(question)
            results = await self.vector_store.search(
                query_embedding,
                filter_dict={"document_id": document_id},
                top_k=top_k
            )

            chunks = []
            for i, result in enumerate(results):
                chunk = DocChunk(
                    chunk_id=result.get("id", f"{document_id}_{i}"),
                    document_id=document_id,
                    document_title=doc.title,
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    embedding=result.get("embedding")
                )
                chunks.append(RetrievedChunk(
                    chunk=chunk,
                    score=result.get("score", 0.0),
                    rank=0
                ))

            return chunks
        finally:
            db.close()

    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        """构建上下文文本"""
        context_parts = []
        for retrieved in chunks:
            chunk = retrieved.chunk
            context_parts.append(
                f"[来源: {chunk.document_title}]\n{chunk.content}\n"
            )
        return "\n---\n".join(context_parts)

    async def _generate_answer(
        self,
        question: str,
        context: str
    ) -> str:
        """
        基于上下文生成答案
        TODO: 接入真实 LLM
        """
        # 模拟 LLM 响应
        return (
            f"基于提供的文档内容，关于「{question}」的回答如下：\n\n"
            f"{context[:500]}...\n\n"
            f"(此处将调用 LLM 生成更精确的答案)"
        )

    def _extract_citations(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[Citation]:
        """提取引用信息"""
        citations = []
        for retrieved in chunks:
            chunk = retrieved.chunk
            citations.append(Citation(
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                chunk_id=chunk.chunk_id,
                content=chunk.content[:200],
                start_char=0,
                end_char=min(200, len(chunk.content))
            ))
        return citations

    async def compare_documents(
        self,
        document_ids: List[str],
        comparison_dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        对比分析多个文档

        Args:
            document_ids: 要对比的文档ID列表（2-4个）
            comparison_dimensions: 对比维度

        Returns:
            对比分析结果
        """
        if len(document_ids) < 2:
            raise ValueError("至少需要2个文档进行对比")
        if len(document_ids) > 4:
            raise ValueError("最多支持4个文档对比")

        db = get_db_session()
        try:
            # 获取文档信息
            docs = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()

            # 提取关键信息进行对比
            comparison_data = {
                "documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "file_type": doc.file_type,
                        "category": doc.category,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                    for doc in docs
                ],
                "dimensions": comparison_dimensions or ["内容摘要", "关键参数", "适用场景"],
                "comparison_results": {}
            }

            return comparison_data
        finally:
            db.close()


# 单例
multi_doc_rag_service = MultiDocRAGService()
