"""
关系抽取服务
识别实体间的关系（使用、影响、属于等）
"""
import re
import time
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass

from kg_module.models.entity import (
    EntityType, RelationType, ExtractedEntity, ExtractedRelation, ExtractionResult
)


@dataclass
class RelationPattern:
    """关系抽取模式"""
    patterns: List[str]                      # 正则表达式列表
    relation_type: RelationType              # 关系类型
    priority: int = 1                        # 优先级
    direction: str = "forward"               # 方向: forward (A->B) 或 reverse (B->A)


class RelationExtractor:
    """关系抽取器 - 基于规则的方法"""
    
    # 关系模式定义
    RELATION_PATTERNS = {
        # 设备使用材料
        RelationType.USES: RelationPattern(
            patterns=[
                r'(\w+)\s*使用\s*(\w+)',
                r'(\w+)\s*uses?\s*(\w+)',
                r'(\w+)\s*采用\s*(\w+)',
                r'使用\s*(\w+)\s*的\s*(\w+)',
            ],
            relation_type=RelationType.USES,
            priority=1
        ),
        
        # 设备包含部件
        RelationType.HAS_PART: RelationPattern(
            patterns=[
                r'(\w+)\s*的\s*(\w+)',
                r'(\w+)\s*包括\s*(\w+)',
                r'(\w+)\s*包含\s*(\w+)',
                r'(\w+)\s*has\s*(\w+)',
                r'(\w+)\s*includes?\s*(\w+)',
            ],
            relation_type=RelationType.HAS_PART,
            priority=2
        ),
        
        # 需要/依赖关系
        RelationType.REQUIRES: RelationPattern(
            patterns=[
                r'(\w+)\s*需要\s*(\w+)',
                r'(\w+)\s*requires?\s*(\w+)',
                r'(\w+)\s*依赖\s*(\w+)',
                r'(\w+)\s*depends?\s*on\s*(\w+)',
                r'(\w+)\s*requires?\s*(\w+)',
            ],
            relation_type=RelationType.REQUIRES,
            priority=1
        ),
        
        # 产生/生成关系
        RelationType.PRODUCES: RelationPattern(
            patterns=[
                r'(\w+)\s*产生\s*(\w+)',
                r'(\w+)\s*生成\s*(\w+)',
                r'(\w+)\s*produces?\s*(\w+)',
                r'(\w+)\s*generates?\s*(\w+)',
            ],
            relation_type=RelationType.PRODUCES,
            priority=1
        ),
        
        # 影响关系
        RelationType.INFLUENCES: RelationPattern(
            patterns=[
                r'(\w+)\s*影响\s*(\w+)',
                r'(\w+)\s*affects?\s*(\w+)',
                r'(\w+)\s*influences?\s*(\w+)',
                r'(\w+)\s*决定\s*(\w+)',
                r'(\w+)\s*determines?\s*(\w+)',
            ],
            relation_type=RelationType.INFLUENCES,
            priority=1
        ),
        
        # 工艺步骤关系
        RelationType.STEP_OF: RelationPattern(
            patterns=[
                r'(\w+)\s*是\s*(\w+)\s*的?步骤',
                r'(\w+)\s*step\s*of\s*(\w+)',
                r'(\w+)\s*属于\s*(\w+)\s*工艺',
            ],
            relation_type=RelationType.STEP_OF,
            priority=1
        ),
        
        # 参数关系
        RelationType.PARAMETER_OF: RelationPattern(
            patterns=[
                r'(\w+)\s*是\s*(\w+)\s*的?参数',
                r'(\w+)\s*parameter\s*of\s*(\w+)',
            ],
            relation_type=RelationType.PARAMETER_OF,
            priority=1
        ),
        
        # 测量关系
        RelationType.MEASURES: RelationPattern(
            patterns=[
                r'(\w+)\s*测量\s*(\w+)',
                r'(\w+)\s*measures?\s*(\w+)',
                r'(\w+)\s*检测\s*(\w+)',
                r'(\w+)\s*monitors?\s*(\w+)',
            ],
            relation_type=RelationType.MEASURES,
            priority=1
        ),
        
        # 描述关系
        RelationType.DESCRIBES: RelationPattern(
            patterns=[
                r'(\w+)\s*描述\s*(\w+)',
                r'(\w+)\s*describes?\s*(\w+)',
                r'(\w+)\s*说明\s*(\w+)',
            ],
            relation_type=RelationType.DESCRIBES,
            priority=3
        ),
        
        # 相关关系（最弱）
        RelationType.RELATED_TO: RelationPattern(
            patterns=[
                r'(\w+)\s*与\s*(\w+)\s*相关',
                r'(\w+)\s*和\s*(\w+)',
                r'(\w+)\s*related\s*to\s*(\w+)',
            ],
            relation_type=RelationType.RELATED_TO,
            priority=5
        ),
    }
    
    # 实体类型兼容性关系映射
    TYPE_COMPATIBILITY = {
        RelationType.USES: [
            (EntityType.EQUIPMENT, EntityType.MATERIAL),
            (EntityType.PROCESS, EntityType.MATERIAL),
            (EntityType.EQUIPMENT, EntityType.PROCESS),
        ],
        RelationType.HAS_PART: [
            (EntityType.EQUIPMENT, EntityType.EQUIPMENT),
            (EntityType.PROCESS, EntityType.PROCESS),
            (EntityType.PRODUCT, EntityType.MATERIAL),
        ],
        RelationType.REQUIRES: [
            (EntityType.PROCESS, EntityType.PARAMETER),
            (EntityType.EQUIPMENT, EntityType.PARAMETER),
            (EntityType.PROCESS, EntityType.MATERIAL),
        ],
        RelationType.PRODUCES: [
            (EntityType.PROCESS, EntityType.PRODUCT),
            (EntityType.PROCESS, EntityType.MATERIAL),
        ],
        RelationType.INFLUENCES: [
            (EntityType.PARAMETER, EntityType.QUALITY),
            (EntityType.PARAMETER, EntityType.PARAMETER),
            (EntityType.PROCESS, EntityType.QUALITY),
        ],
        RelationType.MEASURES: [
            (EntityType.EQUIPMENT, EntityType.PARAMETER),
            (EntityType.EQUIPMENT, EntityType.QUALITY),
        ],
    }
    
    def __init__(self):
        """初始化关系抽取器"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式"""
        self.compiled_patterns = {}
        for rel_type, pattern_config in self.RELATION_PATTERNS.items():
            self.compiled_patterns[rel_type] = [
                re.compile(p, re.IGNORECASE) for p in pattern_config.patterns
            ]
    
    def extract_relations(
        self,
        text: str,
        entities: List[ExtractedEntity],
        doc_id: Optional[str] = None,
        min_confidence: float = 0.3
    ) -> List[ExtractedRelation]:
        """
        从文本中抽取关系
        
        Args:
            text: 输入文本
            entities: 已抽取的实体列表
            doc_id: 文档ID
            min_confidence: 最小置信度阈值
            
        Returns:
            抽取的关系列表
        """
        start_time = time.time()
        relations = []
        seen_relations = set()  # 用于去重
        
        # 方法1: 基于模式匹配
        pattern_relations = self._extract_by_patterns(text, entities, min_confidence)
        relations.extend(pattern_relations)
        
        # 方法2: 基于实体共现（实体在同一句话中）
        cooccurrence_relations = self._extract_by_cooccurrence(
            text, entities, min_confidence
        )
        relations.extend(cooccurrence_relations)
        
        # 方法3: 基于实体类型推理
        inferred_relations = self._infer_relations_by_types(entities, min_confidence)
        relations.extend(inferred_relations)
        
        # 去重
        unique_relations = []
        for rel in relations:
            rel_key = (rel.head_text, rel.type.value, rel.tail_text)
            if rel_key not in seen_relations:
                seen_relations.add(rel_key)
                unique_relations.append(rel)
        
        return unique_relations
    
    def _extract_by_patterns(
        self,
        text: str,
        entities: List[ExtractedEntity],
        min_confidence: float
    ) -> List[ExtractedRelation]:
        """基于模式匹配抽取关系"""
        relations = []
        entity_map = {e.text: e for e in entities}
        
        for rel_type, pattern_config in self.RELATION_PATTERNS.items():
            compiled_patterns = self.compiled_patterns.get(rel_type, [])
            
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    groups = match.groups()
                    if len(groups) >= 2:
                        head_text = groups[0].strip()
                        tail_text = groups[1].strip()
                        
                        # 检查是否是已知实体
                        head_entity = entity_map.get(head_text) or self._find_similar_entity(
                            head_text, entities
                        )
                        tail_entity = entity_map.get(tail_text) or self._find_similar_entity(
                            tail_text, entities
                        )
                        
                        if head_entity and tail_entity:
                            # 检查类型兼容性
                            if self._check_type_compatibility(
                                rel_type, head_entity.type, tail_entity.type
                            ):
                                confidence = self._calculate_relation_confidence(
                                    match, pattern_config.priority, True
                                )
                                
                                if confidence >= min_confidence:
                                    relation = ExtractedRelation(
                                        head_text=head_text,
                                        tail_text=tail_text,
                                        type=rel_type,
                                        confidence=confidence,
                                        properties={
                                            "head_entity_id": head_entity,
                                            "tail_entity_id": tail_entity,
                                            "context": text[max(0, match.start()-30):min(len(text), match.end()+30)]
                                        }
                                    )
                                    relations.append(relation)
        
        return relations
    
    def _extract_by_cooccurrence(
        self,
        text: str,
        entities: List[ExtractedEntity],
        min_confidence: float
    ) -> List[ExtractedRelation]:
        """基于实体共现抽取关系"""
        relations = []
        
        # 将文本分割为句子
        sentences = re.split(r'[。！？.!?\n]+', text)
        
        for sentence in sentences:
            # 找到句子中的所有实体
            sent_entities = []
            for entity in entities:
                if entity.text in sentence:
                    sent_entities.append(entity)
            
            # 如果句子中有多个实体，尝试建立关系
            if len(sent_entities) >= 2:
                for i, head in enumerate(sent_entities):
                    for tail in sent_entities[i+1:]:
                        # 推断最可能的关系类型
                        rel_type = self._infer_relation_type(head, tail)
                        
                        if rel_type and self._check_type_compatibility(
                            rel_type, head.type, tail.type
                        ):
                            confidence = 0.4  # 共现关系置信度较低
                            
                            if confidence >= min_confidence:
                                relation = ExtractedRelation(
                                    head_text=head.text,
                                    tail_text=tail.text,
                                    type=rel_type,
                                    confidence=confidence,
                                    properties={
                                        "context": sentence.strip(),
                                        "extraction_method": "cooccurrence"
                                    }
                                )
                                relations.append(relation)
        
        return relations
    
    def _infer_relations_by_types(
        self,
        entities: List[ExtractedEntity],
        min_confidence: float
    ) -> List[ExtractedRelation]:
        """基于实体类型推理关系"""
        relations = []
        
        # 按类型分组
        equipment = [e for e in entities if e.type == EntityType.EQUIPMENT]
        processes = [e for e in entities if e.type == EntityType.PROCESS]
        materials = [e for e in entities if e.type == EntityType.MATERIAL]
        parameters = [e for e in entities if e.type == EntityType.PARAMETER]
        
        # 设备-工艺关联
        for equip in equipment:
            for proc in processes:
                if self._entities_mentioned_together(equip, proc):
                    relation = ExtractedRelation(
                        head_text=equip.text,
                        tail_text=proc.text,
                        type=RelationType.OPERATES,
                        confidence=0.35,
                        properties={"extraction_method": "type_inference"}
                    )
                    relations.append(relation)
        
        # 工艺-材料关联
        for proc in processes:
            for mat in materials:
                if self._entities_mentioned_together(proc, mat):
                    relation = ExtractedRelation(
                        head_text=proc.text,
                        tail_text=mat.text,
                        type=RelationType.USES,
                        confidence=0.35,
                        properties={"extraction_method": "type_inference"}
                    )
                    relations.append(relation)
        
        # 工艺-参数关联
        for proc in processes:
            for param in parameters:
                if self._entities_mentioned_together(proc, param):
                    relation = ExtractedRelation(
                        head_text=proc.text,
                        tail_text=param.text,
                        type=RelationType.HAS_PARAMETER,
                        confidence=0.4,
                        properties={"extraction_method": "type_inference"}
                    )
                    relations.append(relation)
        
        return relations
    
    def _find_similar_entity(
        self,
        text: str,
        entities: List[ExtractedEntity]
    ) -> Optional[ExtractedEntity]:
        """查找相似的实体"""
        text_lower = text.lower()
        for entity in entities:
            if text_lower in entity.text.lower() or entity.text.lower() in text_lower:
                return entity
        return None
    
    def _check_type_compatibility(
        self,
        rel_type: RelationType,
        head_type: EntityType,
        tail_type: EntityType
    ) -> bool:
        """检查实体类型是否兼容该关系类型"""
        compatible_pairs = self.TYPE_COMPATIBILITY.get(rel_type, [])
        
        # 如果没有定义兼容对，允许所有
        if not compatible_pairs:
            return True
        
        return (head_type, tail_type) in compatible_pairs
    
    def _calculate_relation_confidence(
        self,
        match,
        priority: int,
        is_pattern_match: bool
    ) -> float:
        """计算关系置信度"""
        confidence = 0.6  # 基础置信度
        
        # 模式匹配加分
        if is_pattern_match:
            confidence += 0.2
        
        # 优先级调整（优先级越低越确定）
        confidence += (6 - priority) * 0.03
        
        # 确保在0-1范围内
        return min(max(confidence, 0.0), 1.0)
    
    def _infer_relation_type(
        self,
        head: ExtractedEntity,
        tail: ExtractedEntity
    ) -> Optional[RelationType]:
        """根据实体类型推断关系类型"""
        type_pair = (head.type, tail.type)
        
        # 常见类型对到关系的映射
        type_relation_map = {
            (EntityType.EQUIPMENT, EntityType.MATERIAL): RelationType.USES,
            (EntityType.EQUIPMENT, EntityType.PROCESS): RelationType.OPERATES,
            (EntityType.PROCESS, EntityType.MATERIAL): RelationType.USES,
            (EntityType.PROCESS, EntityType.PARAMETER): RelationType.HAS_PARAMETER,
            (EntityType.PROCESS, EntityType.QUALITY): RelationType.INFLUENCES,
            (EntityType.PARAMETER, EntityType.QUALITY): RelationType.INFLUENCES,
            (EntityType.EQUIPMENT, EntityType.PARAMETER): RelationType.MEASURES,
        }
        
        return type_relation_map.get(type_pair)
    
    def _entities_mentioned_together(
        self,
        entity1: ExtractedEntity,
        entity2: ExtractedEntity,
        max_distance: int = 100
    ) -> bool:
        """检查两个实体是否在文本中靠得较近"""
        distance = abs(entity1.start - entity2.end)
        return distance <= max_distance


# 全局关系抽取器实例
_relation_extractor = None

def get_relation_extractor() -> RelationExtractor:
    """获取全局关系抽取器实例"""
    global _relation_extractor
    if _relation_extractor is None:
        _relation_extractor = RelationExtractor()
    return _relation_extractor


def extract_relations(
    text: str,
    entities: List[ExtractedEntity],
    doc_id: Optional[str] = None,
    min_confidence: float = 0.3
) -> List[ExtractedRelation]:
    """便捷的关系抽取函数"""
    return get_relation_extractor().extract_relations(text, entities, doc_id, min_confidence)