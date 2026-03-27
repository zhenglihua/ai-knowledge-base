import React, { useState, useEffect } from 'react';
import {
  List, Card, Typography, Space, Tag, Button, Empty, Spin,
  Input, Badge, Tooltip, Dropdown, Menu, Modal, message, Popconfirm
} from 'antd';
import {
  HistoryOutlined, MessageOutlined, DeleteOutlined, 
  EditOutlined, MoreOutlined, ClockCircleOutlined,
  SearchOutlined, StarOutlined, StarFilled, ExportOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

const API_BASE = 'http://localhost:8000/api';

export interface ChatHistory {
  id: string;
  title: string;
  firstMessage: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
  isPinned?: boolean;
  tags?: string[];
}

interface ChatHistoryListProps {
  onSelect?: (history: ChatHistory) => void;
  onDelete?: (id: string) => void;
  onPin?: (id: string, pinned: boolean) => void;
  onRename?: (id: string, newTitle: string) => void;
  currentChatId?: string;
  maxHeight?: string | number;
  showSearch?: boolean;
  showTitle?: boolean;
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  } else if (days === 1) {
    return '昨天';
  } else if (days < 7) {
    return `${days}天前`;
  } else if (days < 30) {
    return `${Math.floor(days / 7)}周前`;
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  }
};

