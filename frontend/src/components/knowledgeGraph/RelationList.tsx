import React from 'react';
import { Card, List, Tag, Space, Typography, Empty, Badge } from 'antd';
import {
  ArrowRightOutlined,
  LinkOutlined,
  NodeIndexOutlined,
  SwapRightOutlined,
} from '@ant-design/icons';
import { Relation, RelationType, Entity } from '../../types/knowledgeGraph';
import './RelationList.css';

const { Text } = Typography;

interface RelationListProps {
  relations: Relation[];
  currentEntityId: string;
  entities: Record<string, Entity>;
  loading?: boolean;
  onEntityClick?: (entityId: string) => void;
}

// 关系类型配置
const relationConfig: Record<RelationType, { color: string; label: string; icon: React.ReactNode }> = {
  uses: { color: '#1677ff', label: '使用', icon: <ArrowRightOutlined /> },
  produces: { color: '#52c41a', label: '产出', icon: <ArrowRightOutlined /> },
  requires: { color: '#faad14', label: '需要', icon: <ArrowRightOutlined /> },
  part_of: { color: '#722ed1', label: '属于', icon: <ArrowRightOutlined /> },
  located_at: { color: '#13c2c2', label: '位于', icon: <ArrowRightOutlined /> },
  operated_by: { color: '#eb2f96', label: '操作者', icon: <ArrowRightOutlined /> },
  related_to: { color: '#8c8c8c', label: '相关', icon: <LinkOutlined /> },
  references: { color: '#fa8c16', label: '引用', icon: <ArrowRightOutlined /> },
};

const RelationList: React.FC<RelationListProps> = ({
  relations,
  currentEntityId,
  entities,
  loading,
  onEntityClick,
}) => {
  if (relations.length === 0 && !loading) {
    return (
      <Card className="relation-list-card empty">
        <Empty
          description="暂无关系数据"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  // 分组显示关系
  const incomingRelations = relations.filter(r => r.target_id === currentEntityId);
  const outgoingRelations = relations.filter(r => r.source_id === currentEntityId);

  const renderRelationItem = (relation: Relation, direction: 'in' | 'out') => {
    const config = relationConfig[relation.type] || relationConfig.related_to;
    const isIncoming = direction === 'in';
    const relatedEntityId = isIncoming ? relation.source_id : relation.target_id;
    const relatedEntity = entities[relatedEntityId];

    return (
      <List.Item
        className="relation-item"
        onClick={() => onEntityClick?.(relatedEntityId)}
        style={{ cursor: onEntityClick ? 'pointer' : 'default' }}
      >
        <div className="relation-item-content">
          <Space align="center">
            {isIncoming ? (
              <>
                <Badge
                  count={relatedEntity?.name || relatedEntityId.slice(0, 8)}
                  style={{ backgroundColor: '#f0f0f0', color: '#595959' }}
                />
                <SwapRightOutlined style={{ color: '#8c8c8c' }} />
                <Tag color={config.color} icon={config.icon}>
                  {config.label}
                </Tag>
                <Text type="secondary">当前实体</Text>
              </>
            ) : (
              <>
                <Text type="secondary">当前实体</Text>
                <SwapRightOutlined style={{ color: '#8c8c8c' }} />
                <Tag color={config.color} icon={config.icon}>
                  {config.label}
                </Tag>
                <Badge
                  count={relatedEntity?.name || relatedEntityId.slice(0, 8)}
                  style={{ backgroundColor: '#f0f0f0', color: '#595959' }}
                />
              </>
            )}
          </Space>
          {relation.confidence && (
            <Badge
              count={`${(relation.confidence * 100).toFixed(0)}%`}
              style={{
                backgroundColor: relation.confidence > 0.8 ? '#52c41a' : '#faad14',
                fontSize: '11px',
              }}
            />
          )}
        </div>
      </List.Item>
    );
  };

  return (
    <Card
      className="relation-list-card"
      title={
        <Space>
          <NodeIndexOutlined />
          <span>关系网络</span>
          <Badge count={relations.length} style={{ backgroundColor: '#1677ff' }} />
        </Space>
      }
      loading={loading}
    >
      {incomingRelations.length > 0 && (
        <div className="relation-section">
          <Text type="secondary" className="section-title">
            被引用 ({incomingRelations.length})
          </Text>
          <List
            dataSource={incomingRelations}
            renderItem={(item) => renderRelationItem(item, 'in')}
            size="small"
          />
        </div>
      )}

      {outgoingRelations.length > 0 && (
        <div className="relation-section">
          <Text type="secondary" className="section-title">
            引用 ({outgoingRelations.length})
          </Text>
          <List
            dataSource={outgoingRelations}
            renderItem={(item) => renderRelationItem(item, 'out')}
            size="small"
          />
        </div>
      )}
    </Card>
  );
};

export default RelationList;
