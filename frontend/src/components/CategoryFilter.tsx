import React, { useState, useEffect } from 'react';
import {
  Card, Tag, Space, Input, Select, Button, Badge, 
  Collapse, Tooltip, Checkbox, Empty, Typography
} from 'antd';
import {
  FilterOutlined, ReloadOutlined, TagsOutlined,
  ClearOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import {
  Category, Tag as TagType, getCategories, getTags, getPopularTags
} from '../services/categoryService';

const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;
const { Text } = Typography;

export interface FilterState {
  categories: string[];
  tags: string[];
  searchText: string;
  fileType: string | null;
}

interface CategoryFilterProps {
  onFilterChange: (filters: FilterState) => void;
  onAutoClassify?: () => void;
  showAutoClassify?: boolean;
}

const CategoryFilter: React.FC<CategoryFilterProps> = ({
  onFilterChange,
  onAutoClassify,
  showAutoClassify = false
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<TagType[]>([]);
  const [popularTags, setPopularTags] = useState<TagType[]>([]);
  const [loading, setLoading] = useState(false);
  
  // 筛选状态
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [searchText, setSearchText] = useState('');
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // 当筛选条件变化时通知父组件
    onFilterChange({
      categories: selectedCategories,
      tags: selectedTags,
      searchText,
      fileType: selectedFileType
    });
  }, [selectedCategories, selectedTags, searchText, selectedFileType]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cats, tagsData, popular] = await Promise.all([
        getCategories(),
        getTags(),
        getPopularTags(10)
      ]);
      setCategories(cats);
      setTags(tagsData);
      setPopularTags(popular);
    } catch (error) {
      console.error('加载筛选数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (categoryName: string) => {
    setSelectedCategories(prev => {
      if (prev.includes(categoryName)) {
        return prev.filter(c => c !== categoryName);
      }
      return [...prev, categoryName];
    });
  };

  const handleTagToggle = (tagName: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tagName)) {
        return prev.filter(t => t !== tagName);
      }
      return [...prev, tagName];
    });
  };

  const handleClearFilters = () => {
    setSelectedCategories([]);
    setSelectedTags([]);
    setSearchText('');
    setSelectedFileType(null);
  };

  const hasActiveFilters = selectedCategories.length > 0 || 
                          selectedTags.length > 0 || 
                          searchText || 
                          selectedFileType;

  // 获取标签颜色
  const getTagColor = (tagType: string): string => {
    const colorMap: Record<string, string> = {
      'equipment': 'blue',
      'process': 'green',
      'parameter': 'orange',
      'material': 'purple',
      'custom': 'default'
    };
    return colorMap[tagType] || 'default';
  };

  return (
    <Card 
      size="small" 
      title={
        <Space>
          <FilterOutlined />
          <span>筛选条件</span>
          {hasActiveFilters && (
            <Badge count={selectedCategories.length + selectedTags.length + (searchText ? 1 : 0)} />
          )}
        </Space>
      }
      extra={
        <Space>
          {showAutoClassify && onAutoClassify && (
            <Tooltip title="智能分类所有未分类文档">
              <Button 
                size="small" 
                icon={<ThunderboltOutlined />}
                onClick={onAutoClassify}
              >
                智能分类
              </Button>
            </Tooltip>
          )}
          {hasActiveFilters && (
            <Button 
              size="small" 
              icon={<ClearOutlined />}
              onClick={handleClearFilters}
            >
              清除筛选
            </Button>
          )}
          <Button 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={loadData}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 搜索框 */}
        <Search
          placeholder="搜索文档名称..."
          allowClear
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: '100%' }}
        />

        {/* 文件类型筛选 */}
        <Select
          placeholder="文件类型"
          allowClear
          style={{ width: '100%' }}
          value={selectedFileType}
          onChange={setSelectedFileType}
        >
          <Option value="pdf">PDF</Option>
          <Option value="doc">Word</Option>
          <Option value="docx">Word (docx)</Option>
          <Option value="txt">文本</Option>
        </Select>

        <Collapse ghost defaultActiveKey={['categories', 'tags']}>
          {/* 分类筛选 */}
          <Panel 
            header={
              <Space>
                <span>📁 分类</span>
                {selectedCategories.length > 0 && (
                  <Tag>{selectedCategories.length}</Tag>
                )}
              </Space>
            } 
            key="categories"
          >
            <Space wrap size="small">
              {categories.length === 0 ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分类" />
              ) : (
                categories.map(cat => (
                  <Tag
                    key={cat.id}
                    color={selectedCategories.includes(cat.name) ? cat.color : 'default'}
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleCategoryToggle(cat.name)}
                  >
                    {cat.icon} {cat.name}
                    {cat.document_count > 0 && (
                      <span style={{ marginLeft: 4, opacity: 0.7 }}>
                        ({cat.document_count})
                      </span>
                    )}
                  </Tag>
                ))
              )}
            </Space>
          </Panel>

          {/* 热门标签 */}
          <Panel 
            header={
              <Space>
                <span>🔥 热门标签</span>
                {selectedTags.length > 0 && (
                  <Tag>{selectedTags.length}</Tag>
                )}
              </Space>
            } 
            key="tags"
          >
            <Space wrap size="small">
              {popularTags.length === 0 ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无标签" />
              ) : (
                popularTags.map(tag => (
                  <Tag
                    key={tag.id}
                    color={selectedTags.includes(tag.name) ? getTagColor(tag.tag_type) : 'default'}
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleTagToggle(tag.name)}
                  >
                    {tag.name}
                    <span style={{ marginLeft: 4, opacity: 0.7 }}>
                      ({tag.usage_count})
                    </span>
                  </Tag>
                ))
              )}
            </Space>          </Panel>

          {/* 所有标签 */}
          {tags.length > 10 && (
            <Panel header={<span>🏷️ 所有标签 ({tags.length})</span>} key="all-tags">
              <Space wrap size="small">
                {tags.map(tag => (
                  <Tag
                    key={tag.id}
                    color={selectedTags.includes(tag.name) ? getTagColor(tag.tag_type) : 'default'}
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleTagToggle(tag.name)}
                  >
                    {tag.name}
                  </Tag>
                ))}
              </Space>
            </Panel>
          )}
        </Collapse>

        {/* 已选条件汇总 */}
        {hasActiveFilters && (
          <div style={{ 
            padding: '8px 12px', 
            background: '#f6ffed', 
            borderRadius: 6,
            border: '1px solid #b7eb8f'
          }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Text type="secondary" style={{ fontSize: 12 }}>已选条件：</Text>
              <Space wrap size="small">
                {selectedCategories.map(cat => (
                  <Tag 
                    key={cat} 
                    closable 
                    onClose={() => handleCategoryToggle(cat)}
                  >
                    📁 {cat}
                  </Tag>
                ))}
                {selectedTags.map(tag => (
                  <Tag 
                    key={tag} 
                    closable 
                    onClose={() => handleTagToggle(tag)}
                  >
                    🏷️ {tag}
                  </Tag>
                ))}
                {searchText && (
                  <Tag 
                    closable 
                    onClose={() => setSearchText('')}
                  >
                    🔍 {searchText}
                  </Tag>
                )}
              </Space>
            </Space>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default CategoryFilter;