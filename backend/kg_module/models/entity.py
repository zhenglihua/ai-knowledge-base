"""
知识图谱实体和关系模型定义
"""
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class EntityType(Enum):
    """实体类型枚举"""
    EQUIPMENT = "equipment"           # 设备
    PROCESS = "process"               # 工艺
    MATERIAL = "material"             # 材料
    PARAMETER = "parameter"           # 参数
    PRODUCT = "product"               # 产品
    QUALITY = "quality"               # 质量指标
    PERSON = "person"                 # 人员
    DEPARTMENT = "department"         # 部门
    DOCUMENT = "document"             # 文档
    LOCATION = "location"             # 位置
    OTHER = "other"                   # 其他


class RelationType(Enum):
    """关系类型枚举"""
    # 设备相关
    USES = "uses"                     # 使用（设备使用材料）
    HAS_PART = "has_part"             # 有部件
    PART_OF = "part_of"               # 是部件
    OPERATES = "operates"             # 操作
    MAINTAINS = "maintains"           # 维护
    
    # 工艺相关
    HAS_PROCESS = "has_process"       # 有工艺步骤
    STEP_OF = "step_of"               # 是工艺步骤
    REQUIRES = "requires"             # 需要
    PRODUCES = "produces"             # 产生
    
    # 参数相关
    HAS_PARAMETER = "has_parameter"   # 有参数
    PARAMETER_OF = "parameter_of"     # 是参数
    INFLUENCES = "influences"         # 影响
    DEPENDS_ON = "depends_on"         # 依赖于
    
    # 质量相关
    AFFECTS_QUALITY = "affects_quality"  # 影响质量
    MEASURES = "measures"             # 测量
    DETECTS = "detects"               # 检测
    
    # 文档相关
    MENTIONS = "mentions"             # 提及
    DESCRIBES = "describes"           # 描述
    RELATED_TO = "related_to"         # 相关
    
    # 一般关系
    SIMILAR_TO = "similar_to"         # 相似
    CONTRADICTS = "contradicts"       # 矛盾
    REPLACES = "replaces"             # 替换


