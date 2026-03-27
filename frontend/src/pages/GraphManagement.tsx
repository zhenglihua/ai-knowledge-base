import React, { useState, useEffect, useCallback } from 'react';
import {
  Row,
  Col,
  Typography,
  Card,
  Statistic,
  Table,
  Button,
  Space,
  Tag,
  Timeline,
  message,
  Upload,
  Tabs,
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  ShareAltOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  HistoryOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { knowledgeGraphService } from '../services/knowledgeGraphService';
import { GraphStats, GraphOperation, EntityType, RelationType } from '../types/knowledgeGraph';
import './GraphManagement.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const GraphManagement: React.FC = () => {
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [operations, setOperations] = useState<GraphOperation[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载统计数据
  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const data = await knowledgeGraphService.getStats();
      setStats(data);
    } catch (error) {
      message.error('加载统计信息失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载操作记录
  const loadOperations = useCallback(async () => {
    try {
      const data = await knowledgeGraphService.getOperations(20);
      setOperations(data);
    } catch (error) {
      console.error('加载操作记录失败:', error);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadStats();
    loadOperations();
  }, [loadStats, loadOperations]);

  // 处理导入
  const handleImport = async (file: File) => {
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const content = e.target?.result as string;
        const data = JSON.parse(content);
        const result = await knowledgeGraphService.importData(data);
        message.success(`导入成功: ${result.success} 条, 失败: ${result.failed} 条`);
        loadStats();
      };
      reader.readAsText(file);
    } catch (error) {
      message.error('导入失败');
      console.error(error);
    }
    return false;
  };

  // 处理导出
  const handleExport = async () => {
    try {
      const data = await knowledgeGraphService.exportData('json');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-graph-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
      console.error(error);
    }
  };

  // 获取实体类型颜色
  const getEntityTypeColor = (type: EntityType): string => {
    const colors: Record<EntityType, string> = {
      equipment: '#1677ff',
      process: '#52c41a',
      material: '#faad14',
      parameter: '#722ed1',
      document: '#eb2f96',
      person: '#13c2c2',
      organization: '#fa8c16',
      location: '#2f54eb',
    };
    return colors[type] || '#8c8c8c';
  };

  // 获取实体类型标签
  const getEntityTypeLabel = (type: EntityType): string => {
    const labels: Record<EntityType, string> = {
      equipment: '设备',
      process: '工艺',
      material: '材料',
      parameter: '参数',
      document: '文档',
      person: '人员',
      organization: '组织',
      location: '位置',
    };
    return labels[type] || type;
  };

  // 统计卡片数据
  const statCards = [
    {
      title: '实体总数',
      value: stats?.total_entities || 0,
      icon: <DatabaseOutlined />,
      color: '#1677ff',
    },
    {
      title: '关系总数',
      value: stats?.total_relations || 0,
      icon: <ShareAltOutlined />,
      color: '#52c41a',
    },
  ];

  return (
    <div className="graph-management-page">
      <div className="page-header">
        <Title level={2}>
          <DatabaseOutlined /> 图谱管理
        </Title>
        <Space>
          <Upload beforeUpload={handleImport} showUploadList={false}>
            <Button icon={<UploadOutlined />}>导入数据</Button>
          </Upload>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出数据
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="overview">
        <TabPane
          tab={
            <Space>
              <BarChartOutlined />
              概览
            </Space>
          }
          key="overview"
        >
          <Row gutter={[24, 24]}>
            {statCards.map((card, index) => (
              <Col xs={24} sm={12} lg={6} key={index}>
                <Card className="stat-card">
                  <Statistic
                    title={card.title}
                    value={card.value}
                    valueStyle={{ color: card.color }}
                    prefix={card.icon}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="实体类型分布" className="distribution-card">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {stats?.entity_types &&
                    Object.entries(stats.entity_types).map(([type, count]) => (
                      <div key={type} className="distribution-item">
                        <Tag color={getEntityTypeColor(type as EntityType)}>
                          {getEntityTypeLabel(type as EntityType)}
                        </Tag>
                        <div className="distribution-bar">
                          <div
                            className="distribution-fill"
                            style={{
                              width: `${(count / (stats.total_entities || 1)) * 100}%`,
                              backgroundColor: getEntityTypeColor(type as EntityType),
                            }}
                          />
                        </div>
                        <span className="distribution-count">{count}</span>
                      </div>
                    ))}
                </Space>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="最近操作记录" className="operations-card">
                <Timeline
                  items={operations.map((op) => ({
                    key: op.id,
                    color: op.type === 'create' ? 'green' : op.type === 'delete' ? 'red' : 'blue',
                    dot: <HistoryOutlined />,
                    children: (
                      <div className="operation-item">
                        <Text strong>{op.operator}</Text>
                        <Text type="secondary">
                          {op.type === 'create'
                            ? ' 创建了 '
                            : op.type === 'update'
                            ? ' 更新了 '
                            : op.type === 'delete'
                            ? ' 删除了 '
                            : ' 操作了 '}
                          <Tag>
                            {op.target_type === 'entity' ? '实体' : '关系'}
                          </Tag>
                          <Text>{op.target_name}</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            <ClockCircleOutlined />{' '}
                            {new Date(op.operation_time).toLocaleString('zh-CN')}
                          </Text>
                        </Text>
                      </div>
                    ),
                  }))}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane
          tab={
            <Space>
              <HistoryOutlined />
              操作日志
            </Space>
          }
          key="logs"
        >
          <Card>
            <Table
              dataSource={operations}
              rowKey="id"
              columns={[
                {
                  title: '操作类型',
                  dataIndex: 'type',
                  key: 'type',
                  render: (type: string) => (
                    <Tag
                      color={
                        type === 'create'
                          ? 'green'
                          : type === 'update'
                          ? 'blue'
                          : type === 'delete'
                          ? 'red'
                          : 'default'
                      }
                    >
                      {type === 'create'
                        ? '创建'
                        : type === 'update'
                        ? '更新'
                        : type === 'delete'
                        ? '删除'
                        : type}
                    </Tag>
                  ),
                },
                {
                  title: '目标类型',
                  dataIndex: 'target_type',
                  key: 'target_type',
                  render: (type: string) => (
                    <Tag>{type === 'entity' ? '实体' : '关系'}</Tag>
                  ),
                },
                {
                  title: '目标名称',
                  dataIndex: 'target_name',
                  key: 'target_name',
                },
                {
                  title: '操作人',
                  dataIndex: 'operator',
                  key: 'operator',
                },
                {
                  title: '操作时间',
                  dataIndex: 'operation_time',
                  key: 'operation_time',
                  render: (time: string) =>
                    new Date(time).toLocaleString('zh-CN'),
                },
              ]}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default GraphManagement;
