/*
权限管理页面 - 用户管理
*/

import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, Space, Tag, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { userService } from '../services/userService';

const { Option } = Select;

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [form] = Form.useForm();

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await userService.getUsers();
      setUsers(res || []);
    } catch (error) {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: any) => {
    setEditingUser(record);
    form.setFieldsValue({
      username: record.username,
      email: record.email,
      phone: record.phone,
      real_name: record.real_name,
      status: record.status,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await userService.deleteUser(id);
      message.success('删除成功');
      loadUsers();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, values);
        message.success('更新成功');
      } else {
        await userService.createUser(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'real_name', key: 'real_name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '手机', dataIndex: 'phone', key: 'phone' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '正常' : '禁用'}
        </Tag>
      )
    },
    { 
      title: '角色', 
      dataIndex: 'roles', 
      key: 'roles',
      render: (roles: any[]) => roles?.map(r => <Tag key={r.id}>{r.name}</Tag>)
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>用户管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增用户
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={users} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input disabled={!!editingUser} />
          </Form.Item>
          
          {!editingUser && (
            <>
              <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
                <Input />
              </Form.Item>
            </>
          )}
          
          <Form.Item name="real_name" label="真实姓名">
            <Input />
          </Form.Item>
          
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          
          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
              <Option value="active">正常</Option>
              <Option value="inactive">禁用</Option>
              <Option value="locked">锁定</Option>
            </Select>
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

export default UserManagement;
