"""
知识图谱构建服务
整合实体抽取和关系抽取，构建完整的知识图谱
"""
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from kg_module.models.entity import (
    Entity, Relation, EntityMention, EntityType, RelationType,
    ExtractedEntity, ExtractedRelation, ExtractionResult
)
from kg_module.models.graph_store import KnowledgeGraphStore, get_graph_store
from kg_module.services.entity_extraction import get_entity_extractor
from kg_module.services.relation_extraction import get_relation_extractor


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, store: Optional[KnowledgeGraphStore] = None):
        """
        初始化构建器
        
        Args:
            store: 知识图谱存储实例，默认使用全局实例
        """
        self.store = store or get_graph_store()
        self.entity_extractor = get_entity_extractor()
        self.relation_extractor = get_relation_extractor()
    
    def process_document(
        self,
        doc_id: str,
        text: str,
        title: str = "",
        min_entity_confidence: float = 0.5,
        min_relation_confidence: float = 0.3
    ) -> Dict:
        """
        处理单个文档，提取实体和关系并添加到图谱
        
        Args:
            doc_id: 文档ID
            text: 文档文本内容
            title: 文档标题
            min_entity_confidence: 实体最小置信度
            min_relation_confidence: 关系最小置信度
            
        Returns:
            处理结果统计
        """
        start_time = time.time()
        
        # 1. 抽取实体
        entity_result = self.entity_extractor.extract(
            text=text,
            doc_id=doc_id,
            min_confidence=min_entity_confidence
        )
        
        # 2. 抽取关系
        relations = self.relation_extractor.extract_relations(
            text=text,
            entities=entity_result.entities,
            doc_id=doc_id,
            min_confidence=min_relation_confidence
        )
        
        # 3. 将抽取结果添加到图谱
        added_entities = []
        added_relations = []
        
        # 添加文档实体
        doc_entity = Entity.create(
            name=title or f"文档_{doc_id}",
            entity_type=EntityType.DOCUMENT,
            description=f"文档ID: {doc_id}",
            source_doc_id=doc_id,
            properties={"doc_id": doc_id, "title": title}
        )
        doc_entity = self.store.add_entity(doc_entity)
        added_entities.append(doc_entity)
        
        # 添加提取的实体
        entity_id_map = {}  # 临时映射：extracted text -> entity id
        for extracted in entity_result.entities:
            entity = self._create_entity_from_extracted(extracted, doc_id)
            stored_entity = self.store.add_entity(entity)
            added_entities.append(stored_entity)
            entity_id_map[extracted.text] = stored_entity.id
            
            # 添加提及记录
            mention = EntityMention(
                entity_id=stored_entity.id,
                doc_id=doc_id,
                start_pos=extracted.start,
                end_pos=extracted.end,
                context=text[max(0, extracted.start-20):min(len(text), extracted.end+20)],
                confidence=extracted.confidence
            )
            self.store.add_mention(mention)
            
            # 添加文档-实体关系
            doc_relation = Relation.create(
                relation_type=RelationType.MENTIONS,
                source_id=doc_entity.id,
                target_id=stored_entity.id,
                source_doc_id=doc_id,
                properties={"mention_count": 1}
            )
            self.store.add_relation(doc_relation)
        
        # 添加关系
        for extracted_rel in relations:
            relation = self._create_relation_from_extracted(
                extracted_rel, entity_id_map, doc_id
            )
            if relation:
                stored_relation = self.store.add_relation(relation)
                added_relations.append(stored_relation)
        
        # 保存图谱
        self.store.save()
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "doc_id": doc_id,
            "extracted_entities": len(entity_result.entities),
            "extracted_relations": len(relations),
            "added_entities": len(added_entities),
            "added_relations": len(added_relations),
            "processing_time_ms": processing_time,
            "entity_types": self._count_entity_types(added_entities),
            "relation_types": self._count_relation_types(added_relations)
        }
    
    def _create_entity_from_extracted(
        self,
        extracted: ExtractedEntity,
        doc_id: str
    ) -> Entity:
        """从抽取结果创建实体"""
        return Entity.create(
            name=extracted.text,
            entity_type=extracted.type,
            description=extracted.properties.get("context", ""),
            source_doc_id=doc_id,
            confidence=extracted.confidence,
            properties=extracted.properties
        )
    
    def _create_relation_from_extracted(
        self,
        extracted: ExtractedRelation,
        entity_id_map: Dict[str, str],
        doc_id: str
    ) -> Optional[Relation]:
        """从抽取结果创建关系"""
        head_id = entity_id_map.get(extracted.head_text)
        tail_id = entity_id_map.get(extracted.tail_text)
        
        if not head_id or not tail_id:
            return None
        
        return Relation.create(
            relation_type=extracted.type,
            source_id=head_id,
            target_id=tail_id,
            source_doc_id=doc_id,
            confidence=extracted.confidence,
            properties=extracted.properties
        )
    
    def _count_entity_types(self, entities: List[Entity]) -> Dict[str, int]:
        """统计实体类型分布"""
        counts = {}
        for entity in entities:
            type_name = entity.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def _count_relation_types(self, relations: List[Relation]) -> Dict[str, int]:
        """统计关系类型分布"""
        counts = {}
        for relation in relations:
            type_name = relation.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def batch_process(
        self,
        documents: List[Tuple[str, str, str]],  # [(doc_id, text, title), ...]
        min_entity_confidence: float = 0.5,
        min_relation_confidence: float = 0.3
    ) -> List[Dict]:
        """
        批量处理文档
        
        Args:
            documents: 文档列表，每项为 (doc_id, text, title)
            min_entity_confidence: 实体最小置信度
            min_relation_confidence: 关系最小置信度
            
        Returns:
            各文档处理结果列表
        """
        results = []
        for doc_id, text, title in documents:
            result = self.process_document(
                doc_id=doc_id,
                text=text,
                title=title,
                min_entity_confidence=min_entity_confidence,
                min_relation_confidence=min_relation_confidence
            )
            results.append(result)
        return results
    
    def rebuild_document_graph(self, doc_id: str, documents_db) -> Dict:
        """
        从数据库重新构建文档的知识图谱
        
        Args:
            doc_id: 文档ID
            documents_db: 文档数据库会话
            
        Returns:
            处理结果
        """
        # 获取文档内容
        from models.database import Document
        doc = documents_db.query(Document).filter(Document.id == doc_id).first()
        
        if not doc:
            return {"error": "文档不存在", "doc_id": doc_id}
        
        # 删除旧的图谱数据
        self._remove_document_from_graph(doc_id)
        
        # 重新处理
        return self.process_document(
            doc_id=doc_id,
            text=doc.content,
            title=doc.title
        )
    
    def _remove_document_from_graph(self, doc_id: str):
        """从图谱中移除文档相关的所有数据"""
        # 获取文档实体
        doc_entities = self.store.get_document_entities(doc_id)
        
        # 删除这些实体（会级联删除关系）
        for entity in doc_entities:
            if entity.source_doc_id == doc_id:
                self.store.delete_entity(entity.id)
        
        self.store.save()
    
    def get_document_knowledge(self, doc_id: str) -> Dict:
        """
        获取文档的知识图谱表示
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档的知识图谱数据
        """
        entities = self.store.get_document_entities(doc_id)
        
        # 获取文档相关的所有关系
        relations = []
        for entity in entities:
            entity_relations = self.store.get_relations_by_entity(entity.id, "both")
            for rel, related_entity in entity_relations:
                if rel not in relations:
                    relations.append(rel)
        
        return {
            "doc_id": doc_id,
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations],
            "entity_count": len(entities),
            "relation_count": len(relations)
        }


# 全局构建器实例
_kg_builder = None

def get_kg_builder(store: Optional[KnowledgeGraphStore] = None) -> KnowledgeGraphBuilder:
    """获取全局知识图谱构建器实例"""
    global _kg_builder
    if _kg_builder is None:
        _kg_builder = KnowledgeGraphBuilder(store)
    return _kg_builder