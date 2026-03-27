import React, { useState, useCallback } from 'react';
import { Input, Select, Tag, Space, List, Card, Empty, Typography } from 'antd';
import {
  SearchOutlined,
  NodeIndexOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { Entity, EntityType, EntitySearchResult } from '../../types/knowledgeGraph';
import './EntitySearch.css';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

interface EntitySearchProps {
  onSearch: (keyword: string, type?: EntityType) => Promise<EntitySearchResult>;
  onEntityClick?: (entity: Entity) => void;
  placeholder?: string;
  showFilter?: boolean;
}

// 实体类型配置
const typeConfig: Record<EntityType, { color: string; label: string }> = {
  equipment: { color: '#1677ff', label: '设备' },
  process: { color: '#52c41a', label: '工艺' },
  material: { color: '#faad14', label: '材料' },
  parameter: { color: '#722ed1', label: '参数' },
  document: { color: '#eb2f96', label: '文档' },
  person: { color: '#13c2c2', label: '人员' },
  organization: { color: '#fa8c16', label: '组织' },
  location: { color: '#2f54eb', label: '位置' },
};

const EntitySearch: React.FC<EntitySearchProps> = ({
  onSearch,
  onEntityClick,
  placeholder = '搜索实体...',
  showFilter = true,
}) => {
  const [keyword, setKeyword] = useState('');
  const [selectedType, setSelectedType] = useState<EntityType | undefined>(undefined);
  const [results, setResults] = useState<EntitySearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!keyword.trim()) return;
    
    setLoading(true);
    try {
      const result = await onSearch(keyword, selectedType);
      setResults(result);
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      setLoading(false);
    }
  }, [keyword, selectedType, onSearch]);

  const handleTypeChange = useCallback((value: EntityType | undefined) => {
    setSelectedType(value);
    if (keyword.trim()) {
      handleSearch();
    }
  }, [keyword, handleSearch]);

  return (
    <div className="entity-search">
      <Card className="search-card">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space style={{ width: '100%' }}>
            <Search
              placeholder={placeholder}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
              loading={loading}
              style={{ flex: 1 }}
              size="large"
            />
            {showFilter && (
              <Select
                placeholder={<Space><FilterOutlined /> 类型筛选</Space>}
                value={selectedType}
                onChange={handleTypeChange}
                allowClear
                style={{ width: 150 }}
                size="large"
              >
                {(Object.keys(typeConfig) as EntityType[]).map((type) => (
                  <Option key={type} value={type}>
                    <Tag color={typeConfig[type].color}>{typeConfig[type].label}</Tag>
                  </Option>
                ))}
              </Select>
            )}
          </Space>

          {results && (
            <div className="search-results">
              <div className="search-summary">
                <Text type="secondary">
                  找到 <Text strong>{results.total}</Text> 个结果
                  {selectedType && (
                    <>
                      ，类型: <Tag color={typeConfig[selectedType].color}>
                        {typeConfig[selectedType].label}
                      </Tag>
                    </>
                  )}
                </Text>
              </div>

              {results.entities.length > 0 ? (
                <List
                  dataSource={results.entities}
                  renderItem={(entity) => (
                    <List.Item
                      className="search-result-item"
                      onClick={() => onEntityClick?.(entity)}
                      style={{ cursor: onEntityClick ? 'pointer' : 'default' }}
                    >
                      <List.Item.Meta
                        avatar={
                          <div
                            className="entity-avatar"
                            style={{
                              backgroundColor: `${typeConfig[entity.type].color}15`,
                              color: typeConfig[entity.type].color,
                            }}
                          >
                            <NodeIndexOutlined />
                          </div>
                        }
                        title={
                          <Space>
                            <Text strong>{entity.name}</Text>
                            <Tag color={typeConfig[entity.type].color}>
                              {typeConfig[entity.type].label}
                            </Tag>
                          </Space>
                        }
                        description={
                          entity.description ? (
                            <Text type="secondary" ellipsis>
                              {entity.description}
                            </Text>
                          ) : (
                            <Text type="secondary">暂无描述</Text>
                          )
                        }
                      />
                      {entity.tags && entity.tags.length > 0 && (
                        <div className="entity-tags">
                          <Space size={[4, 4]} wrap>
                            {entity.tags.slice(0, 3).map((tag, index) => (
                              <Tag key={index}>{tag}</Tag>
                            ))}
                            {entity.tags.length > 3 && (
                              <Tag>+{entity.tags.length - 3}</Tag>
                            )}
                          </Space>
                        </div>
                      )}
                    </List.Item>
                  )}
                />
              ) : (
                <Empty
                  description="未找到匹配的实体"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default EntitySearch;
