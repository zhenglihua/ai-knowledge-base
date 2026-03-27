import React, { useState, useCallback } from 'react';
import { Row, Col, Typography, Card, message, Drawer, Button } from 'antd';
import {
  SearchOutlined,
  DatabaseOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import {
  EntitySearch,
  EntityDetailCard,
  KnowledgeGraphVisualizer,
  RelationList,
} from '../components/knowledgeGraph';
import { knowledgeGraphService } from '../services/knowledgeGraphService';
import {
  Entity,
  EntityType,
  EntitySearchResult,
  GraphData,
  Relation,
} from '../types/knowledgeGraph';
import './EntitySearchPage.css';

const { Title } = Typography;

const EntitySearchPage: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [relations, setRelations] = useState<Relation[]>([]);
  const [loading, setLoading] = useState(false);

  // 搜索实体
  const handleSearch = useCallback(async (
    keyword: string,
    type?: EntityType
  ): Promise<EntitySearchResult> => {
    const result = await knowledgeGraphService.searchEntities({
      keyword,
      type,
      page: 1,
      limit: 20,
    });
    return result;
  }, []);

  // 点击实体
  const handleEntityClick = useCallback(async (entity: Entity) => {
    setSelectedEntity(entity);
    setDrawerVisible(true);

    // 加载实体关系图谱
    setLoading(true);
    try {
      const data = await knowledgeGraphService.getGraphData(entity.id, 2);
      setGraphData(data);

      const entityRelations = await knowledgeGraphService.getEntityRelations(entity.id);
      setRelations(entityRelations);
    } catch (error) {
      message.error('加载实体关系失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 关闭抽屉
  const handleCloseDrawer = () => {
    setDrawerVisible(false);
    setSelectedEntity(null);
    setGraphData({ nodes: [], edges: [] });
    setRelations([]);
  };

  return (
    <div className="entity-search-page">
      <div className="page-header">
        <Title level={2}>
          <SearchOutlined /> 实体搜索
        </Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <EntitySearch
              onSearch={handleSearch}
              onEntityClick={handleEntityClick}
              placeholder="搜索设备、工艺、材料等实体..."
              showFilter={true}
            />
          </Card>
        </Col>
      </Row>

      {/* 实体详情抽屉 */}
      <Drawer
        title={
          <span>
            <DatabaseOutlined /> 实体详情
          </span>
        }
        placement="right"
        onClose={handleCloseDrawer}
        open={drawerVisible}
        width={800}
        bodyStyle={{ padding: 0 }}
      >
        {selectedEntity && (
          <div className="entity-detail-container">
            <EntityDetailCard entity={selectedEntity} />

            <Card
              title={<span><ShareAltOutlined /> 关系图谱</span>}
              style={{ marginTop: 16 }}
              bodyStyle={{ padding: 0 }}
            >
              <KnowledgeGraphVisualizer
                data={graphData}
                loading={loading}
                height={350}
                centerNodeId={selectedEntity.id}
                showToolbar={true}
                showLegend={false}
                interactive={true}
              />
            </Card>

            <Card
              title={<span><ShareAltOutlined /> 关联关系</span>}
              style={{ marginTop: 16 }}
            >
              <RelationList
                relations={relations}
                currentEntityId={selectedEntity.id}
                entities={graphData.nodes.reduce((acc, node) => ({
                  ...acc,
                  [node.id]: node.data,
                }), {})}
                loading={loading}
              />
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default EntitySearchPage;
