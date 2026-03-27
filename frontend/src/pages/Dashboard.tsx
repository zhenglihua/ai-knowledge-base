import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, DatePicker, Select, Button, Spin,
  Typography, Badge, Empty, Tag, Progress, Tooltip, Table, Tabs, Space
} from 'antd';
import {
  FileTextOutlined, MessageOutlined, SearchOutlined,
  RiseOutlined, FallOutlined, UserOutlined, ClockCircleOutlined,
  BarChartOutlined, PieChartOutlined, LineChartOutlined,
  ReloadOutlined, DownloadOutlined, CalendarOutlined
} from '@ant-design/icons';
import type { TabsProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 统计卡片组件
interface StatCardProps {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  color?: string;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  prefix,
  suffix,
  trend = 'flat',
  trendValue,
  color = '#1677ff',
  loading = false
}) => {
  const trendIcon = {
    up: <RiseOutlined style={{ color: '#52c41a' }} />,
    down: <FallOutlined style={{ color: '#ff4d4f' }} />,
    flat: null
  };

  return (
    <Card className="hover-card" style={{ height: '100%' }}>
      <Spin spinning={loading}>
        <Statistic
          title={
            <Space>
              {prefix}
              <Text type="secondary">{title}</Text>
            </Space>
          }
          value={value}
          valueStyle={{ color, fontSize: 28, fontWeight: 600 }}
          suffix={suffix}
        />
        {trendValue && (
          <div style={{ marginTop: 8 }}>
            <Space>
              {trendIcon[trend]}
              <Text type={trend === 'up' ? 'success' : trend === 'down' ? 'danger' : 'secondary'}>
                {trendValue}
              </Text>
            </Space>
          </div>
        )}
      </Spin>
    </Card>
  );
};

// 文档统计Tab
const DocumentStats: React.FC<{ loading: boolean }> = ({ loading }) => {
  const [docStats, setDocStats] = useState({
    total: 156,
    pdf: 89,
    word: 45,
    txt: 22,
    thisWeek: 12,
    growth: 15.3
  });

  const categoryData = [
    { name: '工艺文档', count: 45, percentage: 28.8 },
    { name: '设备手册', count: 38, percentage: 24.4 },
    { name: '故障处理', count: 32, percentage: 20.5 },
    { name: '安全规范', count: 25, percentage: 16.0 },
    { name: '其他', count: 16, percentage: 10.3 }
  ];

  const columns = [
    {
      title: '分类',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '文档数',
      dataIndex: 'count',
      key: 'count',
      align: 'center' as const
    },
    {
      title: '占比',
      dataIndex: 'percentage',
      key: 'percentage',
      align: 'center' as const,
      render: (value: number) => (
        <Progress percent={value} size="small" showInfo={false} strokeColor="#1677ff" />
      )
    },
    {
      title: '比例',
      dataIndex: 'percentage',
      key: 'percentage_text',
      align: 'center' as const,
      render: (value: number) => <Text>{value}%</Text>
    }
  ];

  return (
    <Spin spinning={loading}>
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="文档总数"
            value={docStats.total}
            prefix={<FileTextOutlined />}
            trend="up"
            trendValue={`+${docStats.thisWeek} 本周新增`}
            color="#1677ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="PDF文档"
            value={docStats.pdf}
            prefix={<FileTextOutlined style={{ color: '#ff4d4f' }} />}
            color="#ff4d4f"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Word文档"
            value={docStats.word}
            prefix={<FileTextOutlined style={{ color: '#1677ff' }} />}
            color="#1677ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="增长率"
            value={`${docStats.growth}%`}
            prefix={<RiseOutlined />}
            trend="up"
            trendValue="较上月"
            color="#52c41a"
          />
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="文档分类分布" className="hover-card">
            <Table
              dataSource={categoryData}
              columns={columns}
              pagination={false}
              rowKey="name"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="文档上传趋势" className="hover-card">
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Empty description="图表组件需要额外库支持" />
            </div>
          </Card>
        </Col>
      </Row>
    </Spin>
  );
};

