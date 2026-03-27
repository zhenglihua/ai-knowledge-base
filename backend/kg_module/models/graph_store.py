"""
知识图谱存储 - NetworkX实现
轻量级、无需外部数据库的知识图谱存储方案
"""
import os
import json
import pickle
from typing import List, Dict, Optional, Tuple, Set, Any
from datetime import datetime
from pathlib import Path

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("⚠️ networkx未安装，知识图谱功能将受限")

from kg_module.models.entity import (
    Entity, Relation, KnowledgeTriple, EntityType, RelationType,
    EntityMention, ExtractedEntity, ExtractedRelation
)


class KnowledgeGraphStore:
    """知识图谱存储类 - 基于NetworkX"""
    
    def __init__(self, storage_path: str = "data/knowledge_graph.pkl"):
        """
        初始化知识图谱存储
        
        Args:
            storage_path: 图谱数据存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not NETWORKX_AVAILABLE:
            raise ImportError("需要安装networkx: pip install networkx")
        
        # 创建有向图
        self.graph = nx.DiGraph()
        
        # 实体和关系索引
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.mentions: Dict[str, List[EntityMention]] = {}  # entity_id -> mentions
        
        # 名称到实体的映射（用于快速查找）
        self.name_to_entities: Dict[str, Set[str]] = {}  # normalized_name -> entity_ids
        
        # 加载已有数据
        self._load()
    
    def _normalize_name(self, name: str) -> str:
        """标准化名称用于索引"""
        return name.lower().strip()
    
    def _load(self):
        """从文件加载图谱数据"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                    self.entities = data.get('entities', {})
                    self.relations = data.get('relations', {})
                    self.mentions = data.get('mentions', {})
                    self.name_to_entities = data.get('name_to_entities', {})
                    
                # 重建NetworkX图
                self._rebuild_graph()
                print(f"📚 已加载知识图谱: {len(self.entities)}个实体, {len(self.relations)}个关系")
            except Exception as e:
                print(f"⚠️ 加载知识图谱失败: {e}，将创建新图谱")
                self._init_empty()
        else:
            self._init_empty()
    
    def _init_empty(self):
        """初始化空图谱"""
        self.graph = nx.DiGraph()
        self.entities = {}
        self.relations = {}
        self.mentions = {}
        self.name_to_entities = {}
    
    def _rebuild_graph(self):
        """从实体和关系重建NetworkX图"""
        self.graph = nx.DiGraph()
        
        # 添加节点
        for entity_id, entity in self.entities.items():
            self.graph.add_node(entity_id, **entity.to_dict())
        
        # 添加边
        for relation_id, relation in self.relations.items():
            self.graph.add_edge(
                relation.source_id,
                relation.target_id,
                **relation.to_dict()
            )
    
    def save(self):
        """保存图谱数据到文件"""
        try:
            data = {
                'entities': self.entities,
                'relations': self.relations,
                'mentions': self.mentions,
                'name_to_entities': self.name_to_entities,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.storage_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"❌ 保存知识图谱失败: {e}")
            return False
    
    # ========== 实体操作 ==========
    
    def add_entity(self, entity: Entity) -> Entity:
        """
        添加实体到图谱
        
        Args:
            entity: 要添加的实体
            
        Returns:
            Entity: 添加的实体（可能是合并后的已有实体）
        """
        # 检查是否已存在同名实体
        normalized_name = self._normalize_name(entity.name)
        existing_ids = self.name_to_entities.get(normalized_name, set())
        
        # 查找相同类型的实体进行合并
        for existing_id in existing_ids:
            existing = self.entities.get(existing_id)
            if existing and existing.type == entity.type:
                # 合并实体信息
                self._merge_entities(existing, entity)
                return existing
        
        # 添加新实体
        self.entities[entity.id] = entity
        self.graph.add_node(entity.id, **entity.to_dict())
        
        # 更新名称索引
        if normalized_name not in self.name_to_entities:
            self.name_to_entities[normalized_name] = set()
        self.name_to_entities[normalized_name].add(entity.id)
        
        # 添加别名索引
        for alias in entity.aliases:
            alias_normalized = self._normalize_name(alias)
            if alias_normalized not in self.name_to_entities:
                self.name_to_entities[alias_normalized] = set()
            self.name_to_entities[alias_normalized].add(entity.id)
        
        return entity
    
    def _merge_entities(self, existing: Entity, new: Entity):
        """合并两个实体"""
        # 合并别名
        existing.aliases = list(set(existing.aliases + new.aliases + [new.name]))
        
        # 合并属性
        existing.properties.update(new.properties)
        
        # 更新置信度（取最高）
        existing.confidence = max(existing.confidence, new.confidence)
        
        # 更新时间
        existing.updated_at = datetime.now()
        
        # 更新图中节点
        self.graph.nodes[existing.id].update(existing.to_dict())
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """根据ID获取实体"""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str, entity_type: Optional[EntityType] = None) -> Optional[Entity]:
        """
        根据名称获取实体
        
        Args:
            name: 实体名称
            entity_type: 可选的实体类型过滤
            
        Returns:
            找到的实体或None
        """
        normalized_name = self._normalize_name(name)
        entity_ids = self.name_to_entities.get(normalized_name, set())
        
        for entity_id in entity_ids:
            entity = self.entities.get(entity_id)
            if entity:
                if entity_type is None or entity.type == entity_type:
                    return entity
        return None
    
    def search_entities(
        self,
        keyword: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 20
    ) -> List[Entity]:
        """
        搜索实体
        
        Args:
            keyword: 搜索关键词
            entity_type: 可选的实体类型过滤
            limit: 返回结果数量限制
            
        Returns:
            匹配的实体列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for entity in self.entities.values():
            # 检查名称匹配
            name_match = keyword_lower in entity.name.lower()
            # 检查别名匹配
            alias_match = any(keyword_lower in alias.lower() for alias in entity.aliases)
            # 检查属性匹配
            prop_match = any(
                keyword_lower in str(v).lower() 
                for v in entity.properties.values()
            )
            
            if name_match or alias_match or prop_match:
                # 类型过滤
                if entity_type is None or entity.type == entity_type:
                    # 计算匹配分数
                    score = 0
                    if name_match:
                        score += 2 if entity.name.lower() == keyword_lower else 1
                    if alias_match:
                        score += 1
                    
                    results.append((entity, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in results[:limit]]
    
    def delete_entity(self, entity_id: str) -> bool:
        """删除实体及其关系"""
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # 删除相关关系
        relations_to_delete = []
        for rel_id, rel in self.relations.items():
            if rel.source_id == entity_id or rel.target_id == entity_id:
                relations_to_delete.append(rel_id)
        
        for rel_id in relations_to_delete:
            self.delete_relation(rel_id)
        
        # 从图中删除节点
        self.graph.remove_node(entity_id)
        
        # 从实体字典删除
        del self.entities[entity_id]
        
        # 更新名称索引
        normalized_name = self._normalize_name(entity.name)
        if normalized_name in self.name_to_entities:
            self.name_to_entities[normalized_name].discard(entity_id)
        
        return True
    
    # ========== 关系操作 ==========
    
    def add_relation(self, relation: Relation) -> Relation:
        """添加关系到图谱"""
        # 检查源实体和目标实体是否存在
        if relation.source_id not in self.entities:
            raise ValueError(f"源实体不存在: {relation.source_id}")
        if relation.target_id not in self.entities:
            raise ValueError(f"目标实体不存在: {relation.target_id}")
        
        # 检查是否已存在相同的关系
        for existing_id, existing in self.relations.items():
            if (existing.source_id == relation.source_id and 
                existing.target_id == relation.target_id and
                existing.type == relation.type):
                # 更新已有关系
                existing.confidence = max(existing.confidence, relation.confidence)
                existing.properties.update(relation.properties)
                return existing
        
        # 添加新关系
        self.relations[relation.id] = relation
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            **relation.to_dict()
        )
        
        return relation
    
    def get_relation(self, relation_id: str) -> Optional[Relation]:
        """根据ID获取关系"""
        return self.relations.get(relation_id)
    
    def get_relations_by_entity(
        self,
        entity_id: str,
        direction: str = "both"  # "out", "in", "both"
    ) -> List[Tuple[Relation, Entity]]:
        """
        获取实体的相关关系
        
        Args:
            entity_id: 实体ID
            direction: 关系方向 - "out"出边, "in"入边, "both"双向
            
        Returns:
            [(关系, 相关实体), ...]
        """
        results = []
        
        if direction in ("out", "both"):
            # 出边关系
            for rel_id in self.graph.successors(entity_id):
                for edge_data in self.graph[entity_id][rel_id].values():
                    relation = self.relations.get(edge_data.get('id'))
                    if relation:
                        target_entity = self.entities.get(rel_id)
                        if target_entity:
                            results.append((relation, target_entity))
        
        if direction in ("in", "both"):
            # 入边关系
            for rel_id in self.graph.predecessors(entity_id):
                for edge_data in self.graph[rel_id][entity_id].values():
                    relation = self.relations.get(edge_data.get('id'))
                    if relation:
                        source_entity = self.entities.get(rel_id)
                        if source_entity:
                            results.append((relation, source_entity))
        
        return results
    
    def delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        if relation_id not in self.relations:
            return False
        
        relation = self.relations[relation_id]
        
        # 从图中删除边
        if self.graph.has_edge(relation.source_id, relation.target_id):
            self.graph.remove_edge(relation.source_id, relation.target_id)
        
        # 从关系字典删除
        del self.relations[relation_id]
        
        return True
    
    # ========== 图谱查询 ==========
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        depth: int = 1
    ) -> List[Dict]:
        """
        获取实体的邻居节点
        
        Args:
            entity_id: 实体ID
            relation_type: 可选的关系类型过滤
            depth: 搜索深度
            
        Returns:
            邻居实体列表
        """
        if entity_id not in self.graph:
            return []
        
        results = []
        seen = {entity_id}
        current_level = {entity_id}
        
        for d in range(depth):
            next_level = set()
            for node in current_level:
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in seen:
                        seen.add(neighbor)
                        next_level.add(neighbor)
                        
                        entity = self.entities.get(neighbor)
                        if entity:
                            # 获取连接关系
                            edge_data = self.graph[node][neighbor]
                            # 处理单一边和多边情况
                            if isinstance(edge_data, dict):
                                items_to_check = [edge_data]
                            else:
                                items_to_check = edge_data.values() if hasattr(edge_data, 'values') else [edge_data]
                            
                            for data in items_to_check:
                                if isinstance(data, dict):
                                    relation = self.relations.get(data.get('id'))
                                    if relation:
                                        if relation_type is None or relation.type == relation_type:
                                            results.append({
                                                "entity": entity.to_dict(),
                                                "relation": relation.to_dict(),
                                                "depth": d + 1
                                            })
            current_level = next_level
        
        return results
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[Dict]]:
        """
        查找两个实体之间的路径
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            max_depth: 最大搜索深度
            
        Returns:
            路径上的实体和关系列表，或None
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(
                self.graph.to_undirected(),
                source_id,
                target_id
            )
            
            result = []
            for i, entity_id in enumerate(path):
                entity = self.entities.get(entity_id)
                if entity:
                    node_info = {"entity": entity.to_dict(), "step": i}
                    
                    # 添加关系信息（除了最后一个节点）
                    if i < len(path) - 1:
                        next_id = path[i + 1]
                        edge_data = self.graph[entity_id][next_id]
                        for data in edge_data.values():
                            relation = self.relations.get(data.get('id'))
                            if relation:
                                node_info["relation"] = relation.to_dict()
                                break
                    
                    result.append(node_info)
            
            return result
        except nx.NetworkXNoPath:
            return None
    
    def find_connected_components(self) -> List[List[str]]:
        """查找连通分量"""
        undirected = self.graph.to_undirected()
        return list(nx.connected_components(undirected))
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        return {
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "entity_types": {
                et.value: len([e for e in self.entities.values() if e.type == et])
                for et in EntityType
            },
            "relation_types": {
                rt.value: len([r for r in self.relations.values() if r.type == rt])
                for rt in RelationType
            },
            "connected_components": len(self.find_connected_components()),
            "density": nx.density(self.graph) if len(self.graph) > 0 else 0
        }
    
    # ========== 文档提及 ==========
    
    def add_mention(self, mention: EntityMention):
        """添加实体提及记录"""
        if mention.entity_id not in self.mentions:
            self.mentions[mention.entity_id] = []
        self.mentions[mention.entity_id].append(mention)
    
    def get_entity_mentions(self, entity_id: str) -> List[EntityMention]:
        """获取实体的所有提及"""
        return self.mentions.get(entity_id, [])
    
    def get_document_entities(self, doc_id: str) -> List[Entity]:
        """获取文档中提到的所有实体"""
        entities = []
        for entity_id, mentions in self.mentions.items():
            for mention in mentions:
                if mention.doc_id == doc_id:
                    entity = self.entities.get(entity_id)
                    if entity and entity not in entities:
                        entities.append(entity)
                    break
        return entities
    
    # ========== 导出/导入 ==========
    
    def export_to_json(self, filepath: str):
        """导出图谱为JSON格式"""
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations.values()],
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, filepath: str):
        """从JSON导入图谱"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 导入实体
        for entity_data in data.get("entities", []):
            entity = Entity.from_dict(entity_data)
            self.add_entity(entity)
        
        # 导入关系
        for relation_data in data.get("relations", []):
            relation = Relation.from_dict(relation_data)
            self.add_relation(relation)


# 全局存储实例
_graph_store = None

def get_graph_store(storage_path: str = "data/knowledge_graph.pkl") -> KnowledgeGraphStore:
    """获取全局知识图谱存储实例"""
    global _graph_store
    if _graph_store is None:
        _graph_store = KnowledgeGraphStore(storage_path)
    return _graph_store