@dataclass
class Entity:
    """知识图谱实体"""
    id: str
    name: str                          # 实体名称
    type: EntityType                   # 实体类型
    description: str = ""              # 实体描述
    aliases: List[str] = field(default_factory=list)  # 别名列表
    properties: Dict[str, Any] = field(default_factory=dict)  # 附加属性
    confidence: float = 1.0            # 置信度
    source_doc_id: Optional[str] = None  # 来源文档ID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = EntityType(self.type)
    
    @classmethod
    def create(
        cls,
        name: str,
        entity_type: EntityType,
        description: str = "",
        aliases: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source_doc_id: Optional[str] = None
    ) -> "Entity":
        """工厂方法创建实体"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            type=entity_type,
            description=description,
            aliases=aliases or [],
            properties=properties or {},
            confidence=confidence,
            source_doc_id=source_doc_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "aliases": self.aliases,
            "properties": self.properties,
            "confidence": self.confidence,
            "source_doc_id": self.source_doc_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """从字典创建"""
        data = data.copy()
        data["type"] = EntityType(data.get("type", "other"))
        data["created_at"] = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        data["updated_at"] = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        return cls(**data)
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.name
    
    def add_alias(self, alias: str):
        """添加别名"""
        if alias and alias != self.name and alias not in self.aliases:
            self.aliases.append(alias)
    
    def get_type_display(self) -> str:
        """获取类型显示名称"""
        type_names = {
            EntityType.EQUIPMENT: "设备",
            EntityType.PROCESS: "工艺",
            EntityType.MATERIAL: "材料",
            EntityType.PARAMETER: "参数",
            EntityType.PRODUCT: "产品",
            EntityType.QUALITY: "质量指标",
            EntityType.PERSON: "人员",
            EntityType.DEPARTMENT: "部门",
            EntityType.DOCUMENT: "文档",
            EntityType.LOCATION: "位置",
            EntityType.OTHER: "其他"
        }
        return type_names.get(self.type, "未知")


@dataclass
class Relation:
    """知识图谱关系"""
    id: str
    type: RelationType               # 关系类型
    source_id: str                   # 源实体ID
    target_id: str                   # 目标实体ID
    description: str = ""            # 关系描述
    properties: Dict[str, Any] = field(default_factory=dict)  # 附加属性
    confidence: float = 1.0          # 置信度
    source_doc_id: Optional[str] = None  # 来源文档ID
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = RelationType(self.type)
    
    @classmethod
    def create(
        cls,
        relation_type: RelationType,
        source_id: str,
        target_id: str,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source_doc_id: Optional[str] = None
    ) -> "Relation":
        """工厂方法创建关系"""
        return cls(
            id=str(uuid.uuid4()),
            type=relation_type,
            source_id=source_id,
            target_id=target_id,
            description=description,
            properties=properties or {},
            confidence=confidence,
            source_doc_id=source_doc_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "description": self.description,
            "properties": self.properties,
            "confidence": self.confidence,
            "source_doc_id": self.source_doc_id,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relation":
        """从字典创建"""
        data = data.copy()
        data["type"] = RelationType(data.get("type", "related_to"))
        data["created_at"] = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        return cls(**data)
    
    def get_type_display(self) -> str:
        """获取关系类型显示名称"""
        type_names = {
            RelationType.USES: "使用",
            RelationType.HAS_PART: "包含部件",
            RelationType.PART_OF: "属于",
            RelationType.OPERATES: "操作",
            RelationType.MAINTAINS: "维护",
            RelationType.HAS_PROCESS: "有工艺",
            RelationType.STEP_OF: "是步骤",
            RelationType.REQUIRES: "需要",
            RelationType.PRODUCES: "产生",
            RelationType.HAS_PARAMETER: "有参数",
            RelationType.PARAMETER_OF: "是参数",
            RelationType.INFLUENCES: "影响",
            RelationType.DEPENDS_ON: "依赖于",
            RelationType.AFFECTS_QUALITY: "影响质量",
            RelationType.MEASURES: "测量",
            RelationType.DETECTS: "检测",
            RelationType.MENTIONS: "提及",
            RelationType.DESCRIBES: "描述",
            RelationType.RELATED_TO: "相关",
            RelationType.SIMILAR_TO: "相似",
            RelationType.CONTRADICTS: "矛盾",
            RelationType.REPLACES: "替换"
        }
        return type_names.get(self.type, "关联")


@dataclass
class EntityMention:
    """实体在文档中的提及"""
    entity_id: str                   # 实体ID
    doc_id: str                      # 文档ID
    start_pos: int                   # 开始位置
    end_pos: int                     # 结束位置
    context: str = ""                # 上下文文本
    confidence: float = 1.0          # 置信度
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityMention":
        return cls(**data)


@dataclass
class KnowledgeTriple:
    """知识三元组 (头实体, 关系, 尾实体)"""
    head: Entity
    relation: Relation
    tail: Entity
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head.to_dict(),
            "relation": self.relation.to_dict(),
            "tail": self.tail.to_dict(),
            "confidence": self.confidence
        }


# 抽取结果模型（用于NLP服务返回）

@dataclass
class ExtractedEntity:
    """抽取出的实体"""
    text: str                        # 原始文本
    type: EntityType                 # 实体类型
    start: int                       # 在文档中的开始位置
    end: int                         # 在文档中的结束位置
    confidence: float = 1.0          # 置信度
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "type": self.type.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedEntity":
        data = data.copy()
        data["type"] = EntityType(data.get("type", "other"))
        return cls(**data)


@dataclass
class ExtractedRelation:
    """抽取出的关系"""
    head_text: str                   # 头实体文本
    tail_text: str                   # 尾实体文本
    type: RelationType               # 关系类型
    confidence: float = 1.0          # 置信度
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "head_text": self.head_text,
            "tail_text": self.tail_text,
            "type": self.type.value,
            "confidence": self.confidence,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedRelation":
        data = data.copy()
        data["type"] = RelationType(data.get("type", "related_to"))
        return cls(**data)


@dataclass
class ExtractionResult:
    """文档抽取结果"""
    doc_id: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    relations: List[ExtractedRelation] = field(default_factory=list)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
            "processing_time_ms": self.processing_time_ms
        }