import React, { useState, useCallback } from 'react';
import {
  Upload, Button, List, Progress, Space, Tag, Typography, 
  Modal, Tooltip, Badge, message
} from 'antd';
import {
  UploadOutlined, FileOutlined, CloseOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import axios from 'axios';

const { Text, Title } = Typography;

interface BatchUploadProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
  category?: string;
}

interface FileItem {
  uid: string;
  file: File;
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  errorMsg?: string;
}

const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  let color = '#8c8c8c';
  switch (ext) {
    case 'pdf': color = '#ff4d4f'; break;
    case 'doc':
    case 'docx': color = '#1677ff'; break;
    case 'txt': color = '#52c41a'; break;
  }
  return <FileOutlined style={{ color, fontSize: 20 }} />;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

export const BatchUpload: React.FC<BatchUploadProps> = ({
  visible,
  onClose,
  onSuccess,
  category = '工艺文档'
}) => {
  const [fileList, setFileList] = useState<FileItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const API_BASE = 'http://localhost:8888/api';

  const handleFileSelect = useCallback((info: any) => {
    const files = info.fileList as UploadFile[];
    const newItems: FileItem[] = files.map(f => ({
      uid: f.uid,
      file: f.originFileObj as File,
      name: f.name,
      size: f.size || 0,
      status: 'pending',
      progress: 0
    }));
    
    // 过滤重复文件
    setFileList(prev => {
      const existingUids = new Set(prev.map(p => p.uid));
      const uniqueNew = newItems.filter(n => !existingUids.has(n.uid));
      return [...prev, ...uniqueNew];
    });
    
    return false;
  }, []);

  const removeFile = (uid: string) => {
    setFileList(prev => prev.filter(f => f.uid !== uid));
  };

  const clearAll = () => {
    setFileList([]);
  };

  const uploadSingleFile = async (item: FileItem): Promise<void> => {
    const formData = new FormData();
    formData.append('file', item.file);
    formData.append('category', category);

    try {
      setFileList(prev => prev.map(f => 
        f.uid === item.uid ? { ...f, status: 'uploading' } : f
      ));

      await axios.post(`${API_BASE}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setFileList(prev => prev.map(f => 
            f.uid === item.uid ? { ...f, progress } : f
          ));
        }
      });

      setFileList(prev => prev.map(f => 
        f.uid === item.uid ? { ...f, status: 'success', progress: 100 } : f
      ));
    } catch (error: any) {
      setFileList(prev => prev.map(f => 
        f.uid === item.uid ? { 
          ...f, 
          status: 'error', 
          errorMsg: error.response?.data?.detail || '上传失败'
        } : f
      ));
    }
  };

  const handleBatchUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件');
      return;
    }

    const pendingFiles = fileList.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) {
      message.info('没有待上传的文件');
      return;
    }

    setIsUploading(true);
    
    // 串行上传避免服务器压力
    for (const file of pendingFiles) {
      await uploadSingleFile(file);
    }

    setIsUploading(false);
    
    const successCount = fileList.filter(f => f.status === 'success').length;
    if (successCount > 0) {
      message.success(`成功上传 ${successCount} 个文件`);
      onSuccess();
    }
  };

  const getStatusIcon = (status: FileItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'uploading':
        return <LoadingOutlined style={{ color: '#1677ff' }} />;
      default:
        return null;
    }
  };

  const pendingCount = fileList.filter(f => f.status === 'pending').length;
  const successCount = fileList.filter(f => f.status === 'success').length;
  const errorCount = fileList.filter(f => f.status === 'error').length;

  return (
    <Modal
      title={
        <Space>
          <CloudUploadOutlined style={{ color: '#1677ff' }} />
          <span>批量上传文档</span>
          <Badge count={fileList.length} showZero />
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={600}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button 
          key="upload" 
          type="primary" 
          icon={<UploadOutlined />}
          loading={isUploading}
          disabled={pendingCount === 0}
          onClick={handleBatchUpload}
        >
          开始上传 ({pendingCount})
        </Button>
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 上传区域 */}
        <Upload.Dragger
          multiple
          showUploadList={false}
          beforeUpload={() => false}
          onChange={handleFileSelect}
          accept=".pdf,.doc,.docx,.txt"
          disabled={isUploading}
        >
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined style={{ fontSize: 48, color: '#1677ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
          <p className="ant-upload-hint">
            支持 PDF、Word、TXT 格式，可一次性选择多个文件
          </p>
        </Upload.Dragger>

        {/* 状态统计 */}
        {fileList.length > 0 && (
          <Space>
            <Tag color="default">待上传 {pendingCount}</Tag>
            {successCount > 0 && <Tag color="success">成功 {successCount}</Tag>}
            {errorCount > 0 && <Tag color="error">失败 {errorCount}</Tag>}
            <Button 
              type="link" 
              size="small" 
              onClick={clearAll}
              disabled={isUploading}
            >
              清空列表
            </Button>
          </Space>
        )}

        {/* 文件列表 */}
        {fileList.length > 0 && (
          <List
            size="small"
            bordered
            style={{ maxHeight: 300, overflow: 'auto' }}
            dataSource={fileList}
            renderItem={(item) => (
              <List.Item
                actions={[
                  getStatusIcon(item.status),
                  <Tooltip title="删除">
                    <Button
                      type="text"
                      size="small"
                      icon={<CloseOutlined />}
                      onClick={() => removeFile(item.uid)}
                      disabled={item.status === 'uploading'}
                    />
                  </Tooltip>
                ]}
              >
                <List.Item.Meta
                  avatar={getFileIcon(item.name)}
                  title={<Text ellipsis style={{ maxWidth: 300 }}>{item.name}</Text>}
                  description={formatSize(item.size)}
                />
                {item.status === 'uploading' && (
                  <Progress 
                    percent={item.progress} 
                    size="small" 
                    style={{ width: 80 }}
                  />
                )}
              </List.Item>
            )}
          />
        )}
      </Space>
    </Modal>
  );
};

export default BatchUpload;