import React, { useState, useEffect } from 'react';
import {
  Input, Button, List, Card, Typography, Spin, Tag, Space, 
  Empty, Row, Col, Avatar, Badge, Skeleton, Divider,
  Tooltip, FloatButton, Statistic
} from 'antd';
import {
  SearchOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  FireOutlined,
  BulbOutlined,
  RobotFilled,
  ArrowRightOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/global.css';
import { SearchHighlight } from '../components/SearchHighlight';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const API_BASE = 'http://localhost:8000/api';

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [searchHistory, setSearchHistory] = useState([
    '光刻工艺', '设备故障', 'CVD工艺', '离子注入', '刻蚀机'
  ]);

  const hotSearches = [
    { keyword: '光刻机故障', count: 128 },
    { keyword: '工艺参数', count: 96 },
    { keyword: 'SOP流程', count: 84 },
    { keyword: '质量检测', count: 72 },
  ];

  const handleSearch = async (value?: string) => {
    const searchKeyword = value || keyword;
    if (!searchKeyword.trim()) return;
    
    setLoading(true);
    setSearched(true);
    
    try {
      const res = await axios.post(`${API_BASE}/search`, { 
        keyword: searchKeyword, 
        limit: 10 
      });
      setResults(res.data.results);
      
      // 添加到搜索历史
      if (!searchHistory.includes(searchKeyword)) {
        setSearchHistory(prev => [searchKeyword, ...prev].slice(0, 10));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setSearchHistory([]);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#1677ff';
    if (score >= 0.4) return '#faad14';
    return '#8c8c8c';
  };

  return (
    <div className="page-enter-active">
      {/* 搜索头部 */}
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Avatar
            size={64}
            icon={<SearchOutlined />}
            style={{ backgroundColor: '#e6f7ff', color: '#1677ff' }}
          />
          
          <Title level={2} style={{ margin: 0 }}>智能搜索</Title>
          <Paragraph type="secondary" style={{ fontSize: 16 }}>
            输入关键词，快速查找知识库中的文档和内容
          </Paragraph>

          {/* 大搜索框 */}
          <Card style={{ maxWidth: 800, margin: '0 auto', width: '100%' }}>
            <Search
              placeholder="搜索知识库..."
              allowClear
              enterButton={
                <Button type="primary" icon={<SearchOutlined />} size="large">
                  搜索
                </Button>
              }
              size="large"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onSearch={() => handleSearch()}
              style={{ width: '100%' }}
            />
          </Card>

          {/* 热门搜索 */}
          {!searched && (
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">
                <FireOutlined /> 热门搜索
              </Text>
              <Space wrap>
                {hotSearches.map((item) => (
                  <Tag
                    key={item.keyword}
                    className="hover-card"
                    style={{ cursor: 'pointer', padding: '4px 12px' }}
                    onClick={() => {
                      setKeyword(item.keyword);
                      handleSearch(item.keyword);
                    }}
                  >
                    {item.keyword}
                    <Badge count={item.count} style={{ marginLeft: 8 }} />
                  </Tag>
                ))}
              </Space>
            </Space>
          )}
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        {/* 左侧：搜索历史和筛选 */}
        <Col xs={24} lg={6}>
          {!searched ? (
            <Card title={<Space><HistoryOutlined /> 搜索历史</Space>}>
              {searchHistory.length > 0 ? (
                <>
                  <List
                    dataSource={searchHistory}
                    renderItem={(item) => (
                      <List.Item
                        style={{ cursor: 'pointer', padding: '8px 0' }}
                        onClick={() => {
                          setKeyword(item);
                          handleSearch(item);
                        }}
                        actions={[
                          <ArrowRightOutlined style={{ color: '#bfbfbf' }} />
                        ]}
                      >
                        <List.Item.Meta
                          title={<Text>{item}</Text>}
                        />
                      </List.Item>
                    )}
                  />
                  <Button type="link" danger onClick={clearHistory} block>
                    清空历史
                  </Button>
                </>
              ) : (
                <Empty description="暂无搜索历史" />
              )}
            </Card>
          ) : (
            <Card title="搜索统计">
              <Statistic
                title="搜索结果"
                value={results.length}
                suffix="条"
                valueStyle={{ color: '#1677ff' }}
              />
              <Divider />
              <Button onClick={() => { setSearched(false); setResults([]); }} block>
                重新搜索
              </Button>
            </Card>
          )}
        </Col>

        {/* 右侧：搜索结果 */}
        <Col xs={24} lg={18}>
          {searched ? (
            <Card 
              title={
                <Space>
                  <FileTextOutlined />
                  <span>搜索结果</span>
                  {loading && <Spin  />}
                </Space>
              }
              extra={
                results.length > 0 && (
                  <Text type="secondary">找到 {results.length} 个相关结果</Text>
                )
              }
            >
              {loading ? (
                <>
                  {[1, 2, 3].map((i) => (
                    <Card key={i} style={{ marginBottom: 16 }}>
                      <Skeleton active />
                    </Card>
                  ))}
                </>
              ) : results.length > 0 ? (
                <List
                  dataSource={results}
                  renderItem={(item: any) => (
                    <List.Item
                      style={{ 
                        padding: '16px',
                        marginBottom: '12px',
                        background: '#fafafa',
                        borderRadius: '8px',
                        cursor: 'pointer'
                      }}
                      className="hover-card"
                    >
                      <List.Item.Meta
                        avatar={
                          <Avatar 
                            size={48}
                            icon={<FileTextOutlined />}
                            style={{ 
                              backgroundColor: '#e6f7ff',
                              color: '#1677ff'
                            }}
                          />
                        }
                        title={
                          <Space>
                            <Text strong style={{ fontSize: 16 }}>
                              <SearchHighlight 
                                text={item.metadata?.title || '未命名文档'} 
                                keyword={keyword} 
                              />
                            </Text>
                            <Tag 
                              color={getScoreColor(item.score)}
                              style={{ fontWeight: 'bold' }}
                            >
                              相关度 {(item.score * 100).toFixed(1)}%
                            </Tag>
                          </Space>
                        }
                        description={
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <Paragraph 
                              ellipsis={{ rows: 2 }}
                              style={{ margin: 0, color: '#595959' }}
                            >
                              <SearchHighlight text={item.content} keyword={keyword} />
                            </Paragraph>
                            <Space>
                              <Tag>{item.metadata?.category || '未分类'}</Tag>
                              <Button 
                                type="link" 
                                
                                onClick={() => navigate('/chat')}
                              >
                                向AI询问此文档 →
                              </Button>
                            </Space>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    <Space direction="vertical">
                      <Text>未找到相关结果</Text>
                      <Text type="secondary">尝试使用其他关键词或上传相关文档</Text>
                    </Space>
                  }
                />
              )}
            </Card>
          ) : (
            <Card
              style={{ 
                textAlign: 'center', 
                padding: '60px 20px',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
              }}
            >
              <Space direction="vertical" size={16}>
                <BulbOutlined style={{ fontSize: 48, color: '#1677ff' }} />
                <Title level={4}>搜索提示</Title>
                <Paragraph type="secondary">
                  输入关键词开始搜索，系统将基于语义相似度为您匹配最相关的内容
                </Paragraph>
                <div style={{ textAlign: 'left', maxWidth: 400, margin: '0 auto' }}>
                  <Text strong>支持搜索：</Text>
                  <ul style={{ color: '#595959' }}>
                    <li>文档标题和内容</li>
                    <li>故障代码和处理方法</li>
                    <li>工艺参数和流程</li>
                    <li>自然语言描述的问题</li>
                  </ul>
                </div>
              </Space>
            </Card>
          )}
        </Col>
      </Row>

      {/* AI问答快捷入口 */}
      <FloatButton
        icon={<RobotFilled />}
        type="primary"
        tooltip="AI问答"
        onClick={() => navigate('/chat')}
      />
    </div>
  );
};

export default SearchPage;
