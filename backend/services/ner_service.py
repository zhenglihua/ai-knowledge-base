"""
半导体行业实体识别与关系抽取服务
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Entity:
    """实体"""
    id: str
    name: str
    type: str  # Equipment/Process/Material/Parameter/Fault/Person/Document/Term
    properties: Dict


@dataclass
class Relation:
    """关系"""
    from_id: str
    from_type: str
    to_id: str
    to_type: str
    relation_type: str
    properties: Dict


class SemiconductorNER:
    """半导体行业实体识别器"""
    
    # 实体类型
    ENTITY_TYPES = {
        'equipment': ['光刻机', '刻蚀机', 'CVD', 'PVD', 'CMP', '退火炉', '离子注入机', '清洗机', '检测设备', '显微镜', ' spectrometer', '机台', '设备'],
        'process': ['光刻', '刻蚀', '沉积', '镀膜', '离子注入', '退火', '清洗', '氧化', '扩散', '掺杂', 'CMP', '化学机械平坦化'],
        'material': ['晶圆', '光刻胶', '硅片', '靶材', '气体', '液体', '化学品', '试剂', '溶液'],
        'parameter': ['温度', '压力', '流量', '时间', '功率', '电压', '电流', '转速', '浓度', '纯度', '厚度', '速率'],
        'fault': ['报警', '异常', '不良', '缺陷', 'Error', 'Fault', 'Alarming'],
        'person': ['工程师', '技术员', '经理', '主管', 'operator', 'engineer'],
        'document': ['SOP', '规格书', 'spec', '手册', '作业指导书', '工艺卡', '参数表'],
        'term': ['Wafer', 'Die', 'Chip', 'Lot', 'Batch', 'Module', 'Layer']
    }
    
    # 正则模式
    PATTERNS = {
        'equipment_id': r'[A-Z]{2,5}[-_]?\d{3,6}',  # 如: ALD-1234,ETCH_5678
        'temperature': r'(\d+(?:\.\d+)?)\s*(?:℃|°C|度)',  # 如: 150℃, 200.5度
        'pressure': r'(\d+(?:\.\d+)?)\s*(?:Pa|kPa|mTorr|Torr|mbar)',  # 如: 100Pa, 50mTorr
        'flow_rate': r'(\d+(?:\.\d+)?)\s*(?:sccm|slm|mL|ml/min)',  # 如: 100sccm, 50ml/min
        'time_duration': r'(\d+(?:\.\d+)?)\s*(?:s|sec|min|分钟|秒)',  # 如: 30s, 5min
    }
    
    def recognize(self, text: str) -> List[Entity]:
        """识别文本中的实体"""
        entities = []
        text_lower = text.lower()
        
        # 按类型识别
        for entity_type, keywords in self.ENTITY_TYPES.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # 创建实体
                    entity = Entity(
                        id=self._generate_id(keyword),
                        name=keyword,
                        type=entity_type.capitalize(),
                        properties={'source': 'keyword_match', 'confidence': 0.9}
                    )
                    entities.append(entity)
        
        # 使用正则识别参数类实体
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity = Entity(
                    id=self._generate_id(match.group()),
                    name=match.group(),
                    type='Parameter',
                    properties={
                        'source': 'regex_match',
                        'pattern': pattern_name,
                        'value': match.group(),
                        'confidence': 0.85
                    }
                )
                entities.append(entity)
        
        # 去重
        seen = set()
        unique_entities = []
        for e in entities:
            key = (e.name, e.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        
        return unique_entities
    
    def _generate_id(self, name: str) -> str:
        """生成实体ID"""
        import hashlib
        return hashlib.md5(name.encode()).hexdigest()[:8]


class SemiconductorRelationExtractor:
    """半导体行业关系抽取器"""
    
    # 关系模式
    RELATION_PATTERNS = [
        # 设备-工艺关系
        (r'([\w]+)使用([\w]+)', 'USES'),
        (r'([\w]+)采用([\w]+)工艺', 'USES'),
        (r'([\w]+)通过([\w]+)', 'THROUGH'),
        
        # 设备-参数关系
        (r'([\w]+)参数.*?(\d+(?:\.\d+)?)', 'HAS_PARAMETER'),
        (r'设置(\d+(?:\.\d+)?).*?([\w]+)', 'PARAMETER_OF'),
        
        # 工艺-参数关系
        (r'([\w]+)温度(\d+)', 'HAS_TEMP'),
        (r'([\w]+)压力(\d+)', 'HAS_PRESSURE'),
        
        # 故障关系
        (r'([\w]+)导致([\w]+)异常', 'CAUSES'),
        (r'([\w]+)引发([\w]+)报警', 'CAUSES'),
    ]
    
    def extract(self, text: str, entities: List[Entity]) -> List[Relation]:
        """抽取实体间的关系"""
        relations = []
        
        # 基于模式的抽取
        for pattern, rel_type in self.RELATION_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                from_name = match.group(1)
                to_name = match.group(2)
                
                # 查找对应的实体
                from_entity = self._find_entity(from_name, entities)
                to_entity = self._find_entity(to_name, entities)
                
                if from_entity and to_entity:
                    relation = Relation(
                        from_id=from_entity.id,
                        from_type=from_entity.type,
                        to_id=to_entity.id,
                        to_type=to_entity.type,
                        relation_type=rel_type,
                        properties={'source': 'pattern_match', 'text': match.group()}
                    )
                    relations.append(relation)
        
        return relations
    
    def _find_entity(self, name: str, entities: List[Entity]) -> Optional[Entity]:
        """查找匹配的实体"""
        for e in entities:
            if name in e.name or e.name in name:
                return e
        return None


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self):
        self.ner = SemiconductorNER()
        self.extractor = SemiconductorRelationExtractor()
    
    def process_document(self, text: str, doc_id: str) -> Tuple[List[Entity], List[Relation]]:
        """处理文档，提取实体和关系"""
        # 实体识别
        entities = self.ner.recognize(text)
        
        # 关系抽取
        relations = self.extractor.extract(text, entities)
        
        # 添加文档实体
        doc_entity = Entity(
            id=doc_id,
            name=f'Doc_{doc_id}',
            type='Document',
            properties={'doc_id': doc_id}
        )
        entities.append(doc_entity)
        
        # 建立文档-内容关系
        for e in entities:
            if e.id != doc_entity.id:
                rel = Relation(
                    from_id=doc_entity.id,
                    from_type='Document',
                    to_id=e.id,
                    to_type=e.type,
                    relation_type='CONTAINS',
                    properties={}
                )
                relations.append(rel)
        
        return entities, relations
    
    def process_equipment_manual(self, text: str, equipment_id: str, equipment_name: str) -> Tuple[List[Entity], List[Relation]]:
        """处理设备手册"""
        # 创建设备实体
        equipment = Entity(
            id=equipment_id,
            name=equipment_name,
            type='Equipment',
            properties={'source': 'equipment_manual'}
        )
        entities = [equipment]
        
        # 识别相关内容
        related_entities = self.ner.recognize(text)
        relations = []
        
        # 建立设备-相关实体关系
        for e in related_entities:
            if e.id != equipment_id:
                rel = Relation(
                    from_id=equipment_id,
                    from_type='Equipment',
                    to_id=e.id,
                    to_type=e.type,
                    relation_type='HAS_RELATED',
                    properties={}
                )
                relations.append(rel)
        
        entities.extend(related_entities)
        return entities, relations


# 全局单例
_ner_service: Optional[KnowledgeGraphBuilder] = None

def get_ner_service() -> KnowledgeGraphBuilder:
    """获取NER服务单例"""
    global _ner_service
    if _ner_service is None:
        _ner_service = KnowledgeGraphBuilder()
    return _ner_service
