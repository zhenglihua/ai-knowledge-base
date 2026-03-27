"""
基于知识图谱的智能推荐服务
提供文档推荐、实体推荐等功能
"""
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import random

from kg_module.models.entity import Entity, EntityType, RelationType
from kg_module.models.graph_store import KnowledgeGraphStore, get_graph_store


class KnowledgeGraphRecommender:
    """知识图谱推荐器"""
    
    def __init__(self, store: Optional[KnowledgeGraphStore] = None):
        """
        初始化推荐器
        
        Args:
            store: 知识图谱存储实例
        """
        self.store = store or get_graph_store()
    
    def recommend_documents(
        self,
        query_doc_id: str,
        limit: int = 5,
        method: str = "hybrid"  # "content", "collaborative", "hybrid"
    ) -> List[Dict]:
        """
        推荐相关文档
        
        Args:
            query_doc_id: 查询文档ID
            limit: 返回结果数量
            method: 推荐方法
            
        Returns:
            推荐的文档列表及相似度分数
        """
        if method == "content":
            return self._content_based_recommend(query_doc_id, limit)
        elif method == "collaborative":
            return self._collaborative_recommend(query_doc_id, limit)
        else:
            return self._hybrid_recommend(query_doc_id, limit)
    
    def _content_based_recommend(
        self,
        query_doc_id: str,
        limit: int
    ) -> List[Dict]:
        """基于内容的推荐"""
        # 获取查询文档的实体
        query_entities = self.store.get_document_entities(query_doc_id)
        query_entity_ids = {e.id for e in query_entities}
        
        # 计算与其他文档的相似度
        doc_scores = defaultdict(float)
        doc_common_entities = defaultdict(set)
        
        # 遍历所有实体，找到提及这些实体的其他文档
        for entity in query_entities:
            mentions = self.store.get_entity_mentions(entity.id)
            for mention in mentions:
                if mention.doc_id != query_doc_id:
                    # 计算权重（实体类型权重）
                    weight = self._get_entity_weight(entity.type)
                    doc_scores[mention.doc_id] += weight * entity.confidence
                    doc_common_entities[mention.doc_id].add(entity.id)
        
        # 归一化分数（Jaccard相似度）
        results = []
        for doc_id, score in doc_scores.items():
            common_count = len(doc_common_entities[doc_id])
            union_count = len(query_entity_ids) + len(
                {e.id for e in self.store.get_document_entities(doc_id)}
            ) - common_count
            
            if union_count > 0:
                jaccard = common_count / union_count
                normalized_score = score * (0.5 + 0.5 * jaccard)
            else:
                normalized_score = score
            
            results.append({
                "doc_id": doc_id,
                "score": round(normalized_score, 3),
                "common_entities": list(doc_common_entities[doc_id]),
                "method": "content_based"
            })
        
        # 排序并返回
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _collaborative_recommend(
        self,
        query_doc_id: str,
        limit: int
    ) -> List[Dict]:
        """协同过滤推荐（基于实体共现）"""
        # 获取查询文档的实体
        query_entities = self.store.get_document_entities(query_doc_id)
        query_entity_ids = {e.id for e in query_entities}
        
        # 查找与查询文档有共同实体的文档
        doc_cooccurrence = defaultdict(int)
        doc_weights = defaultdict(float)
        
        for entity in query_entities:
            mentions = self.store.get_entity_mentions(entity.id)
            for mention in mentions:
                if mention.doc_id != query_doc_id:
                    doc_cooccurrence[mention.doc_id] += 1
                    doc_weights[mention.doc_id] += entity.confidence
        
        # 计算相似度
        results = []
        for doc_id in doc_cooccurrence:
            # 使用共同实体数量和置信度加权
            score = doc_weights[doc_id] * (1 + doc_cooccurrence[doc_id] / 10)
            
            results.append({
                "doc_id": doc_id,
                "score": round(score, 3),
                "common_count": doc_cooccurrence[doc_id],
                "method": "collaborative"
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _hybrid_recommend(
        self,
        query_doc_id: str,
        limit: int
    ) -> List[Dict]:
        """混合推荐（内容 + 协同）"""
        content_results = self._content_based_recommend(query_doc_id, limit * 2)
        collaborative_results = self._collaborative_recommend(query_doc_id, limit * 2)
        
        # 合并结果
        combined_scores = defaultdict(lambda: {"score": 0, "methods": []})
        
        for result in content_results:
            doc_id = result["doc_id"]
            combined_scores[doc_id]["score"] += result["score"] * 0.6
            combined_scores[doc_id]["methods"].append("content")
        
        for result in collaborative_results:
            doc_id = result["doc_id"]
            combined_scores[doc_id]["score"] += result["score"] * 0.4
            combined_scores[doc_id]["methods"].append("collaborative")
        
        # 构建结果
        results = []
        for doc_id, data in combined_scores.items():
            results.append({
                "doc_id": doc_id,
                "score": round(data["score"], 3),
                "methods": data["methods"],
                "method": "hybrid"
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def recommend_by_entity(
        self,
        entity_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        基于实体的文档推荐
        
        Args:
            entity_id: 实体ID
            limit: 返回结果数量
            
        Returns:
            相关文档列表
        """
        entity = self.store.get_entity(entity_id)
        if not entity:
            return []
        
        # 获取提及该实体的所有文档
        mentions = self.store.get_entity_mentions(entity_id)
        doc_scores = defaultdict(float)
        
        for mention in mentions:
            doc_scores[mention.doc_id] += mention.confidence
        
        # 同时考虑相关实体
        related_entities = self._get_related_entities(entity_id)
        for related_id, relation_strength in related_entities:
            mentions = self.store.get_entity_mentions(related_id)
            for mention in mentions:
                doc_scores[mention.doc_id] += mention.confidence * relation_strength * 0.5
        
        results = [
            {
                "doc_id": doc_id,
                "score": round(score, 3),
                "method": "entity_based",
                "seed_entity": entity.name
            }
            for doc_id, score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return results[:limit]
    
    def recommend_entities(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        推荐相关实体
        
        Args:
            entity_id: 种子实体ID
            relation_type: 可选的关系类型过滤
            limit: 返回结果数量
            
        Returns:
            相关实体列表
        """
        entity = self.store.get_entity(entity_id)
        if not entity:
            return []
        
        # 获取邻居节点
        neighbors = self.store.get_neighbors(entity_id, relation_type, depth=2)
        
        # 计算相关度分数
        entity_scores = defaultdict(float)
        for neighbor in neighbors:
            neighbor_entity = neighbor["entity"]
            relation = neighbor["relation"]
            depth = neighbor["depth"]
            
            # 距离越近分数越高
            distance_weight = 1.0 / depth
            # 关系置信度
            confidence_weight = relation["confidence"]
            # 实体本身置信度
            entity_weight = neighbor_entity["confidence"]
            
            score = distance_weight * confidence_weight * entity_weight
            entity_scores[neighbor_entity["id"]] = score
        
        # 构建结果
        results = []
        for neighbor_id, score in sorted(entity_scores.items(), key=lambda x: x[1], reverse=True):
            neighbor_entity = self.store.get_entity(neighbor_id)
            if neighbor_entity:
                results.append({
                    "entity": neighbor_entity.to_dict(),
                    "score": round(score, 3),
                    "method": "graph_neighbors"
                })
        
        return results[:limit]
    
    def recommend_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        基于关键词的文档推荐
        
        Args:
            keywords: 关键词列表
            limit: 返回结果数量
            
        Returns:
            相关文档列表
        """
        # 搜索匹配关键词的实体
        matched_entities = []
        for keyword in keywords:
            entities = self.store.search_entities(keyword, limit=5)
            matched_entities.extend(entities)
        
        # 根据匹配实体推荐文档
        doc_scores = defaultdict(float)
        entity_matches = defaultdict(list)
        
        for entity in matched_entities:
            mentions = self.store.get_entity_mentions(entity.id)
            for mention in mentions:
                weight = entity.confidence * mention.confidence
                doc_scores[mention.doc_id] += weight
                entity_matches[mention.doc_id].append({
                    "entity_id": entity.id,
                    "entity_name": entity.name,
                    "type": entity.type.value
                })
        
        results = []
        for doc_id, score in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True):
            results.append({
                "doc_id": doc_id,
                "score": round(score, 3),
                "matched_entities": entity_matches[doc_id],
                "method": "keyword_based"
            })
        
        return results[:limit]
    
    def get_trending_entities(
        self,
        entity_type: Optional[EntityType] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取热门实体（被最多文档提及）
        
        Args:
            entity_type: 可选的实体类型过滤
            limit: 返回结果数量
            
        Returns:
            热门实体列表
        """
        # 统计每个实体被提及的文档数
        entity_doc_counts = defaultdict(set)
        
        for entity in self.store.entities.values():
            if entity_type and entity.type != entity_type:
                continue
            
            mentions = self.store.get_entity_mentions(entity.id)
            for mention in mentions:
                entity_doc_counts[entity.id].add(mention.doc_id)
        
        # 排序
        results = []
        for entity_id, doc_ids in sorted(
            entity_doc_counts.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ):
            entity = self.store.get_entity(entity_id)
            if entity:
                results.append({
                    "entity": entity.to_dict(),
                    "mention_count": len(doc_ids),
                    "doc_count": len(doc_ids),
                    "method": "trending"
                })
        
        return results[:limit]
    
    def _get_entity_weight(self, entity_type: EntityType) -> float:
        """获取实体类型权重"""
        weights = {
            EntityType.EQUIPMENT: 1.5,
            EntityType.PROCESS: 1.4,
            EntityType.MATERIAL: 1.3,
            EntityType.PARAMETER: 1.0,
            EntityType.QUALITY: 1.2,
            EntityType.PRODUCT: 1.1,
            EntityType.DEPARTMENT: 0.8,
            EntityType.PERSON: 0.7,
            EntityType.DOCUMENT: 0.5,
            EntityType.LOCATION: 0.6,
            EntityType.OTHER: 0.5
        }
        return weights.get(entity_type, 1.0)
    
    def _get_related_entities(
        self,
        entity_id: str,
        depth: int = 1
    ) -> List[Tuple[str, float]]:
        """获取相关实体及其关联强度"""
        related = []
        visited = {entity_id}
        current_level = [(entity_id, 1.0)]
        
        for d in range(depth):
            next_level = []
            for current_id, strength in current_level:
                neighbors = self.store.get_neighbors(current_id, depth=1)
                for neighbor in neighbors:
                    neighbor_id = neighbor["entity"]["id"]
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        new_strength = strength * 0.5 * neighbor["relation"]["confidence"]
                        next_level.append((neighbor_id, new_strength))
                        related.append((neighbor_id, new_strength))
            current_level = next_level
        
        return related


# 全局推荐器实例
_recommender = None

def get_recommender(store: Optional[KnowledgeGraphStore] = None) -> KnowledgeGraphRecommender:
    """获取全局推荐器实例"""
    global _recommender
    if _recommender is None:
        _recommender = KnowledgeGraphRecommender(store)
    return _recommender