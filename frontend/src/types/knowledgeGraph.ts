/**
 * 知识图谱类型定义
 */

// 实体类型
export type EntityType = 'equipment' | 'process' | 'material' | 'parameter' | 'document' | 'person' | 'organization' | 'location';

// 实体接口
export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  description?: string;
  properties?: Record<string, any>;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  confidence?: number;
  source?: string;
  metadata?: Record<string, any>;
}

// 关系类型
export type RelationType = 'uses' | 'produces' | 'requires' | 'part_of' | 'located_at' | 'operated_by' | 'related_to' | 'references';

// 关系接口
export interface Relation {
  id: string;
  source_id: string;
  target_id: string;
  type: RelationType;
  name?: string;
  description?: string;
  properties?: Record<string, any>;
  confidence?: number;
  created_at?: string;
  updated_at?: string;
}

// 图谱数据接口（用于可视化）
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  categories?: GraphCategory[];
}

// 图谱节点
export interface GraphNode {
  id: string;
  name: string;
  value?: number;
  symbolSize?: number;
  category?: number;
  x?: number;
  y?: number;
  itemStyle?: any;
  label?: any;
  data?: Entity;
}

// 图谱边
export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  value?: number;
  name?: string;
  lineStyle?: any;
  label?: any;
  data?: Relation;
}

// 图谱分类
export interface GraphCategory {
  name: string;
  itemStyle?: any;
}

// 搜索参数
export interface EntitySearchParams {
  keyword?: string;
  type?: EntityType;
  tags?: string[];
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 搜索结果
export interface EntitySearchResult {
  entities: Entity[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// 推荐结果
export interface Recommendation {
  id: string;
  type: 'entity' | 'document' | 'relation';
  title: string;
  description: string;
  score: number;
  reason: string;
  data: Entity | any;
}

// 图谱统计
export interface GraphStats {
  total_entities: number;
  total_relations: number;
  entity_types: Record<EntityType, number>;
  relation_types: Record<RelationType, number>;
  recent_entities: Entity[];
  hot_entities: Entity[];
}

// 图谱操作记录
export interface GraphOperation {
  id: string;
  type: 'create' | 'update' | 'delete' | 'merge' | 'import';
  target_type: 'entity' | 'relation';
  target_id: string;
  target_name: string;
  operator: string;
  operation_time: string;
  details?: string;
}
