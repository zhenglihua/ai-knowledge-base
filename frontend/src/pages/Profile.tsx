import React, { useState, useEffect } from 'react';
import {
  Card,
  Avatar,
  Descriptions,
  Button,
  Form,
  Input,
  message,
  Tabs,
  List,
  Tag,
  Space,
  Modal,
  Row,
  Col,
  Timeline,
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  LockOutlined,
  SafetyOutlined,
  HistoryOutlined,
  MailOutlined,
  PhoneOutlined,
  TeamOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { authService } from '../services/authService';
import { User } from '../types/auth';

const { TabPane } = Tabs;

const Profile: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [infoForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  // 加载用户信息
  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    const currentUser = await authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser as User);
      infoForm.setFieldsValue(currentUser);
    }
  };

  // 更新个人信息
  const handleUpdateInfo = async (values: any) => {
    setLoading(true);
    try {
      await authService.updateUserInfo(values);
      message.success('个人信息更新成功');
      setIsEditing(false);
      loadUserInfo();
    } catch (error: any) {
      message.error(error.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values: any) => {
    setLoading(true);
    try {
      await authService.changePassword(values.oldPassword, values.newPassword);
      message.success('密码修改成功');
      passwordForm.resetFields();
      setPasswordModalVisible(false);
    } catch (error: any) {
      message.error(error.message || '密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  // 模拟登录历史
  const loginHistory = [
    { time: '2024-01-15 14:30:00', ip: '192.168.1.100', device: 'Chrome / macOS', status: 'success' },
    { time: '2024-01-14 09:15:00', ip: '192.168.1.100', device: 'Chrome / macOS', status: 'success' },
    { time: '2024-01-13 18:45:00', ip: '192.168.1.105', device: 'Safari / iOS', status: 'success' },
    { time: '2024-01-12 08:30:00', ip: '192.168.1.100', device: 'Chrome / macOS', status: 'success' },
    { time: '2024-01-10 20:10:00', ip: '10.0.0.50', device: 'Firefox / Windows', status: 'failed' },
  ];

  // 基本信息卡片
  const renderBasicInfo = () => (
    <Card
      title="基本信息"
      extra={
        <Button
          type={isEditing ? 'default' : 'primary'}
          icon={<EditOutlined />}
          onClick={() => setIsEditing(!isEditing)}
        >
          {isEditing ? '取消' : '编辑'}
        </Button>
      }
    >
      {isEditing ? (
        <Form
          form={infoForm}
          layout="vertical"
          onFinish={handleUpdateInfo}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="realName"
                label="真实姓名"
              >
                <Input prefix={<UserOutlined />} placeholder="请输入真实姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
              >
                <Input disabled prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[{ type: 'email', message: '邮箱格式不正确' }]}
              >
                <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
              >
                <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="department"
            label="部门"
          >
            <Input prefix={<TeamOutlined />} placeholder="请输入部门" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      ) : (
        <Descriptions column={2}>
          <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
          <Descriptions.Item label="真实姓名">{user?.realName || '-'}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="手机号">{user?.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="部门">{user?.department || '-'}</Descriptions.Item>
          <Descriptions.Item label="注册时间">{user?.createdAt}</Descriptions.Item>
          <Descriptions.Item label="最后登录">{user?.lastLoginAt || '从未登录'}</Descriptions.Item>
          <Descriptions.Item label="账户状态">
            <Tag color={user?.status === 'active' ? 'success' : 'error'}>
              {user?.status === 'active' ? '正常' : '禁用'}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      )}
    </Card>
  );

  // 角色权限卡片
  const renderRoles = () => (
    <Card title="我的角色权限">
      <List
        dataSource={user?.roles || []}
        renderItem={(role) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space>
                  <Tag color={role.code === 'super_admin' ? 'red' : 'blue'}>{role.name}</Tag>
                  <span style={{ color: '#999' }}>{role.code}</span>
                </Space>
              }
              description={role.description}
            />
            <Tag color="cyan">{role.permissions?.length || 0} 项权限</Tag>
          </List.Item>
        )}
      />
    </Card>
  );

  // 安全设置卡片
  const renderSecurity = () => (
    <Card title="安全设置">
      <List>
        <List.Item>
          <List.Item.Meta
            avatar={<Avatar icon={<LockOutlined />} />}
            title="登录密码"
            description="定期修改密码可以保护账户安全"
          />
          <Button onClick={() => setPasswordModalVisible(true)}>修改密码</Button>
        </List.Item>
        <List.Item>
          <List.Item.Meta
            avatar={<Avatar icon={<SafetyOutlined />} style={{ backgroundColor: '#52c41a' }} />}
            title="双重验证"
            description="开启后登录需要手机验证码"
          />
          <Button>开启</Button>
        </List.Item>
        <List.Item>
          <List.Item.Meta
            avatar={<Avatar icon={<HistoryOutlined />} style={{ backgroundColor: '#722ed1' }} />}
            title="登录设备管理"
            description="查看和管理已登录的设备"
          />
          <Button>查看</Button>
        </List.Item>
      </List>
    </Card>
  );

  // 登录历史
  const renderLoginHistory = () => (
    <Card title="登录历史">
      <Timeline mode="left">
        {loginHistory.map((record, index) => (
          <Timeline.Item
            key={index}
            dot={<ClockCircleOutlined style={{ fontSize: '16px' }} />}
            color={record.status === 'success' ? 'green' : 'red'}
            label={record.time}
          >
            <div>
              <div>{record.device}</div>
              <div style={{ color: '#999', fontSize: '12px' }}>IP: {record.ip}</div>
              <Tag color={record.status === 'success' ? 'success' : 'error'}>
                {record.status === 'success' ? '成功' : '失败'}
              </Tag>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    </Card>
  );

  return (
    <div>
      <Row gutter={[24, 24]}>
        <Col span={8}>
          <Card style={{ textAlign: 'center' }}>
            <Avatar
              size={120}
              icon={<UserOutlined />}
              style={{ backgroundColor: '#1677ff', marginBottom: 16 }}
            />
            <div style={{ marginBottom: 8 }}>
              <h3 style={{ margin: 0 }}>{user?.realName || user?.username}</h3>
            </div>
            <div style={{ marginBottom: 16 }}>
              {user?.roles?.map(role => (
                <Tag key={role.id} color={role.code === 'super_admin' ? 'red' : 'blue'}>
                  {role.name}
                </Tag>
              ))}
            </div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button type="primary" block icon={<EditOutlined />} onClick={() => setIsEditing(true)}>
                编辑资料
              </Button>
              <Button block icon={<LockOutlined />} onClick={() => setPasswordModalVisible(true)}>
                修改密码
              </Button>
            </Space>
          </Card>

          {renderSecurity()}
        </Col>

        <Col span={16}>
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              {renderBasicInfo()}
              <div style={{ marginTop: 24 }}>
                {renderRoles()}
              </div>
            </TabPane>
            <TabPane tab="登录历史" key="2">
              {renderLoginHistory()}
            </TabPane>
          </Tabs>
        </Col>
      </Row>

      {/* 修改密码弹窗 */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onOk={() => passwordForm.submit()}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="oldPassword"
            label="原密码"
            rules={[{ required: true, message: '请输入原密码' }]}
          >
            <Input.Password placeholder="请输入原密码" />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Profile;