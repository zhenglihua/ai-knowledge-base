// 分类和标签管理 API 服务

import { message } from 'antd';

const API_BASE = 'http://localhost:8888/api';

// 分类相关类型
export interface Category {
  id: string;
  name: string;
  description?: string;
  color: string;
  icon: string;
  sort_order: number;
  is_preset: boolean;
  document_count: number;
  created_at: string;
}

export interface CreateCategoryRequest {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order?: number;
}

export interface UpdateCategoryRequest {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order?: number;
}

// 标签相关类型
export interface Tag {
  id: string;
  name: string;
  tag_type: string;
  description?: string;
  color: string;
  usage_count: number;
  created_at: string;
}

export interface CreateTagRequest {
  name: string;
  tag_type?: string;
  description?: string;
  color?: string;
}

// 分类结果类型
export interface ClassificationResult {
  document_id: string;
  suggested_category: string;
  confidence: number;
  reason: string;
  tags: Array<{
    tag: string;
    type: string;
    confidence: number;
  }>;
  applied: boolean;
}

export interface ExtractedTag {
  tag: string;
  type: string;
  confidence: number;
}

// 预设分类配置
export const PRESET_CATEGORIES = [
  { id: 'process', name: '工艺文档', color: 'blue', icon: '⚙️' },
  { id: 'equipment', name: '设备文档', color: 'green', icon: '🔧' },
  { id: 'cim', name: 'CIM系统', color: 'purple', icon: '💻' },
  { id: 'quality', name: '质量管控', color: 'orange', icon: '📊' },
  { id: 'production', name: '生产管理', color: 'cyan', icon: '🏭' },
  { id: 'safety', name: '安全环保', color: 'red', icon: '🛡️' },
  { id: 'other', name: '其他文档', color: 'default', icon: '📄' },
];

// 分类颜色映射
export const CATEGORY_COLORS: Record<string, string> = {
  '工艺文档': 'blue',
  '设备文档': 'green',
  'CIM系统': 'purple',
  '质量管控': 'orange',
  '生产管理': 'cyan',
  '安全环保': 'red',
  '其他文档': 'default',
  '未分类': 'default',
};

// 分类图标映射
export const CATEGORY_ICONS: Record<string, string> = {
  '工艺文档': '⚙️',
  '设备文档': '🔧',
  'CIM系统': '💻',
  '质量管控': '📊',
  '生产管理': '🏭',
  '安全环保': '🛡️',
  '其他文档': '📄',
  '未分类': '📄',
};

// 获取分类颜色
export const getCategoryColor = (categoryName: string): string => {
  return CATEGORY_COLORS[categoryName] || 'default';
};

// 获取分类图标
export const getCategoryIcon = (categoryName: string): string => {
  return CATEGORY_ICONS[categoryName] || '📄';
};

// ==================== 分类管理 API ====================

// 获取所有分类
export const getCategories = async (): Promise<Category[]> => {
  const response = await fetch(`${API_BASE}/categories`);
  if (!response.ok) {
    throw new Error('获取分类列表失败');
  }
  return response.json();
};

// 创建分类
export const createCategory = async (data: CreateCategoryRequest): Promise<Category> => {
  const response = await fetch(`${API_BASE}/categories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '创建分类失败');
  }
  return response.json();
};

// 更新分类
export const updateCategory = async (id: string, data: UpdateCategoryRequest): Promise<Category> => {
  const response = await fetch(`${API_BASE}/categories/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '更新分类失败');
  }
  return response.json();
};

// 删除分类
export const deleteCategory = async (id: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/categories/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '删除分类失败');
  }
};

// ==================== 标签管理 API ====================

// 获取所有标签
export const getTags = async (tagType?: string): Promise<Tag[]> => {
  const url = tagType 
    ? `${API_BASE}/categories/tags/all?tag_type=${tagType}`
    : `${API_BASE}/categories/tags/all`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('获取标签列表失败');
  }
  return response.json();
};

// 获取热门标签
export const getPopularTags = async (limit: number = 20): Promise<Tag[]> => {
  const response = await fetch(`${API_BASE}/categories/tags/popular?limit=${limit}`);
  if (!response.ok) {
    throw new Error('获取热门标签失败');
  }
  return response.json();
};

// 创建标签
export const createTag = async (data: CreateTagRequest): Promise<Tag> => {
  const response = await fetch(`${API_BASE}/categories/tags`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '创建标签失败');
  }
  return response.json();
};

// 删除标签
export const deleteTag = async (id: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/categories/tags/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '删除标签失败');
  }
};

// ==================== 智能分类 API ====================

// 智能分类文档
export const classifyDocument = async (
  documentId: string, 
  autoApply: boolean = false
): Promise<ClassificationResult> => {
  const response = await fetch(`${API_BASE}/categories/classify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      auto_apply: autoApply,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '分类文档失败');
  }
  return response.json();
};

// 批量分类文档
export const batchClassifyDocuments = async (
  documentIds: string[],
  autoApply: boolean = false
): Promise<any> => {
  const response = await fetch(`${API_BASE}/categories/classify/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_ids: documentIds,
      auto_apply: autoApply,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '批量分类失败');
  }
  return response.json();
};

// 提取文档标签（不应用）
export const extractDocumentTags = async (documentId: string): Promise<any> => {
  const response = await fetch(`${API_BASE}/categories/extract-tags?document_id=${documentId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '提取标签失败');
  }
  return response.json();
};

// ==================== 文档标签管理 API ====================

// 获取文档的标签
export const getDocumentTags = async (documentId: string): Promise<any[]> => {
  const response = await fetch(`${API_BASE}/categories/documents/${documentId}/tags`);
  if (!response.ok) {
    throw new Error('获取文档标签失败');
  }
  return response.json();
};

// 为文档添加标签
export const addTagToDocument = async (documentId: string, tagId: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/categories/documents/${documentId}/tags?tag_id=${tagId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '添加标签失败');
  }
};

// 从文档移除标签
export const removeTagFromDocument = async (documentId: string, tagId: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/categories/documents/${documentId}/tags/${tagId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '移除标签失败');
  }
};

// ==================== 预设配置 API ====================

// 获取预设分类
export const getPresetCategories = async (): Promise<any[]> => {
  const response = await fetch(`${API_BASE}/categories/preset/list`);
  if (!response.ok) {
    throw new Error('获取预设分类失败');
  }
  return response.json();
};