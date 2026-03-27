"""
Neo4j图数据库服务
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional, Any
import os

class Neo4jService:
    """Neo4j图数据库服务"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    def connect(self):
        """建立连接"""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def __enter__(self):
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def execute(self, query: str, params: Dict = None) -> List[Dict]:
        """执行Cypher查询"""
        if not self.driver:
            self.connect()
        
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
    
    # ========== 实体操作 ==========
    
    def create_entity(self, label: str, properties: Dict) -> Dict:
        """创建实体"""
        query = f"""
        CREATE (e:{label} $props)
        RETURN e
        """
        result = self.execute(query, {"props": properties})
        return result[0]["e"] if result else None
    
    def get_entity(self, label: str, entity_id: str) -> Optional[Dict]:
        """获取实体"""
        query = f"""
        MATCH (e:{label} {{id: $id}})
        RETURN e
        """
        result = self.execute(query, {"id": entity_id})
        return result[0]["e"] if result else None
    
    def update_entity(self, label: str, entity_id: str, properties: Dict) -> Optional[Dict]:
        """更新实体"""
        query = f"""
        MATCH (e:{label} {{id: $id}})
        SET e += $props
        RETURN e
        """
        result = self.execute(query, {"id": entity_id, "props": properties})
        return result[0]["e"] if result else None
    
    def delete_entity(self, label: str, entity_id: str) -> bool:
        """删除实体及其关系"""
        query = f"""
        MATCH (e:{label} {{id: $id}})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        result = self.execute(query, {"id": entity_id})
        return result[0]["deleted"] > 0 if result else False
    
    def search_entities(self, label: str, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索实体"""
        query = f"""
        MATCH (e:{label})
        WHERE e.name CONTAINS $keyword OR e.id CONTAINS $keyword
        RETURN e
        LIMIT $limit
        """
        result = self.execute(query, {"keyword": keyword, "limit": limit})
        return [r["e"] for r in result]
    
    # ========== 关系操作 ==========
    
    def create_relationship(
        self, 
        from_label: str, from_id: str,
        to_label: str, to_id: str,
        rel_type: str,
        properties: Dict = None
    ) -> Optional[Dict]:
        """创建关系"""
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        CREATE (a)-[r:{rel_type} $props]->(b)
        RETURN r
        """
        result = self.execute(query, {
            "from_id": from_id,
            "to_id": to_id,
            "props": properties or {}
        })
        return result[0]["r"] if result else None
    
    def delete_relationship(
        self,
        from_label: str, from_id: str,
        to_label: str, to_id: str,
        rel_type: str
    ) -> bool:
        """删除关系"""
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})-[r:{rel_type}]->(b:{to_label} {{id: $to_id}})
        DELETE r
        RETURN count(r) as deleted
        """
        result = self.execute(query, {
            "from_id": from_id,
            "to_id": to_id
        })
        return result[0]["deleted"] > 0 if result else False
    
    # ========== 图谱查询 ==========
    
    def get_neighbors(self, label: str, entity_id: str, depth: int = 1) -> List[Dict]:
        """获取邻居节点"""
        query = f"""
        MATCH path = (e:{label} {{id: $id}})-[*1..{depth}]-(neighbor)
        RETURN nodes(path) as nodes, relationships(path) as rels
        """
        result = self.execute(query, {"id": entity_id})
        
        neighbors = []
        for r in result:
            nodes = r["nodes"]
            rels = r["rels"]
            for i, node in enumerate(nodes):
                if node.get("id") != entity_id:
                    rel = rels[i] if i < len(rels) else None
                    neighbors.append({
                        "entity": dict(node),
                        "relation": dict(rel) if rel else None
                    })
        return neighbors
    
    def get_subgraph(self, center_label: str, center_id: str, depth: int = 2) -> Dict:
        """获取子图"""
        query = f"""
        MATCH path = (e:{center_label} {{id: $id}})-[*1..{depth}]-(other)
        WITH collect(DISTINCT nodes(path)) as allNodes, collect(DISTINCT relationships(path)) as allRels
        UNWIND allNodes as nodeSet
        WITH distinct nodeSet as nodes, allRels
        UNWIND nodes as n
        WITH collect(DISTINCT n) as distinctNodes, allRels
        UNWIND allRels as relSet
        WITH distinctNodes, collect(DISTINCT relSet) as distinctRels
        RETURN distinctNodes as nodes, distinctRels as relationships
        """
        result = self.execute(query, {"id": center_id})
        return result[0] if result else {"nodes": [], "relationships": []}
    
    def shortest_path(
        self,
        from_label: str, from_id: str,
        to_label: str, to_id: str
    ) -> Optional[List[Dict]]:
        """查找最短路径"""
        query = f"""
        MATCH path = shortestPath((a:{from_label} {{id: $from_id}})-[*]-(b:{to_label} {{id: $to_id}}))
        RETURN nodes(path) as nodes, relationships(path) as rels
        """
        result = self.execute(query, {"from_id": from_id, "to_id": to_id})
        if result:
            return {
                "nodes": [dict(n) for n in result[0]["nodes"]],
                "relationships": [dict(r) for r in result[0]["rels"]]
            }
        return None
    
    def get_connected_entities(
        self,
        label: str,
        entity_id: str,
        rel_type: str = None,
        direction: str = "both"  # outgoing/incoming/both
    ) -> List[Dict]:
        """获取关联实体"""
        if direction == "outgoing":
            pattern = f"(e:{label}{{id: $id}})-[r{':'+rel_type if rel_type else ''}]->(neighbor)"
        elif direction == "incoming":
            pattern = f"(neighbor)-[r{':'+rel_type if rel_type else ''}]->(e:{label}{{id: $id}})"
        else:
            pattern = f"(e:{label}{{id: $id}})-[r{':'+rel_type if rel_type else ''}]-(neighbor)"
        
        query = f"""
        MATCH (e:{label} {{id: $id}}), {pattern}
        RETURN neighbor, r
        """
        result = self.execute(query, {"id": entity_id})
        return [{"entity": dict(r["neighbor"]), "relation": dict(r["r"])} for r in result]
    
    # ========== 统计查询 ==========
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        ORDER BY count DESC
        """
        node_stats = self.execute(query)
        
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY count DESC
        """
        rel_stats = self.execute(query)
        
        return {
            "nodes": [{"label": r["label"], "count": r["count"]} for r in node_stats],
            "relationships": [{"type": r["rel_type"], "count": r["count"]} for r in rel_stats]
        }
    
    def entity_count(self, label: str = None) -> int:
        """实体数量"""
        if label:
            query = f"MATCH (e:{label}) RETURN count(e) as count"
        else:
            query = "MATCH (e) RETURN count(e) as count"
        result = self.execute(query)
        return result[0]["count"] if result else 0
    
    def relationship_count(self, rel_type: str = None) -> int:
        """关系数量"""
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
        else:
            query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = self.execute(query)
        return result[0]["count"] if result else 0


# 全局单例
_neo4j_service: Optional[Neo4jService] = None

def get_neo4j_service() -> Neo4jService:
    """获取Neo4j服务单例"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service
