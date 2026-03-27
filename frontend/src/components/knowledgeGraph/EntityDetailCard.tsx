import React from 'react';
import { Card, Tag, Descriptions, Space, Typography, Badge, Divider } from 'antd';
import { 
  DatabaseOutlined, 
  TagOutlined, 
  ClockCircleOutlined,
  FileTextOutlined,
  LinkOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import { Entity, EntityType } from '../../types/knowledgeGraph';
import './EntityDetailCard.css';

const { Title, Text, Paragraph } = Typography;

interface EntityDetailCardProps {
  entity: Entity | null;
  loading?: boolean;
  extra?: React.ReactNode;
}

// 实体类型配置
const typeConfig: Record<EntityType, { color: string; icon: React.ReactNode; label: string }> = {
  equipment: { 
    color: '#1677ff', 
    icon: <DatabaseOutlined />, 
    label: '设备' 
  },
  process: { 
    color: '#52c41a', 
    icon: <NodeIndexOutlined />, 
    label: '工艺' 
  },
  material: { 
    color: '#faad14', 
    icon: <DatabaseOutlined />, 
    label: '材料' 
  },
  parameter: { 
    color: '#722ed1', 
    icon: <TagOutlined />, 
    label: '参数' 
  },
  document: { 
    color: '#eb2f96', 
    icon: <FileTextOutlined />, 
    label: '文档' 
  },
  person: { 
    color: '#13c2c2', 
    icon: <DatabaseOutlined />, 
    label: '人员' 
  },
  organization: { 
    color: '#fa8c16', 
    icon: <DatabaseOutlined />, 
    label: '组织' 
  },
  location: { 
    color: '#2f54eb', 
    icon: <LinkOutlined />, 
    label: '位置' 
  },
};

const EntityDetailCard: React.FC<EntityDetailCardProps> = ({ entity, loading, extra }) => {
  if (!entity) {
    return (
      <Card className="entity-detail-card empty">
        <div className="entity-empty">
          <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <Text type="secondary" style={{ marginTop: 16 }}>
            点击图谱中的节点查看详情
          </Text>
        </div>
      </Card>
    );
  }

  const config = typeConfig[entity.type] || typeConfig.equipment;

  return (
    <Card 
      className="entity-detail-card"
      loading={loading}
      extra={extra}
      title={
        <Space>
          <Badge 
            count={config.icon} 
            style={{ backgroundColor: config.color }}
          />
          <span>{entity.name}</span>
        </Space>
      }
    >
      <div className="entity-header">
        <Tag color={config.color} className="entity-type-tag">
          {config.label}
        </Tag>
        {entity.confidence && (
          <Badge 
            count={`置信度: ${(entity.confidence * 100).toFixed(0)}%`}
            style={{ backgroundColor: entity.confidence > 0.8 ? '#52c41a' : '#faad14' }}
          />
        )}
      </div>

      {entity.description && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <Paragraph className="entity-description">
            {entity.description}
          </Paragraph>
        </>
      )}

      <Divider style={{ margin: '16px 0' }} />

      <Descriptions column={1} size="small" className="entity-descriptions">
        {entity.source && (
          <Descriptions.Item label="数据来源">
            <Text type="secondary">{entity.source}</Text>
          </Descriptions.Item>
        )}
        {entity.created_at && (
          <Descriptions.Item label={
            <Space>
              <ClockCircleOutlined />
              创建时间
            </Space>
          }>
            <Text type="secondary">
              {new Date(entity.created_at).toLocaleString('zh-CN')}
            </Text>
          </Descriptions.Item>
        )}
        {entity.updated_at && entity.updated_at !== entity.created_at && (
          <Descriptions.Item label="更新时间">
            <Text type="secondary">
              {new Date(entity.updated_at).toLocaleString('zh-CN')}
            </Text>
          </Descriptions.Item>
        )}
      </Descriptions>

      {entity.tags && entity.tags.length > 0 && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <div className="entity-tags">
            <Text type="secondary" className="tags-label">
              <TagOutlined /> 标签
            </Text>
            <Space size={[8, 8]} wrap>
              {entity.tags.map((tag, index) => (
                <Tag key={index} color="blue" className="entity-tag">
                  {tag}
                </Tag>
              ))}
            </Space>
          </div>
        </>
      )}

      {entity.properties && Object.keys(entity.properties).length > 0 && (
        <>
          <Divider style={{ margin: '16px 0' }} />
          <div className="entity-properties">
            <Title level={5}>属性信息</Title>
            <Descriptions column={1} size="small" bordered>
              {Object.entries(entity.properties).map(([key, value]) => (
                <Descriptions.Item key={key} label={key}>
                  {typeof value === 'object' 
                    ? JSON.stringify(value) 
                    : String(value)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </div>
        </>
      )}
    </Card>
  );
};

export default EntityDetailCard;
