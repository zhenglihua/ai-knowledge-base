import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Tabs,
  message,
  Space,
  Divider,
  Checkbox,
  Row,
  Col,
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

const { Title, Text, Link } = Typography;

interface LoginFormData {
  username: string;
  password: string;
  remember: boolean;
}

interface RegisterFormData {
  username: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;
  agreement: boolean;
}

const Auth: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('login');
  const [loginLoading, setLoginLoading] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  // 处理登录
  const handleLogin = async (values: LoginFormData) => {
    setLoginLoading(true);
    try {
      await authService.login({
        username: values.username,
        password: values.password,
      });
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败');
    } finally {
      setLoginLoading(false);
    }
  };

  // 处理注册
  const handleRegister = async (values: RegisterFormData) => {
    setRegisterLoading(true);
    try {
      await authService.register({
        username: values.username,
        email: values.email,
        phone: values.phone,
        password: values.password,
      });
      message.success('注册成功！请登录');
      setActiveTab('login');
      registerForm.resetFields();
    } catch (error: any) {
      message.error(error.message || '注册失败');
    } finally {
      setRegisterLoading(false);
    }
  };

  // 登录表单
  const loginFormContent = (
    <Form
      form={loginForm}
      name="login"
      onFinish={handleLogin}
      autoComplete="off"
      size="large"
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="用户名"
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="密码"
        />
      </Form.Item>

      <Form.Item>
        <Row justify="space-between" align="middle">
          <Col>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
          </Col>
          <Col>
            <Link href="#">忘记密码？</Link>
          </Col>
        </Row>
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          block
          loading={loginLoading}
          size="large"
        >
          登 录
        </Button>
      </Form.Item>

      <div style={{ textAlign: 'center' }}>
        <Text type="secondary">演示账号：admin / 123456 或 user / 123456</Text>
      </div>
    </Form>
  );

  // 注册表单
  const registerFormContent = (
    <Form
      form={registerForm}
      name="register"
      onFinish={handleRegister}
      autoComplete="off"
      size="large"
    >
      <Form.Item
        name="username"
        rules={[
          { required: true, message: '请输入用户名' },
          { min: 3, message: '用户名至少3个字符' },
          { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="用户名"
        />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '请输入有效的邮箱地址' },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="邮箱"
        />
      </Form.Item>

      <Form.Item
        name="phone"
        rules={[
          { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' },
        ]}
      >
        <Input
          prefix={<PhoneOutlined />}
          placeholder="手机号（可选）"
        />
      </Form.Item>

      <Form.Item
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6个字符' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="密码"
        />
      </Form.Item>

      <Form.Item
        name="confirmPassword"
        dependencies={['password']}
        rules={[
          { required: true, message: '请确认密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致'));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<SafetyOutlined />}
          placeholder="确认密码"
        />
      </Form.Item>

      <Form.Item
        name="agreement"
        valuePropName="checked"
        rules={[
          {
            validator: (_, value) =>
              value ? Promise.resolve() : Promise.reject(new Error('请同意用户协议')),
          },
        ]}
      >
        <Checkbox>
          我已阅读并同意<Link href="#">《用户协议》</Link>和<Link href="#">《隐私政策》</Link>
        </Checkbox>
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          block
          loading={registerLoading}
          size="large"
        >
          注 册
        </Button>
      </Form.Item>
    </Form>
  );

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '24px',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 480,
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}
        bodyStyle={{ padding: '40px' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ margin: 0, color: '#1677ff' }}>
            AI 知识库系统
          </Title>
          <Text type="secondary">半导体智能工厂 · 用户认证</Text>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          centered
          style={{ color: '#c9d1d9' }}
          items={[
            {
              key: 'login',
              label: '账号登录',
              children: loginFormContent,
            },
            {
              key: 'register',
              label: '用户注册',
              children: registerFormContent,
            },
          ]}
        />

        <Divider>其他方式</Divider>

        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Button block icon={<span>📧</span>}>企业微信登录</Button>
          <Button block icon={<span>💼</span>}>钉钉登录</Button>
        </Space>
      </Card>
    </div>
  );
};

export default Auth;