// 问答统计Tab
const ChatStats: React.FC<{ loading: boolean }> = ({ loading }) => {
  const [chatStats, setChatStats] = useState({
    total: 1289,
    today: 45,
    avgResponseTime: 2.3,
    satisfaction: 94.5,
    activeUsers: 23
  });

  const topQuestions = [
    { question: '光刻机故障E-203怎么处理？', count: 156, trend: 'up' },
    { question: 'CVD工艺温度设置范围', count: 134, trend: 'flat' },
    { question: '离子注入参数优化', count: 98, trend: 'up' },
    { question: '半导体清洗工艺步骤', count: 87, trend: 'down' },
    { question: '刻蚀工艺常见问题', count: 76, trend: 'flat' }
  ];

  return (
    <Spin spinning={loading}>
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="总问答数"
            value={chatStats.total}
            prefix={<MessageOutlined />}
            trend="up"
            trendValue={`+${chatStats.today} 今日`}
            color="#722ed1"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="平均响应"
            value={`${chatStats.avgResponseTime}s`}
            prefix={<ClockCircleOutlined />}
            trend="up"
            trendValue="速度提升 12%"
            color="#1677ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="满意度"
            value={`${chatStats.satisfaction}%`}
            prefix={<UserOutlined />}
            trend="up"
            trendValue="用户好评"
            color="#52c41a"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="活跃用户"
            value={chatStats.activeUsers}
            prefix={<UserOutlined />}
            trend="up"
            trendValue="在线用户"
            color="#fa8c16"
          />
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="热门问题TOP5" className="hover-card">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {topQuestions.map((item, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge
                    count={index + 1}
                    style={{
                      backgroundColor: index < 3 ? '#1677ff' : '#8c8c8c',
                      minWidth: 24
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <Text>{item.question}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.count} 次询问
                    </Text>
                  </div>
                  {item.trend === 'up' ? (
                    <RiseOutlined style={{ color: '#52c41a' }} />
                  ) : item.trend === 'down' ? (
                    <FallOutlined style={{ color: '#ff4d4f' }} />
                  ) : null}
                </div>
              ))}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="问答趋势" className="hover-card">
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Empty description="图表组件需要额外库支持" />
            </div>
          </Card>
        </Col>
      </Row>
    </Spin>
  );
};

// 搜索统计Tab
const SearchStats: React.FC<{ loading: boolean }> = ({ loading }) => {
  const [searchStats, setSearchStats] = useState({
    total: 568,
    today: 28,
    avgResults: 8.5,
    clickRate: 72.3
  });

  const hotKeywords = [
    { word: '光刻机', count: 89 },
    { word: 'CVD', count: 76 },
    { word: '刻蚀', count: 65 },
    { word: '离子注入', count: 54 },
    { word: '清洗工艺', count: 43 }
  ];

  return (
    <Spin spinning={loading}>
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="搜索次数"
            value={searchStats.total}
            prefix={<SearchOutlined />}
            trend="up"
            trendValue={`+${searchStats.today} 今日`}
            color="#1677ff"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="平均结果数"
            value={searchStats.avgResults}
            prefix={<FileTextOutlined />}
            trend="flat"
            color="#52c41a"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="点击率"
            value={`${searchStats.clickRate}%`}
            prefix={<RiseOutlined />}
            trend="up"
            trendValue="较上周 +5%"
            color="#722ed1"
          />
        </Col>
      </Row>

      <Card title="热门搜索词" className="hover-card">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          {hotKeywords.map((item, index) => (
            <Tag 
              key={index} 
              color="blue" 
              style={{ padding: '4px 12px', fontSize: 14 }}
            >
              {item.word}
              <Badge 
                count={item.count} 
                style={{ marginLeft: 8, backgroundColor: '#1677ff' }} 
              />
            </Tag>
          ))}
        </div>
      </Card>
    </Spin>
  );
};

// 主仪表盘组件
const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('week');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1000);
  };

  const items: TabsProps['items'] = [
    {
      key: '1',
      label: (
        <Space>
          <FileTextOutlined />
          文档统计
        </Space>
      ),
      children: <DocumentStats loading={loading} />
    },
    {
      key: '2',
      label: (
        <Space>
          <MessageOutlined />
          问答统计
        </Space>
      ),
      children: <ChatStats loading={loading} />
    },
    {
      key: '3',
      label: (
        <Space>
          <SearchOutlined />
          搜索统计
        </Space>
      ),
      children: <SearchStats loading={loading} />
    }
  ];

  return (
    <div className="page-enter-active">
      {/* 头部区域 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space direction="vertical" size={4}>
            <Title level={3} style={{ margin: 0 }}>
              <BarChartOutlined /> 数据统计仪表盘
            </Title>
            <Text type="secondary">实时监控知识库使用情况和数据统计</Text>
          </Space>
        </Col>
        <Col>
          <Space>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 120 }}
              suffixIcon={<CalendarOutlined />}
            >
              <Option value="today">今日</Option>
              <Option value="week">本周</Option>
              <Option value="month">本月</Option>
              <Option value="quarter">本季度</Option>
              <Option value="year">本年</Option>
            </Select>
            <RangePicker 
              style={{ width: 240 }}
              placeholder={['开始日期', '结束日期']}
            />
            <Tooltip title="刷新数据">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={loading}
              />
            </Tooltip>
            <Button 
              type="primary" 
              icon={<DownloadOutlined />}
            >
              导出报告
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Tabs内容 */}
      <Tabs
        defaultActiveKey="1"
        items={items}
        type="card"
        className="dashboard-tabs"
      />
    </div>
  );
};

export default Dashboard;