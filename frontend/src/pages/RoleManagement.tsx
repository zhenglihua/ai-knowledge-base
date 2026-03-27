"""
权限管理页面 - 角色权限管理
"""

import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Switch, Space, Tag, Tree, message, Card, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const RoleManagement: React.FC = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const [selectedPerms, setSelectedPerms] = useState<string[]>([]);
  const [editingRole, setEditingRole] = useState<any>(null);
  const [form] = Form.useForm();

  // 权限树形结构数据
  const permissionTreeData = [
    {
      title: '文档管理',
      key: 'doc',
      children: [
        { title: '查看文档', key: 'doc:read' },
        { title: '上传文档', key: 'doc:upload' },
        { title: '编辑文档', key: 'doc:edit' },
        { title: '删除文档', key: 'doc:delete' },
        { title: '下载文档', key: 'doc:download' },
      ],
    },
    {
      title: '知识图谱',
      key: 'kg',
      children: [
        { title: '查看图谱', key: 'kg:read' },
        { title: '编辑图谱', key: 'kg:edit' },
        { title: '删除实体', key: 'kg:delete' },
      ],
    },
    {
      title: 'AI问答',
      key: 'chat',
      children: [
        { title: '发起问答', key: 'chat:create' },
        { title: '查看历史', key: 'chat:read' },
        { title: '删除记录', key: 'chat:delete' },
      ],
    },
    {
      title: '系统管理',
      key: 'system',
      children: [
        { title: '用户管理', key: 'system:user' },
        { title: '角色管理', key: 'system:role' },
        { title: '权限配置', key: 'system:permission' },
        { title: '审计日志', key: 'system:audit' },
        { title: '系统设置', key: 'system:config' },
      ],
    },
  ];

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/auth/roles');
      const data = await res.json();
      setRoles(data.data || []);
    } catch (error) {
      message.error('加载角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingRole(null);
    setSelectedPerms([]);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = async (record: any) => {
    setEditingRole(record);
    try {
      const res = await fetch(`/api/auth/roles/${record.id}/permissions`);
      const data = await res.json();
      setSelectedPerms(data.data?.map((p: any) => p.code) || []);
    } catch (error) {
      console.error(error);
    }
    form.setFieldsValue({
      name: record.name,
      code: record.code,
      description: record.description,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const url = editingRole 
        ? `/api/auth/roles/${editingRole.id}` 
        : '/api/auth/roles';
      const method = editingRole ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...values,
          permission_ids: selectedPerms.map(code => {
            // 这里需要将code转换为id，实际应根据API调整
            return code;
          }),
        }),
      });
      message.success(editingRole ? '更新成功' : '创建成功');
      setModalVisible(false);
      loadRoles();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: '角色名称', dataIndex: 'name', key: 'name' },
    { title: '角色代码', dataIndex: 'code', key: 'code' },
    { title: '描述', dataIndex: 'description', key: 'description' },
    { 
      title: '状态', 
      dataIndex: 'is_enabled', 
      key: 'is_enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      )
    },
    { 
      title: '权限数', 
      dataIndex: 'permission_count', 
      key: 'permission_count',
      render: (count: number) => <Tag>{count}</Tag>
    },
    { 
      title: '用户数', 
      dataIndex: 'user_count', 
      key: 'user_count',
      render: (count: number) => <Tag color="blue">{count}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          {!record.is_system && (
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>角色权限管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增角色
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={roles} 
        loading={loading}
        rowKey="id"
        pagination={false}
      />

      <Modal
        title={editingRole ? '编辑角色' : '新增角色'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="角色名称" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="code" label="角色代码" rules={[{ required: true }]}>
                <Input disabled={!!editingRole} />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          
          <Form.Item label="权限配置">
            <Tree
              checkable
              defaultExpandAll
              checkedKeys={selectedPerms}
              onCheck={(keys: any) => setSelectedPerms(keys)}
              treeData={permissionTreeData}
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RoleManagement;
