import React, { useState, useEffect } from 'react';
import {
  Table, Button, Upload, message, Tag, Popconfirm, Input, Select,
  Card, Typography, Space, Row, Col, Statistic, Empty, Tooltip
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileUnknownOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/global.css';
import { BatchUpload } from '../components/BatchUpload';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const API_BASE = 'http://localhost:8000/api';

// 文件类型图标映射
const getFileIcon = (type: string) => {
  switch (type?.toLowerCase()) {
    case 'pdf':
      return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />;
    case 'doc':
    case 'docx':
      return <FileWordOutlined style={{ color: '#1677ff', fontSize: 24 }} />;
    case 'txt':
      return <FileTextOutlined style={{ color: '#52c41a', fontSize: 24 }} />;
    default:
      return <FileUnknownOutlined style={{ color: '#8c8c8c', fontSize: 24 }} />;
  }
};

interface Document {
  id: string;
  title: string;
  file_type: string;
  category: string;
  file_size: number;
  created_at: string;
}

const Documents: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [batchUploadVisible, setBatchUploadVisible] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/documents`, { timeout: 5000 });
      setDocuments(res.data.documents || []);
    } catch (e) {
      // API不可用时使用空列表优雅降级
      console.warn('API不可用，显示空列表');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', '工艺文档');

    try {
      await axios.post(`${API_BASE}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      message.success('上传成功');
      fetchDocuments();
    } catch (e) {
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleDelete = async (id: string) => {
    try {
      await axios.delete(`${API_BASE}/documents/${id}`);
      message.success('删除成功');
      fetchDocuments();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchSearch = doc.title?.toLowerCase().includes(searchText.toLowerCase());
    const matchCategory = selectedCategory === 'all' || doc.category === selectedCategory;
    return matchSearch && matchCategory;
  });

  const categories = ['all', ...Array.from(new Set(documents.map((d) => d.category)))];

  const stats = {
    total: documents.length,
    pdf: documents.filter((d) => d.file_type === 'pdf').length,
    word: documents.filter((d) => ['doc', 'docx'].includes(d.file_type)).length,
    txt: documents.filter((d) => d.file_type === 'txt').length,
  };

  const columns = [
    {
      title: '文档',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Document) => (
        <Space>
          {getFileIcon(record.file_type)}
          <div>
            <Text strong>{text}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {(record.file_size / 1024).toFixed(1)} KB · {record.file_type?.toUpperCase()}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: string) => (
        <Tag color="blue" style={{ borderRadius: 12 }}>{category}</Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => (
        <Space>
          <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
          <Text type="secondary">{new Date(date).toLocaleString('zh-CN')}</Text>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      align: 'center' as const,
      render: (_: any, record: Document) => (
        <Space>
          <Tooltip title="查看">
            <Button type="text" icon={<EyeOutlined />} />
          </Tooltip>
          <Tooltip title="搜索相关">
            <Button 
              type="text" 
              icon={<SearchOutlined />}
              onClick={() => navigate(`/search?keyword=${record.title}`)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除此文档吗？"
              description="删除后不可恢复"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-enter-active">
      {/* 页面标题 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space direction="vertical" size={4}>
            <Title level={3} style={{ margin: 0 }}>文档管理</Title>
            <Text type="secondary">管理您的知识文档，支持PDF、Word、TXT格式</Text>
          </Space>
        </Col>
        <Col>
          <Button type="primary" size="large" icon={<CloudUploadOutlined />} onClick={() => setBatchUploadVisible(true)}>
            批量上传
          </Button>
        </Col>
      </Row>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card className="hover-card" bodyStyle={{ padding: 16 }}>
            <Statistic
              title={<Space><DatabaseOutlined /> 全部文档</Space>}
              value={stats.total}
              valueStyle={{ color: '#1677ff', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="hover-card" bodyStyle={{ padding: 16 }}>
            <Statistic
              title={<Space><FilePdfOutlined /> PDF</Space>}
              value={stats.pdf}
              valueStyle={{ color: '#ff4d4f', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="hover-card" bodyStyle={{ padding: 16 }}>
            <Statistic
              title={<Space><FileWordOutlined /> Word</Space>}
              value={stats.word}
              valueStyle={{ color: '#1677ff', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="hover-card" bodyStyle={{ padding: 16 }}>
            <Statistic
              title={<Space><FileTextOutlined /> 文本</Space>}
              value={stats.txt}
              valueStyle={{ color: '#52c41a', fontSize: 28 }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和搜索 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索文档名称..."
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择分类"
              style={{ width: '100%' }}
              value={selectedCategory}
              onChange={setSelectedCategory}
            >
              {categories.map((cat: string) => (
                <Option key={cat} value={cat}>
                  {cat === 'all' ? '全部分类' : cat}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={24} md={10} style={{ textAlign: 'right' }}>
            <Space>
              <Text type="secondary">共 {filteredDocuments.length} 个文档</Text>
              <Button icon={<ReloadOutlined />} onClick={fetchDocuments}>刷新</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 文档列表 */}
      <Card className="hover-card">
        <Table
          rowKey="id"
          columns={columns}
          dataSource={filteredDocuments}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个文档`,
          }}
          locale={{
            emptyText: (
              <Empty
                description={
                  <Space direction="vertical">
                    <Text>暂无文档</Text>
                    <Upload beforeUpload={handleUpload} showUploadList={false}>
                      <Button type="primary" icon={<UploadOutlined />}>上传第一个文档</Button>
                    </Upload>
                  </Space>
                }
              />
            )
          }}
        />
      </Card>

      {/* 批量上传弹窗 */}
      <BatchUpload
        visible={batchUploadVisible}
        onClose={() => setBatchUploadVisible(false)}
        onSuccess={() => {
          fetchDocuments();
          setBatchUploadVisible(false);
        }}
      />
    </div>
  );
};

export default Documents;