// 获取预览文本
const getPreviewText = (text: string, maxLength: number = 60): string => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const ChatHistoryList: React.FC<ChatHistoryListProps> = ({
  onSelect,
  onDelete,
  onPin,
  onRename,
  currentChatId,
  maxHeight = 500,
  showSearch = true,
  showTitle = true
}) => {
  const [histories, setHistories] = useState<ChatHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [renamingHistory, setRenamingHistory] = useState<ChatHistory | null>(null);
  const [newTitle, setNewTitle] = useState('');

  // 加载历史记录
  const loadHistories = async () => {
    setLoading(true);
    try {
      // 从localStorage加载（模拟API）
      const stored = localStorage.getItem('chat_histories');
      if (stored) {
        const parsed = JSON.parse(stored);
        // 按时间倒序，置顶优先
        const sorted = parsed.sort((a: ChatHistory, b: ChatHistory) => {
          if (a.isPinned && !b.isPinned) return -1;
          if (!a.isPinned && b.isPinned) return 1;
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
        });
        setHistories(sorted);
      } else {
        // 模拟数据
        const mockData: ChatHistory[] = [
          {
            id: '1',
            title: '光刻机故障排查',
            firstMessage: '光刻机故障E-203怎么处理？',
            messageCount: 8,
            createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            updatedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            isPinned: true,
            tags: ['故障', '光刻']
          },
          {
            id: '2',
            title: 'CVD工艺咨询',
            firstMessage: '什么是CVD工艺？',
            messageCount: 12,
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
            updatedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            tags: ['工艺', 'CVD']
          },
          {
            id: '3',
            title: '离子注入参数',
            firstMessage: '如何优化离子注入参数？',
            messageCount: 6,
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
            updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 20).toISOString()
          },
          {
            id: '4',
            title: '半导体制造流程',
            firstMessage: '半导体制造的主要步骤有哪些？',
            messageCount: 15,
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
            updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 46).toISOString(),
            isPinned: false
          }
        ];
        setHistories(mockData);
        localStorage.setItem('chat_histories', JSON.stringify(mockData));
      }
    } catch (error) {
      message.error('加载历史记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistories();
  }, []);

  // 过滤历史记录
  const filteredHistories = histories.filter(h => 
    h.title.toLowerCase().includes(searchText.toLowerCase()) ||
    h.firstMessage.toLowerCase().includes(searchText.toLowerCase()) ||
    h.tags?.some(tag => tag.toLowerCase().includes(searchText.toLowerCase()))
  );

  // 处理选择
  const handleSelect = (history: ChatHistory) => {
    onSelect?.(history);
  };

  // 处理删除
  const handleDelete = async (id: string) => {
    try {
      const newHistories = histories.filter(h => h.id !== id);
      setHistories(newHistories);
      localStorage.setItem('chat_histories', JSON.stringify(newHistories));
      onDelete?.(id);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 处理置顶
  const handlePin = async (id: string, pinned: boolean) => {
    try {
      const newHistories = histories.map(h => 
        h.id === id ? { ...h, isPinned: pinned } : h
      ).sort((a, b) => {
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      });
      setHistories(newHistories);
      localStorage.setItem('chat_histories', JSON.stringify(newHistories));
      onPin?.(id, pinned);
      message.success(pinned ? '已置顶' : '已取消置顶');
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 打开重命名弹窗
  const openRenameModal = (history: ChatHistory) => {
    setRenamingHistory(history);
    setNewTitle(history.title);
    setRenameModalVisible(true);
  };

  // 处理重命名
  const handleRename = () => {
    if (!newTitle.trim()) {
      message.error('标题不能为空');
      return;
    }
    if (renamingHistory) {
      const newHistories = histories.map(h => 
        h.id === renamingHistory.id ? { ...h, title: newTitle.trim() } : h
      );
      setHistories(newHistories);
      localStorage.setItem('chat_histories', JSON.stringify(newHistories));
      onRename?.(renamingHistory.id, newTitle.trim());
      message.success('重命名成功');
    }
    setRenameModalVisible(false);
    setRenamingHistory(null);
    setNewTitle('');
  };

  // 更多操作菜单
  const getMoreMenu = (history: ChatHistory) => (
    <Menu>
      <Menu.Item 
        key="pin" 
        icon={history.isPinned ? <StarFilled /> : <StarOutlined />}
        onClick={() => handlePin(history.id, !history.isPinned)}
      >
        {history.isPinned ? '取消置顶' : '置顶对话'}
      </Menu.Item>
      <Menu.Item 
        key="rename" 
        icon={<EditOutlined />}
        onClick={() => openRenameModal(history)}
      >
        重命名
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item 
        key="delete" 
        icon={<DeleteOutlined />} 
        danger
        onClick={() => handleDelete(history.id)}
      >
        删除对话
      </Menu.Item>
    </Menu>
  );

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 标题 */}
      {showTitle && (
        <div style={{ paddingBottom: 16, borderBottom: '1px solid #f0f0f0', marginBottom: 16 }}>
          <Space>
            <HistoryOutlined />
            <Title level={5} style={{ margin: 0 }}>对话历史</Title>
            <Badge count={histories.length} style={{ backgroundColor: '#1677ff' }} />
          </Space>
        </div>
      )}

      {/* 搜索框 */}
      {showSearch && (
        <Search
          placeholder="搜索对话..."
          allowClear
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16 }}
          prefix={<SearchOutlined />}
        />
      )}

      {/* 历史列表 */}
      <Spin spinning={loading}>
        <List
          style={{ 
            flex: 1, 
            overflow: 'auto',
            maxHeight: typeof maxHeight === 'number' ? maxHeight : undefined
          }}
          dataSource={filteredHistories}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  searchText ? '未找到匹配的历史记录' : '暂无对话历史'
                }
              />
            )
          }}
          renderItem={(history) => (
            <List.Item
              key={history.id}
              style={{ 
                padding: '8px 0',
                cursor: 'pointer',
                backgroundColor: currentChatId === history.id ? '#e6f7ff' : 'transparent',
                borderRadius: 8,
                marginBottom: 4,
                paddingLeft: 8,
                paddingRight: 8
              }}
              onClick={() => handleSelect(history)}
              actions={[
                <Dropdown overlay={getMoreMenu(history)} trigger={['click']}>
                  <Button 
                    type="text" 
                    size="small" 
                    icon={<MoreOutlined />}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Dropdown>
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Space direction="vertical" align="center" size={0}>
                    <MessageOutlined 
                      style={{ 
                        fontSize: 20, 
                        color: currentChatId === history.id ? '#1677ff' : '#8c8c8c' 
                      }} 
                    />
                    {history.isPinned && (
                      <StarFilled style={{ fontSize: 10, color: '#faad14' }} />
                    )}
                  </Space>
                }
                title={
                  <Space>
                    <Text 
                      strong={currentChatId === history.id}
                      style={{ 
                        color: currentChatId === history.id ? '#1677ff' : undefined,
                        maxWidth: 140,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        display: 'inline-block'
                      }}
                    >
                      {history.title}
                    </Text>
                    {history.tags?.map((tag, i) => (
                      <Tag key={i} style={{ fontSize: 10 }}>{tag}</Tag>
                    ))}
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                      {getPreviewText(history.firstMessage)}
                    </Text>
                    <Space size={8} style={{ marginTop: 4 }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        <ClockCircleOutlined /> {formatDate(history.updatedAt)}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {history.messageCount} 条消息
                      </Text>
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Spin>

      {/* 重命名弹窗 */}
      <Modal
        title="重命名对话"
        visible={renameModalVisible}
        onOk={handleRename}
        onCancel={() => {
          setRenameModalVisible(false);
          setRenamingHistory(null);
          setNewTitle('');
        }}
        okText="确认"
        cancelText="取消"
      >
        <Input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="请输入新标题"
          maxLength={50}
          showCount
        />
      </Modal>
    </div>
  );
};

export default ChatHistoryList;