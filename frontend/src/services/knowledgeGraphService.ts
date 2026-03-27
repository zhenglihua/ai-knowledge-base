import axios from 'axios';
import {
  Entity,
  EntitySearchParams,
  EntitySearchResult,
  Relation,
  GraphData,
  Recommendation,
  GraphStats,
  GraphOperation,
  EntityType,
  RelationType,
} from '../types/knowledgeGraph';
import {
  mockGraphData,
  mockEntities,
  mockRelations,
  mockGraphStats,
  mockOperations,
  mockRecommendations,
} from '../data/mockKnowledgeGraph';

const API_BASE = 'http://localhost:8000/api';

/**
 * 知识图谱服务
 */
export const knowledgeGraphService = {
  /**
   * 获取图谱统计信息
   */
  async getStats(): Promise<GraphStats> {
    try {
      const response = await axios.get(`${API_BASE}/graph/stats`);
      return response.data;
    } catch (error) {
      console.log('API不可用，使用mock数据');
      return mockGraphStats;
    }
  },

  /**
   * 获取图谱数据（用于可视化）
   */
  async getGraphData(centerId?: string, depth: number = 2): Promise<GraphData> {
    try {
      const params = centerId ? { center_id: centerId, depth } : {};
      const response = await axios.get(`${API_BASE}/graph/data`, { params });
      return response.data;
    } catch (error) {
      console.log('API不可用，使用mock数据');
      return mockGraphData;
    }
  },

  /**
   * 搜索实体
   */
  async searchEntities(params: EntitySearchParams): Promise<EntitySearchResult> {
    try {
      const response = await axios.get(`${API_BASE}/graph/entities/search`, { params });
      return response.data;
    } catch (error) {
      console.log('API不可用，使用mock数据搜索');
      // 在mock数据中搜索
      let filtered = mockEntities;
      
      if (params.keyword) {
        const keyword = params.keyword.toLowerCase();
        filtered = filtered.filter(e => 
          e.name.toLowerCase().includes(keyword) ||
          (e.description && e.description.toLowerCase().includes(keyword))
        );
      }
      
      if (params.type) {
        filtered = filtered.filter(e => e.type === params.type);
      }
      
      const limit = params.limit || 20;
      const page = params.page || 1;
      const start = (page - 1) * limit;
      const end = start + limit;
      
      return {
        entities: filtered.slice(start, end),
        total: filtered.length,
        page,
        limit,
        total_pages: Math.ceil(filtered.length / limit),
      };
    }
  },

  /**
   * 获取实体详情
   */
  async getEntityById(id: string): Promise<Entity | null> {
    try {
      const response = await axios.get(`${API_BASE}/graph/entities/${id}`);
      return response.data;
    } catch (error) {
      console.log('API不可用，从mock数据中查找');
      return mockEntities.find(e => e.id === id) || null;
    }
  },

  /**
   * 获取实体的关系
   */
  async getEntityRelations(entityId: string, direction?: 'in' | 'out' | 'both'): Promise<Relation[]> {
    try {
      const params = direction ? { direction } : {};
      const response = await axios.get(`${API_BASE}/graph/entities/${entityId}/relations`, { params });
      return response.data.relations || [];
    } catch (error) {
      console.log('API不可用，从mock数据中查找关系');
      return mockRelations.filter(r => 
        r.source_id === entityId || r.target_id === entityId
      );
    }
  },

  /**
   * 获取实体的邻居
   */
  async getEntityNeighbors(entityId: string): Promise<Entity[]> {
    try {
      const response = await axios.get(`${API_BASE}/graph/entities/${entityId}/neighbors`);
      return response.data.entities || [];
    } catch (error) {
      console.log('API不可用，从mock数据中查找邻居');
      const relatedIds = new Set<string>();
      mockRelations.forEach(r => {
        if (r.source_id === entityId) relatedIds.add(r.target_id);
        if (r.target_id === entityId) relatedIds.add(r.source_id);
      });
      return mockEntities.filter(e => relatedIds.has(e.id));
    }
  },

  /**
   * 创建实体
   */
  async createEntity(entity: Partial<Entity>): Promise<Entity | null> {
    try {
      const response = await axios.post(`${API_BASE}/graph/entities`, entity);
      return response.data;
    } catch (error) {
      console.error('创建实体失败:', error);
      return null;
    }
  },

  /**
   * 更新实体
   */
  async updateEntity(id: string, entity: Partial<Entity>): Promise<Entity | null> {
    try {
      const response = await axios.put(`${API_BASE}/graph/entities/${id}`, entity);
      return response.data;
    } catch (error) {
      console.error('更新实体失败:', error);
      return null;
    }
  },

  /**
   * 删除实体
   */
  async deleteEntity(id: string): Promise<boolean> {
    try {
      await axios.delete(`${API_BASE}/graph/entities/${id}`);
      return true;
    } catch (error) {
      console.error('删除实体失败:', error);
      return false;
    }
  },

  /**
   * 创建关系
   */
  async createRelation(relation: Partial<Relation>): Promise<Relation | null> {
    try {
      const response = await axios.post(`${API_BASE}/graph/relations`, relation);
      return response.data;
    } catch (error) {
      console.error('创建关系失败:', error);
      return null;
    }
  },

  /**
   * 删除关系
   */
  async deleteRelation(id: string): Promise<boolean> {
    try {
      await axios.delete(`${API_BASE}/graph/relations/${id}`);
      return true;
    } catch (error) {
      console.error('删除关系失败:', error);
      return false;
    }
  },

  /**
   * 获取智能推荐
   */
  async getRecommendations(entityId?: string, limit: number = 5): Promise<Recommendation[]> {
    try {
      const params = entityId ? { entity_id: entityId, limit } : { limit };
      const response = await axios.get(`${API_BASE}/graph/recommendations`, { params });
      return response.data.recommendations || [];
    } catch (error) {
      console.log('API不可用，使用mock推荐数据');
      return mockRecommendations.slice(0, limit);
    }
  },

  /**
   * 获取操作记录
   */
  async getOperations(limit: number = 20): Promise<GraphOperation[]> {
    try {
      const response = await axios.get(`${API_BASE}/graph/operations`, { params: { limit } });
      return response.data.operations || [];
    } catch (error) {
      console.log('API不可用，使用mock操作记录');
      return mockOperations.slice(0, limit);
    }
  },

  /**
   * 执行图谱查询（Cypher风格）
   */
  async queryGraph(query: string, params?: Record<string, any>): Promise<any> {
    try {
      const response = await axios.post(`${API_BASE}/graph/query`, { query, params });
      return response.data;
    } catch (error) {
      console.error('图谱查询失败:', error);
      return null;
    }
  },

  /**
   * 导入数据
   */
  async importData(data: any[]): Promise<{ success: number; failed: number; errors: string[] }> {
    try {
      const response = await axios.post(`${API_BASE}/graph/import`, { data });
      return response.data;
    } catch (error) {
      console.error('数据导入失败:', error);
      return { success: 0, failed: 0, errors: ['导入失败'] };
    }
  },

  /**
   * 导出数据
   */
  async exportData(format: 'json' | 'csv' | 'cypher' = 'json'): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE}/graph/export`, { 
        params: { format },
        responseType: format === 'json' ? 'json' : 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('数据导出失败:', error);
      return null;
    }
  },
};
