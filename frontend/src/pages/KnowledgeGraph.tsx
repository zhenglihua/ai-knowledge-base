import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Typography, Tabs, Button, Space, message } from 'antd';
import {
  ShareAltOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  KnowledgeGraphVisualizer,
  EntityDetailCard,
  RelationList,
  RecommendationPanel,
} from '../components/knowledgeGraph';
import { knowledgeGraphService } from '../services/knowledgeGraphService';
import { 
  GraphData, 
  GraphNode, 
  Entity, 
  Relation, 
  Recommendation 
} from '../types/knowledgeGraph';
import './KnowledgeGraph.css';

const { Title } = Typography;
const { TabPane } = Tabs;

const KnowledgeGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [relationsLoading, setRelationsLoading] = useState(false);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);

  // 加载图谱数据
  const loadGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await knowledgeGraphService.getGraphData();
      setGraphData(data);
    } catch (error) {
      message.error('加载知识图谱失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  // 加载选中实体的详情和关系
  const handleNodeClick = useCallback(async (node: GraphNode) => {
    if (!node.data) return;

    setSelectedEntity(node.data);
    
    // 加载关系
    setRelationsLoading(true);
    try {
      const entityRelations = await knowledgeGraphService.getEntityRelations(node.id);
      setRelations(entityRelations);
    } catch (error) {
      console.error('加载关系失败:', error);
    } finally {
      setRelationsLoading(false);
    }

    // 加载推荐
    setRecommendationsLoading(true);
    try {
      const recs = await knowledgeGraphService.getRecommendations(node.id, 5);
      setRecommendations(recs);
    } catch (error) {
      console.error('加载推荐失败:', error);
    } finally {
      setRecommendationsLoading(false);
    }
  }, []);

  // 双击节点展开更多关系
  const handleNodeDoubleClick = useCallback(async (node: GraphNode) => {
    setLoading(true);
    try {
      const expandedData = await knowledgeGraphService.getGraphData(node.id, 3);
      setGraphData(expandedData);
    } catch (error) {
      message.error('展开关系失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 点击推荐项
  const handleRecommendationClick = useCallback((rec: Recommendation) => {
    if (rec.type === 'entity' && rec.data) {
      setSelectedEntity(rec.data as Entity);
    }
  }, []);

  return (
    <div className="knowledge-graph-page">
      <div className="page-header">
        <Title level={2}>
          <Space>
            <ShareAltOutlined />
            知识图谱
          </Space>
        </Title>
        <Space>
          <Button icon={<SearchOutlined />} onClick={() => {}}>
            搜索实体
          </Button>
          <Button type="primary" icon={<NodeIndexOutlined />} onClick={loadGraphData}>
            刷新图谱
          </Button>
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <KnowledgeGraphVisualizer
            data={graphData}
            loading={loading}
            height={700}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
            showToolbar={true}
            showLegend={true}
            interactive={true}
          />
        </Col>

        <Col xs={24} lg={8}>
          <Tabs defaultActiveKey="detail" className="right-panel-tabs">
            <TabPane
              tab={
                <Space>
                  <NodeIndexOutlined />
                  实体详情
                </Space>
              }
              key="detail"
            >
              <EntityDetailCard entity={selectedEntity} />
            </TabPane>

            <TabPane
              tab={
                <Space>
                  <ShareAltOutlined />
                  关系网络
                </Space>
              }
              key="relations"
            >
              <RelationList
                relations={relations}
                currentEntityId={selectedEntity?.id || ''}
                entities={graphData.nodes.reduce((acc, node) => ({
                  ...acc,
                  [node.id]: node.data,
                }), {})}
                loading={relationsLoading}
              />
            </TabPane>

            <TabPane
              tab={
                <Space>
                  <ThunderboltOutlined />
                  智能推荐
                </Space>
              }
              key="recommendations"
            >
              <RecommendationPanel
                recommendations={recommendations}
                loading={recommendationsLoading}
                onItemClick={handleRecommendationClick}
              />
            </TabPane>
          </Tabs>
        </Col>
      </Row>
    </div>
  );
};

export default KnowledgeGraph;
