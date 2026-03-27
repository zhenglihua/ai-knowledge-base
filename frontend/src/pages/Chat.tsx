import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Input, Button, List, Card, Typography, Space, 
  Avatar, Divider, Empty, Badge, Tooltip, Row, Col, Tag,
  Spin, Skeleton, message
} from 'antd';
import { 
  SendOutlined, 
  RobotFilled, 
  UserOutlined, 
  ClearOutlined,
  BulbOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  LikeOutlined,
  DislikeOutlined,
  CopyOutlined,
  PauseCircleOutlined,
  HistoryOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined
} from '@ant-design/icons';
import axios from 'axios';
import '../styles/global.css';
import ChatHistoryList, { ChatHistory } from '../components/ChatHistoryList';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const API_BASE = 'http://localhost:8000/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  timestamp: Date;
  liked?: boolean;
  isStreaming?: boolean;
}

// 流式文本组件
interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
  onComplete?: () => void;
}

const StreamingText: React.FC<StreamingTextProps> = ({ text, isStreaming, onComplete }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const speedRef = useRef(10);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayText(text);
      return;
    }

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        const char = text[currentIndex];
        if (char === ' ' || char === '\n') {
          speedRef.current = 5;
        } else if (/[，。！？；：""''（）]/.test(char)) {
          speedRef.current = 50;
        } else {
          speedRef.current = 15;
        }

        setDisplayText(text.substring(0, currentIndex + 1));
        setCurrentIndex(prev => prev + 1);
      }, speedRef.current);

      return () => clearTimeout(timer);
    } else {
      onComplete?.();
    }
  }, [text, isStreaming, currentIndex, onComplete]);

  useEffect(() => {
    setCurrentIndex(0);
    setDisplayText('');
  }, [text]);

  return (
    <span>
      {displayText}
      {isStreaming && currentIndex < text.length && (
        <span className="streaming-cursor" />
      )}
    </span>
  );
};

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(true);
  const [currentChatId, setCurrentChatId] = useState<string | undefined>(undefined);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  const quickQuestions = [
    '光刻机故障E-203怎么处理？',
    '什么是CVD工艺？',
    '半导体制造的主要步骤有哪些？',
    '如何优化离子注入参数？',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const saveToHistory = useCallback((msgs: Message[], chatId?: string) => {
    if (msgs.length === 0) return;

    const histories = JSON.parse(localStorage.getItem('chat_histories') || '[]');
    const firstUserMsg = msgs.find(m => m.role === 'user');
    
    if (!firstUserMsg) return;

    const title = firstUserMsg.content.substring(0, 30) + 
      (firstUserMsg.content.length > 30 ? '...' : '');

    const historyData: ChatHistory = {
      id: chatId || Date.now().toString(),
      title,
      firstMessage: firstUserMsg.content,
      messageCount: msgs.length,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const existingIndex = histories.findIndex((h: ChatHistory) => h.id === historyData.id);
    if (existingIndex >= 0) {
      histories[existingIndex] = historyData;
    } else {
      histories.unshift(historyData);
    }

    localStorage.setItem('chat_histories', JSON.stringify(histories.slice(0, 50)));
    localStorage.setItem(`chat_messages_${historyData.id}`, JSON.stringify(msgs));
    
    if (!chatId) {
      setCurrentChatId(historyData.id);
    }
  }, []);

  const loadChatHistory = (history: ChatHistory) => {
    const stored = localStorage.getItem(`chat_messages_${history.id}`);
    if (stored) {
      const parsed = JSON.parse(stored);
      setMessages(parsed.map((m: any) => ({
        ...m,
        timestamp: new Date(m.timestamp)
      })));
      setCurrentChatId(history.id);
    } else {
      message.warning('对话记录已过期');
    }
  };

  const createNewChat = () => {
    setMessages([]);
    setCurrentChatId(undefined);
    setInput('');
    inputRef.current?.focus();
  };

  const handleStreamRequest = async (query: string) => {
    setIsStreaming(true);
    setStreamingMessage('');
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.substring(6);
              if (data === '[DONE]') {
                break;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  fullText += parsed.content;
                  setStreamingMessage(fullText);
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }
      }

      return fullText;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        return streamingMessage || '已取消生成';
      }
      throw error;
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const simulateStream = async (query: string): Promise<string> => {
    return new Promise((resolve) => {
      setIsStreaming(true);
      
      const responses: Record<string, string> = {
        '光刻机故障E-203怎么处理？': `根据知识库资料：\n\n1. 首先检查光刻机冷却系统，确保冷却液循环正常\n2. 检查激光器功率输出，确认在额定范围内\n3. 清洁光学镜片，排除污染导致的能量损失\n4. 如果问题持续，请联系设备厂商技术支持\n\n（注：具体操作建议参考设备维护手册第3.2节）`,
        '什么是CVD工艺？': `CVD（化学气相沉积）是一种重要的薄膜制备工艺：\n\n1. 原理：通过气相化学反应在衬底表面沉积薄膜\n2. 主要类型：APCVD、LPCVD、PECVD等\n3. 应用：广泛用于制备氧化硅、氮化硅、多晶硅等薄膜\n4. 优势：沉积均匀性好、台阶覆盖优良\n\n如需了解更多工艺参数，请查阅工艺文档。`,
        '半导体制造的主要步骤有哪些？': `半导体制造主要包括以下步骤：\n\n1. 晶圆制备 - 单晶硅生长、切割、抛光\n2. 氧化 - 形成SiO2绝缘层\n3. 光刻 - 图形转移\n4. 刻蚀 - 选择性去除材料\n5. 离子注入 - 掺杂形成PN结\n6. 薄膜沉积 - CVD、PVD等\n7. 金属化 - 形成互连\n8. 测试封装 - 最终检验\n\n每个步骤都有严格的工艺控制要求。`,
        '如何优化离子注入参数？': `离子注入参数优化建议：\n\n1. 能量选择 - 根据目标结深确定注入能量\n2. 剂量控制 - 精确控制掺杂浓度\n3. 角度优化 - 考虑沟道效应，通常选择7°倾斜\n4. 温度控制 - 高温注入可减少缺陷\n5. 退火处理 - 注入后需进行热退火激活\n\n具体参数需要结合实际工艺要求调整。`
      };

      const response = responses[query] || `根据知识库资料，关于"${query}"的相关信息如下：\n\n1. 这是一个重要的技术问题，需要从多个角度分析\n2. 建议参考相关的工艺文档和设备手册\n3. 如需更详细的解答，请提供更具体的上下文\n\n您可以继续提问，我会尽力为您解答。`;

      let index = 0;
      let currentText = '';

      const interval = setInterval(() => {
        if (index < response.length) {
          currentText += response[index];
          setStreamingMessage(currentText);
          index++;
        } else {
          clearInterval(interval);
          setIsStreaming(false);
          resolve(response);
        }
      }, 15);

      (abortControllerRef as any).current = {
        abort: () => {
          clearInterval(interval);
          setIsStreaming(false);
        }
      };
    });
  };

  const handleSend = async (question?: string) => {
    const query = question || input;
    if (!query.trim() || loading || isStreaming) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    
    if (!question) setInput('');
    setLoading(true);

    try {
      let answer: string;
      try {
        answer = await handleStreamRequest(query);
      } catch {
        answer = await simulateStream(query);
      }

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: answer,
        sources: [{ title: '半导体工艺手册.pdf' }],
        timestamp: new Date()
      };

      const finalMessages = [...newMessages, assistantMsg];
      setMessages(finalMessages);
      saveToHistory(finalMessages, currentChatId);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，服务暂时不可用，请稍后重试。',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
      setStreamingMessage('');
    }
  };

  const handleCancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setCurrentChatId(undefined);
    setInput('');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const renderMessageContent = (msg: Message) => {
    if (msg.role === 'assistant') {
      const lines = msg.content.split('\n');
      return lines.map((line, index) => {
        if (line.startsWith('根据知识库资料：')) {
          return <div key={index} style={{ marginBottom: 12, fontWeight: 500 }}>{line}</div>;
        }
        if (/^\d+\./.test(line)) {
          return <div key={index} style={{ marginLeft: 8, marginBottom: 8 }}>{line}</div>;
        }
        if (line.startsWith('（注：')) {
          return <div key={index} style={{ fontSize: 12, color: '#8c8c8c', marginTop: 12 }}>{line}</div>;
        }
        return <div key={index} style={{ marginBottom: 4 }}>{line}</div>;
      });
    }
    return msg.content;
  };

  return (
    <div style={{ height: 'calc(100vh - 112px)', display: 'flex', gap: 16 }}>
      {historyVisible && (
        <Card
          style={{
            width: 300,
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column'
          }}
          bodyStyle={{ padding: 16, height: '100%', overflow: 'hidden' }}
        >
          <div style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              block
              icon={<MessageOutlined />}
              onClick={createNewChat}
            >
              新建对话
            </Button>
          </div>
          <ChatHistoryList
            onSelect={loadChatHistory}
            currentChatId={currentChatId}
            maxHeight="calc(100vh - 280px)"
            showSearch={true}
            showTitle={false}
          />
        </Card>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Space>
              <Button
                type="text"
                icon={historyVisible ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />}
                onClick={() => setHistoryVisible(!historyVisible)}
              />
              <Avatar
                size={40}
                icon={<RobotFilled />}
                style={{ backgroundColor: '#1677ff' }}
              />
              <Space direction="vertical" size={0}>
                <Title level={4} style={{ margin: 0 }}>AI智能助手</Title>
                <Space>
                  <Badge status="success" />
                  <Text type="secondary" style={{ fontSize: 12 }}>在线</Text>
                </Space>
              </Space>
            </Space>
          </Col>
          <Col>
            <Space>
              {messages.length > 0 && (
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={clearChat}
                  type="text"
                  danger
                >
                  清空对话
                </Button>
              )}
            </Space>
          </Col>
        </Row>

        <Card 
          style={{ 
            flex: 1, 
            overflow: 'auto', 
            marginBottom: 16,
            background: '#f5f5f5'
          }}
          bodyStyle={{ padding: '16px' }}
        >
          {messages.length === 0 ? (
            <Empty
              image={<RobotFilled style={{ fontSize: 64, color: '#d9d9d9' }} />}
              description={
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <Text strong style={{ fontSize: 16 }}>我是您的AI知识库助手</Text>
                  <Paragraph type="secondary">
                    基于半导体工厂知识库，为您解答工艺、设备、故障处理等问题
                  </Paragraph>
                  
                  <Divider style={{ margin: '8px 0' }} />
                  
                  <Text type="secondary"><BulbOutlined /> 您可以问我：</Text>
                  
                  <Row gutter={[8, 8]} style={{ maxWidth: 600, margin: '0 auto' }}>
                    {quickQuestions.map((q, i) => (
                      <Col span={12} key={i}>
                        <Tag
                          className="hover-card"
                          style={{ 
                            cursor: 'pointer', 
                            padding: '8px 12px',
                            width: '100%',
                            textAlign: 'center'
                          }}
                          onClick={() => handleSend(q)}
                        >
                          {q}
                        </Tag>
                      </Col>
                    ))}
                  </Row>
                </Space>
              }
            />
          ) : (
            <List
              dataSource={messages}
              renderItem={(msg) => (
                <List.Item 
                  style={{ 
                    border: 'none', 
                    padding: '12px 0',
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    width: '100%',
                    gap: 12
                  }}
                  >
                    {msg.role === 'assistant' && (
                      <Avatar
                        size={36}
                        icon={<RobotFilled />}
                        style={{ backgroundColor: '#1677ff', flexShrink: 0 }}
                      />
                    )}
                    
                    <div style={{ maxWidth: '75%' }}>
                      <div
                        style={{
                          padding: '12px 16px',
                          borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                          background: msg.role === 'user' ? '#1677ff' : '#fff',
                          color: msg.role === 'user' ? '#fff' : '#262626',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                          fontSize: 14,
                          lineHeight: 1.6
                        }}
                      >
                        {renderMessageContent(msg)}
                      </div>
                      
                      <div style={{ 
                        marginTop: 6, 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 8,
                        fontSize: 12,
                        color: '#8c8c8c'
                      }}
                      >
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {msg.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                        </Text>
                        
                        {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                          <Space size={4}>
                            <Divider type="vertical" />
                            <FileTextOutlined />
                            <Text>参考: {msg.sources.map((s: any) => s.title).join(', ')}</Text>
                          </Space>
                        )}
                        
                        {msg.role === 'assistant' && (
                          <>
                            <Divider type="vertical" />
                            <Tooltip title="复制">
                              <CopyOutlined 
                                style={{ cursor: 'pointer' }}
                                onClick={() => copyToClipboard(msg.content)}
                              />
                            </Tooltip>
                            <Tooltip title="有用">
                              <LikeOutlined style={{ cursor: 'pointer', marginLeft: 8 }} />
                            </Tooltip>
                          </>
                        )}
                      </div>
                    </div>
                    
                    {msg.role === 'user' && (
                      <Avatar
                        size={36}
                        icon={<UserOutlined />}
                        style={{ backgroundColor: '#52c41a', flexShrink: 0 }}
                      />
                    )}
                  </div>
                </List.Item>
              )}
            />
          )}
          
          {isStreaming && streamingMessage && (
            <List.Item style={{ border: 'none', padding: '12px 0' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'flex-start',
                width: '100%',
                gap: 12
              }}
              >
                <Avatar
                  size={36}
                  icon={<RobotFilled />}
                  style={{ backgroundColor: '#1677ff', flexShrink: 0 }}
                />
                <div style={{ maxWidth: '75%' }}>
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: '16px 16px 16px 4px',
                      background: '#fff',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                      fontSize: 14,
                      lineHeight: 1.6
                    }}
                  >
                    <StreamingText 
                      text={streamingMessage} 
                      isStreaming={true}
                    />
                  </div>
                  <div style={{ 
                    marginTop: 6, 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 8,
                    fontSize: 12,
                    color: '#8c8c8c'
                  }}
                  >
                    <Spin size="small" />
                    <Text type="secondary">AI正在思考...</Text>
                    <Button
                      type="link"
                      size="small"
                      icon={<PauseCircleOutlined />}
                      onClick={handleCancelStream}
                      style={{ padding: 0, height: 'auto' }}
                    >
                      停止生成
                    </Button>
                  </div>
                </div>
              </div>
            </List.Item>
          )}
          
          <div ref={messagesEndRef} />
        </Card>

        <Card
          bodyStyle={{ padding: '12px 16px' }}
          style={{ margin: 0 }}
        >
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <TextArea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isStreaming ? "AI正在生成回答..." : "输入问题，AI将基于知识库回答..."}
              autoSize={{ minRows: 1, maxRows: 4 }}
              onPressEnter={(e) => {
                if (!e.shiftKey && !isStreaming) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isStreaming}
              style={{ 
                borderRadius: 20,
                padding: '10px 16px',
                resize: 'none'
              }}
            />
            <Button
              type="primary"
              shape="circle"
              icon={isStreaming ? <PauseCircleOutlined /> : <SendOutlined />}
              onClick={isStreaming ? handleCancelStream : () => handleSend()}
              loading={loading && !isStreaming}
              size="large"
              style={{ flexShrink: 0 }}
              danger={isStreaming}
            />
          </div>
          <div style={{ marginTop: 8, textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <InfoCircleOutlined /> AI回答基于知识库内容，仅供参考
            </Text>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Chat;