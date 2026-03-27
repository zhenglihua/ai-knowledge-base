import React from 'react';
import { Card, List, Tag, Space, Typography, Empty, Badge, Tooltip, Progress } from 'antd';
import {
  ThunderboltOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  StarOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { Recommendation, EntityType } from '../../types/knowledgeGraph';
import './RecommendationPanel.css';

const { Text, Paragraph } = Typography;

interface RecommendationPanelProps {
  recommendations: Recommendation[];
  loading?: boolean;
  onItemClick?: (item: Recommendation) => void;
}

// 类型图标映射
const typeIcons: Record<EntityType | 'document' | 'relation', React.ReactNode> = {
  equipment: <NodeIndexOutlined />,
  process: <NodeIndexOutlined />,
  material: <NodeIndexOutlined />,
  parameter: <NodeIndexOutlined />,
  document: <FileTextOutlined />,
  person: <NodeIndexOutlined />,
  organization: <NodeIndexOutlined />,
  location: <NodeIndexOutlined />,
  relation: <NodeIndexOutlined />,
};

// 类型颜色映射
const typeColors: Record<EntityType | 'document' | 'relation', string> = {
  equipment: '#1677ff',
  process: '#52c41a',
  material: '#faad14',
  parameter: '#722ed1',
  document: '#eb2f96',
  person: '#13c2c2',
  organization: '#fa8c16',
  location: '#2f54eb',
  relation: '#8c8c8c',
};

// 推荐原因映射
const reasonLabels: Record<string, string> = {
  similar_content: '内容相似',
  co_occurrence: '共同出现',
  shared_neighbors: '共同关联',
  user_interest: '兴趣推荐',
  trending: '热门推荐',
  semantic_match: '语义匹配',
};

const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  recommendations,
  loading,
  onItemClick,
}) => {
  if (recommendations.length === 0 && !loading) {
    return (
      <Card className="recommendation-panel empty">
        <Empty
          description="暂无推荐内容"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const getRecommendationIcon = (rec: Recommendation) => {
    if (rec.type === 'entity' && rec.data?.type) {
      return typeIcons[rec.data.type as EntityType] || typeIcons.document;
    }
    if (rec.type === 'relation') {
      return typeIcons.relation;
    }
    return typeIcons.document;
  };

  const getRecommendationColor = (rec: Recommendation) => {
    if (rec.type === 'entity' && rec.data?.type) {
      return typeColors[rec.data.type as EntityType] || typeColors.document;
    }
    if (rec.type === 'relation') {
      return typeColors.relation;
    }
    return typeColors.document;
  };

  return (
    <Card
      className="recommendation-panel"
      title={
        <Space>
          <ThunderboltOutlined style={{ color: '#faad14' }} />
          <span>智能推荐</span>
          {recommendations.length > 0 && (
            <Badge count={recommendations.length} style={{ backgroundColor: '#faad14' }} />
          )}
        </Space>
      }
      loading={loading}
    >
      <List
        dataSource={recommendations}
        renderItem={(item) => (
          <List.Item
            className="recommendation-item"
            onClick={() => onItemClick?.(item)}
            style={{ cursor: onItemClick ? 'pointer' : 'default' }}
          >
            <List.Item.Meta
              avatar={
                <div
                  className="recommendation-icon"
                  style={{
                    backgroundColor: `${getRecommendationColor(item)}15`,
                    color: getRecommendationColor(item),
                  }}
                >
                  {getRecommendationIcon(item)}
                </div>
              }
              title={
                <Space align="center">
                  <Text strong>{item.title}</Text>
                  <Tooltip title={`推荐原因: ${reasonLabels[item.reason] || item.reason}`}>
                    <Tag className="reason-tag">
                      {reasonLabels[item.reason] || item.reason}
                    </Tag>
                  </Tooltip>
                </Space>
              }
              description={
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <Paragraph
                    ellipsis={{ rows: 2 }}
                    style={{ margin: 0, fontSize: 12, color: '#8c8c8c' }}
                  >
                    {item.description}
                  </Paragraph>
                  <div className="recommendation-meta">
                    <Space>
                      <StarOutlined style={{ color: '#faad14', fontSize: 12 }} />
                      <Progress
                        percent={Math.round(item.score * 100)}
                        size="small"
                        style={{ width: 60 }}
                        showInfo={false}
                        strokeColor="#faad14"
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {Math.round(item.score * 100)}% 匹配
                      </Text>
                    </Space>
                    <Space size={8}>
                      {item.type === 'document' && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          <EyeOutlined /> 文档
                        </Text>
                      )}
                    </Space>
                  </div>
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default RecommendationPanel;
