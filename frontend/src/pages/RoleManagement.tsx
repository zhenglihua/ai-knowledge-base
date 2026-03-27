import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Card,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Tree,
  message,
  Popconfirm,
  Descriptions,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SafetyOutlined,
  UserOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { roleService } from '../services/roleService';
import { Role, Permission } from '../types/auth';

const RoleManagement: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [permissionsByModule, setPermissionsByModule] = useState<Record<string, Permission[]>>({});
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isPermissionModalVisible, setIsPermissionModalVisible] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentRole, setCurrentRole] = useState<Partial<Role>>({});
  const [selectedPermissionIds, setSelectedPermissionIds] = useState<string[]>([]);
  const [form] = Form.useForm();

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [rolesData, permissionsData, groupedPermissions] = await Promise.all([
        roleService.getRoles(),
        roleService.getAllPermissions(),
        roleService.getPermissionsByModule(),
      ]);
      setRoles(rolesData);
      setPermissions(permissionsData);
      setPermissionsByModule(groupedPermissions);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 打开新增弹窗
  const handleAdd = () => {
    setIsEdit(false);
    setCurrentRole({});
    form.resetFields();
    setIsModalVisible(true);
  };

  // 打开编辑弹窗
  const handleEdit = (record: Role) => {
    setIsEdit(true);
    setCurrentRole(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  // 打开权限配置弹窗
  const handleConfigPermissions = (record: Role) => {
    setCurrentRole(record);
    setSelectedPermissionIds(record.permissions?.map(p => p.id) || []);
    setIsPermissionModalVisible(true);
  };

  // 保存角色
  const handleSave = async (values: any) => {
    try {
      if (isEdit && currentRole.id) {
        await roleService.updateRole(currentRole.id, values);
        message.success('更新成功');
      } else {
        await roleService.createRole(values);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      loadData();
    } catch (error: any) {
      message.error(error.message || '保存失败');
    }
  };

  // 删除角色
  const handleDelete = async (id: string) => {
    try {
      await roleService.deleteRole(id);
      message.success('删除成功');
      loadData();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  // 保存权限配置
  const handleSavePermissions = async () => {
    try {
      if (currentRole.id) {
        await roleService.updateRolePermissions(currentRole.id, selectedPermissionIds);
        message.success('权限配置保存成功');
        setIsPermissionModalVisible(false);
        loadData();
      }
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 构建权限树
  const buildPermissionTree = () => {
    const moduleNames: Record<string, string> = {
      system: '系统管理',
      document: '文档管理',
      ai: 'AI功能',
      stats: '数据统计',
    };

    return Object.entries(permissionsByModule).map(([module, perms]) => ({
      title: moduleNames[module] || module,
      key: `module-${module}`,
      children: perms.map(p => ({
        title: `${p.name} (${p.code})`,
        key: p.id,
      })),
    }));
  };

  // 表格列定义
  const columns: ColumnsType<Role> = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Tag color={record.code === 'super_admin' ? 'red' : 'blue'}>{text}</Tag>
          <Tag>{record.code}</Tag>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '权限数量',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => (
        <Tag color="cyan">{permissions?.length || 0} 项权限</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 250,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<SafetyOutlined />}
            onClick={() => handleConfigPermissions(record)}
          >
            权限配置
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled={record.code === 'super_admin'}
          />
          <Popconfirm
            title="确认删除"
            description="删除后无法恢复，是否继续？"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />}
              disabled={record.code === 'super_admin'}
            />
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
            <Statistic title="角色总数" value={roles.length} prefix={<SafetyOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="启用角色" 
              value={roles.filter(r => r.status === 'active').length} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<SafetyOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="总权限数" 
              value={permissions.length}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="角色权限管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增角色
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={roles}
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 角色表单弹窗 */}
      <Modal
        title={isEdit ? '编辑角色' : '新增角色'}
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsModalVisible(false)}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称，如：普通用户" />
          </Form.Item>

          <Form.Item
            name="code"
            label="角色代码"
            rules={[
              { required: true, message: '请输入角色代码' },
              { pattern: /^[a-z_]+$/, message: '角色代码只能使用小写字母和下划线' },
            ]}
          >
            <Input disabled={isEdit} placeholder="请输入角色代码，如：normal_user" />
          </Form.Item>

          <Form.Item
            name="description"
            label="角色描述"
          >
            <Input.TextArea rows={3} placeholder="请输入角色描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 权限配置弹窗 */}
      <Modal
        title={`配置权限 - ${currentRole.name}`}
        open={isPermissionModalVisible}
        onOk={handleSavePermissions}
        onCancel={() => setIsPermissionModalVisible(false)}
        width={600}
      >
        <Descriptions column={2} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="角色代码">{currentRole.code}</Descriptions.Item>
          <Descriptions.Item label="当前权限数">{selectedPermissionIds.length} 项</Descriptions.Item>
        </Descriptions>

        <Card title="选择权限" size="small">
          <Tree
            checkable
            checkedKeys={selectedPermissionIds}
            onCheck={(checked) => {
              setSelectedPermissionIds(checked as string[]);
            }}
            treeData={buildPermissionTree()}
            defaultExpandAll
          />
        </Card>
      </Modal>
    </div>
  );
};

export default RoleManagement;