import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Card,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  Switch,
  message,
  Popconfirm,
  Avatar,
  Tooltip,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  UserOutlined,
  LockOutlined,
  UnlockOutlined,
  KeyOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { userService } from '../services/userService';
import { roleService } from '../services/roleService';
import { User, Role } from '../types/auth';

const { Option } = Select;

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentUser, setCurrentUser] = useState<Partial<User>>({});
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [form] = Form.useForm();
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
  });

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [usersData, rolesData] = await Promise.all([
        userService.getUsers(),
        roleService.getRoles(),
      ]);
      setUsers(usersData);
      setRoles(rolesData);
      setStats({
        total: usersData.length,
        active: usersData.filter(u => u.status === 'active').length,
        inactive: usersData.filter(u => u.status === 'inactive').length,
      });
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 搜索用户
  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await userService.getUsers({ keyword: searchKeyword });
      setUsers(data);
    } catch (error) {
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  // 打开新增弹窗
  const handleAdd = () => {
    setIsEdit(false);
    setCurrentUser({});
    form.resetFields();
    setIsModalVisible(true);
  };

  // 打开编辑弹窗
  const handleEdit = (record: User) => {
    setIsEdit(true);
    setCurrentUser(record);
    form.setFieldsValue({
      ...record,
      roleIds: record.roles?.map(r => r.id),
    });
    setIsModalVisible(true);
  };

  // 保存用户
  const handleSave = async (values: any) => {
    try {
      const roleIds = values.roleIds || [];
      delete values.roleIds;
      
      if (isEdit && currentUser.id) {
        await userService.updateUser(currentUser.id, values);
        await userService.assignRoles(currentUser.id, roleIds);
        message.success('更新成功');
      } else {
        const newUser = await userService.createUser(values);
        await userService.assignRoles(newUser.id, roleIds);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      loadData();
    } catch (error: any) {
      message.error(error.message || '保存失败');
    }
  };

  // 删除用户
  const handleDelete = async (id: string) => {
    try {
      await userService.deleteUser(id);
      message.success('删除成功');
      loadData();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  // 批量删除
  const handleBatchDelete = async () => {
    try {
      await userService.batchDeleteUser(selectedRowKeys as string[]);
      message.success('批量删除成功');
      setSelectedRowKeys([]);
      loadData();
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  // 切换用户状态
  const handleToggleStatus = async (record: User) => {
    try {
      const newStatus = record.status === 'active' ? 'inactive' : 'active';
      await userService.updateUserStatus(record.id, newStatus);
      message.success(`已${newStatus === 'active' ? '启用' : '禁用'}用户`);
      loadData();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 重置密码
  const handleResetPassword = async (id: string) => {
    try {
      const newPassword = await userService.resetPassword(id);
      Modal.success({
        title: '密码重置成功',
        content: `新密码为：${newPassword}，请尽快告知用户修改`,
      });
    } catch (error) {
      message.error('重置密码失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<User> = [
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} style={{ backgroundColor: record.status === 'active' ? '#1677ff' : '#999' }} />
          <div>
            <div>{record.realName || record.username}</div>
            <div style={{ fontSize: 12, color: '#999' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (dept) => dept || '-',
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: Role[]) => (
        <Space wrap>
          {roles?.map(role => (
            <Tag key={role.id} color={role.code === 'super_admin' ? 'red' : 'blue'}>
              {role.name}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '正常' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'lastLoginAt',
      key: 'lastLoginAt',
      render: (time) => time || '从未登录',
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '禁用' : '启用'}>
            <Button
              type="text"
              icon={record.status === 'active' ? <LockOutlined /> : <UnlockOutlined />}
              onClick={() => handleToggleStatus(record)}
            />
          </Tooltip>
          <Tooltip title="重置密码">
            <Button
              type="text"
              icon={<KeyOutlined />}
              onClick={() => handleResetPassword(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description="删除后无法恢复，是否继续？"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="总用户数" value={stats.total} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="正常用户" value={stats.active} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="禁用用户" value={stats.inactive} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
      </Row>

      <Card
        title="用户管理"
        extra={
          <Space>
            <Input
              placeholder="搜索用户名/姓名/邮箱"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onPressEnter={handleSearch}
              suffix={<SearchOutlined />}
              style={{ width: 250 }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title="确认批量删除"
                description={`确定删除选中的 ${selectedRowKeys.length} 个用户？`}
                onConfirm={handleBatchDelete}
              >
                <Button danger>批量删除</Button>
              </Popconfirm>
            )}
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增用户
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={users}
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={isEdit ? '编辑用户' : '新增用户'}
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input disabled={isEdit} placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="realName"
                label="真实姓名"
              >
                <Input placeholder="请输入真实姓名" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '邮箱格式不正确' },
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
              >
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="department"
            label="部门"
          >
            <Select placeholder="请选择部门">
              <Option value="技术部">技术部</Option>
              <Option value="研发部">研发部</Option>
              <Option value="运营部">运营部</Option>
              <Option value="市场部">市场部</Option>
              <Option value="人事部">人事部</Option>
              <Option value="财务部">财务部</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="roleIds"
            label="角色"
            rules={[{ required: true, message: '请至少选择一个角色' }]}
          >
            <Select mode="multiple" placeholder="请选择角色">
              {roles.map(role => (
                <Option key={role.id} value={role.id}>{role.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            valuePropName="checked"
            getValueFromEvent={(checked) => checked ? 'active' : 'inactive'}
            getValueProps={(value) => ({ checked: value === 'active' })}
          >
            <Switch checkedChildren="正常" unCheckedChildren="禁用" />
          </Form.Item>

          {!isEdit && (
            <Form.Item
              name="password"
              label="初始密码"
              rules={[{ required: true, message: '请输入初始密码' }]}
            >
              <Input.Password placeholder="请输入初始密码" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;