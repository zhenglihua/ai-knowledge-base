import React, { useEffect, useState } from 'react';
import { 
  Card, Statistic, Row, Col, Typography, List, Tag, Button, 
  Space, Timeline, Avatar, Progress, Badge, Divider, Empty
} from 'antd';
import {
  FileTextOutlined,
  SearchOutlined,
  MessageOutlined,
  DatabaseOutlined,
  RiseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  RobotFilled,
  ThunderboltOutlined,
  ArrowRightOutlined,
  PlusOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/global.css';

const { Title, Text, Paragraph } = Typography;
const API_BASE = 'http://localhost:8888/api';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    documents: 0,
    searches: 128,
    chats: 56,
    storage: 45,
  });
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/documents?limit=5`);
      setStats(prev => ({ ...prev, documents: res.data.total }));
      setRecentDocs(res.data.documents);
    } catch (e) {
      console.log('API未连接');
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: '上传文档',
      desc: '添加新的知识文档',
      icon: <PlusOutlined />,
      color: '#1677ff',
      onClick: () => navigate('/documents'),
    },
    {
      title: '智能搜索',
      desc: '快速查找知识',
      icon: <SearchOutlined />,
      color: '#52c41a',
      onClick: () => navigate('/search'),
    },
    {
      title: 'AI问答',
      desc: '智能问答助手',
      icon: <RobotFilled />,
      color: '#722ed1',
      onClick: () => navigate('/chat'),
    },
  ];

  const activities = [
    {
      title: '上传了《半导体工艺基础》',
      time: '10分钟前',
      icon: <FileTextOutlined style={{ color: '#1677ff' }} />,
    },
    {
      title: '搜索"光刻机故障"',
      time: '30分钟前',
      icon: <SearchOutlined style={{ color: '#52c41a' }} />,
    },
    {
      title: 'AI回答了工艺问题',
      time: '1小时前',
      icon: <RobotFilled style={{ color: '#722ed1' }} />,
    },
  ];

  return (
    <div className="page-enter-active">
      {/* 欢迎区域 */}
      <Card 
        className="gradient-bg-blue hover-card"
        style={{ marginBottom: 24, border: 'none', height: '140px' }}
        bodyStyle={{ padding: '20px 24px', height: '100%' }}
      >
        <Row align="middle" gutter={24} style={{ height: '100%' }}>
          <Col flex="auto">
            <Space direction="vertical" size={8}>
              <Title level={3} style={{ margin: 0, color: '#fff' }}>
                欢迎使用 AI知识库
              </Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.9)', margin: 0, fontSize: 16 }}>
                基于大语言模型的半导体工厂智能知识管理系统
              </Paragraph>
              <Space style={{ marginTop: 16 }}>
                <Button 
                  type="primary" 
                  size="large"
                  icon={<ThunderboltOutlined />}
                  onClick={() => navigate('/chat')}
                  style={{ 
                    background: '#fff', 
                    color: '#1677ff', 
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0 24px',
                    height: '44px',
                    fontWeight: 500,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                  }}
                >
                  开始AI问答
                </Button>
                <Button 
                  ghost 
                  size="large"
                  icon={<ArrowRightOutlined />}
                  onClick={() => navigate('/documents')}
                  style={{ 
                    color: '#fff', 
                    borderColor: 'rgba(255,255,255,0.8)',
                    borderRadius: '8px',
                    padding: '0 24px',
                    height: '44px',
                    fontWeight: 500
                  }}
                >
                  查看文档
                </Button>
              </Space>
            </Space>
          </Col>
          <Col>
            <Avatar 
              size={80} 
              icon={<RobotFilled />}
              style={{ 
                background: 'rgba(255,255,255,0.2)',
                border: '3px solid rgba(255,255,255,0.3)'
              }}
            />
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }} align="stretch">
        <Col xs={24} sm={12} lg={6}>
          <Card className="hover-card" style={{ height: '100%' }}>
            <Statistic
              title={<Space><FileTextOutlined /> 文档总数</Space>}
              value={stats.documents}
              valueStyle={{ color: '#1677ff', fontSize: 32, fontWeight: 600 }}
              suffix={<Tag color="blue">+2 今日</Tag>}
            />
            <Progress percent={65} size="small" showInfo={false} strokeColor="#1677ff" />
            <Text type="secondary" style={{ fontSize: 12 }}>存储空间使用 65%</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="hover-card" style={{ height: '100%' }}>
            <Statistic
              title={<Space><SearchOutlined /> 搜索次数</Space>}
              value={stats.searches}
              valueStyle={{ color: '#52c41a', fontSize: 32, fontWeight: 600 }}
              prefix={<RiseOutlined />}
            />
            <Progress percent={82} size="small" showInfo={false} strokeColor="#52c41a" />
            <Text type="secondary" style={{ fontSize: 12 }}>较上周增长 23%</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="hover-card" style={{ height: '100%' }}>
            <Statistic
              title={<Space><MessageOutlined /> 问答次数</Space>}
              value={stats.chats}
              valueStyle={{ color: '#722ed1', fontSize: 32, fontWeight: 600 }}
            />
            <Progress percent={45} size="small" showInfo={false} strokeColor="#722ed1" />
            <Text type="secondary" style={{ fontSize: 12 }}>今日活跃用户 12人</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="hover-card" style={{ height: '100%' }}>
            <Statistic
              title={<Space><DatabaseOutlined /> 系统状态</Space>}
              value="运行中"
              valueStyle={{ color: '#52c41a', fontSize: 32, fontWeight: 600 }}
            />
            <Progress percent={100} size="small" showInfo={false} strokeColor="#52c41a" />
            <Text type="secondary" style={{ fontSize: 12 }}>所有服务正常运行</Text>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 快捷操作 */}
        <Col xs={24} lg={8}>
          <Card title="快捷操作" className="hover-card">
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              {quickActions.map((action, index) => (
                <Card
                  key={index}
                  className="hover-card"
                  bodyStyle={{ padding: 16 }}
                  style={{ cursor: 'pointer', borderLeft: `4px solid ${action.color}` }}
                  onClick={action.onClick}
                >
                  <Row align="middle" gutter={16}>
                    <Col>
                      <Avatar 
                        size={48} 
                        icon={action.icon}
                        style={{ backgroundColor: `${action.color}15`, color: action.color }}
                      />
                    </Col>
                    <Col flex="auto">
                      <Text strong style={{ fontSize: 16 }}>{action.title}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 13 }}>{action.desc}</Text>
                    </Col>
                    <Col>
                      <ArrowRightOutlined style={{ color: '#bfbfbf' }} />
                    </Col>
                  </Row>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>

        {/* 最近文档 */}
        <Col xs={24} lg={8}>
          <Card 
            title="最近上传文档" 
            className="hover-card"
            extra={<Button type="link" onClick={() => navigate('/documents')}>查看全部</Button>}
            loading={loading}
          >
            {recentDocs.length > 0 ? (
              <List
                dataSource={recentDocs}
                renderItem={(doc: any) => (
                  <List.Item
                    actions={[<Tag color="blue">{doc.file_type}</Tag>]}
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar 
                          icon={<FileTextOutlined />}
                          style={{ backgroundColor: '#e6f7ff', color: '#1677ff' }}
                        />
                      }
                      title={doc.title}
                      description={
                        <Space>
                          <Tag>{doc.category}</Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {(doc.file_size / 1024).toFixed(1)} KB
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无文档" />
            )}
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={8}>
          <Card title="最近活动" className="hover-card">
            <Timeline
              items={activities.map((activity, index) => ({
                key: index,
                dot: activity.icon,
                children: (
                  <>
                    <Text>{activity.title}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {activity.time}
                    </Text>
                  </>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Home;
