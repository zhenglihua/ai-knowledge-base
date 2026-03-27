import React, { useState } from 'react';
import { Menu, Layout, Typography, Avatar, Badge, Space, Divider, Button, Dropdown } from 'antd';
import {
  HomeOutlined,
  FileTextOutlined,
  SearchOutlined,
  MessageOutlined,
  BarChartOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RobotFilled,
  UserOutlined,
  TeamOutlined,
  SafetyOutlined,
  LogoutOutlined,
  ProfileOutlined,
  ShareAltOutlined,
  NodeIndexOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';

const { Sider } = Layout;
const { Title, Text } = Typography;

interface SidebarProps {
  collapsed?: boolean;
  setCollapsed?: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed: propCollapsed, setCollapsed: propSetCollapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [openKeys, setOpenKeys] = useState<string[]>(['/knowledge-graph']);
  
  const collapsed = propCollapsed !== undefined ? propCollapsed : internalCollapsed;
  const setCollapsed = propSetCollapsed || setInternalCollapsed;

  const menuItems = [
    { 
      key: '/', 
      icon: <HomeOutlined />, 
      label: '首页',
    },
    { 
      key: '/documents', 
      icon: <FileTextOutlined />, 
      label: '文档管理',
      badge: 2
    },
    { 
      key: '/search', 
      icon: <SearchOutlined />, 
      label: '智能搜索' 
    },
    { 
      key: '/chat', 
      icon: <MessageOutlined />, 
      label: 'AI问答',
      badge: 'New'
    },
    { 
      key: '/dashboard', 
      icon: <BarChartOutlined />, 
      label: '数据统计',
      badge: 'Hot'
    },
  ];

  // 知识图谱子菜单
  const graphMenuItems = {
    key: '/knowledge-graph',
    icon: <ShareAltOutlined />,
    label: '知识图谱',
    badge: 'New',
    children: [
      { key: '/knowledge-graph', icon: <NodeIndexOutlined />, label: '图谱可视化' },
      { key: '/entity-search', icon: <SearchOutlined />, label: '实体搜索' },
      { key: '/graph-management', icon: <DatabaseOutlined />, label: '图谱管理' },
    ],
  };

  // 权限管理子菜单
  const authMenuItems = {
    key: '/auth-management',
    icon: <SafetyOutlined />,
    label: '权限管理',
    children: [
      { key: '/users', icon: <UserOutlined />, label: '用户管理' },
      { key: '/roles', icon: <TeamOutlined />, label: '角色权限' },
    ],
  };

  const bottomMenuItems = [
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置'
    }
  ];

  // 处理退出登录
  const handleLogout = async () => {
    await authService.logout();
    navigate('/auth');
  };

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <ProfileOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: handleLogout,
    },
  ];

  // 处理子菜单展开
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  // 检查当前是否在知识图谱相关页面
  const isGraphActive = location.pathname.startsWith('/knowledge-graph') || 
                        location.pathname === '/entity-search' || 
                        location.pathname === '/graph-management';

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      theme="light"
      width={240}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        boxShadow: '2px 0 8px rgba(0,0,0,0.06)',
        zIndex: 100,
      }}
    >
      {/* Logo区域 */}
      <div style={{ 
        height: collapsed ? 64 : 140,
        padding: collapsed ? '12px 8px' : '0 16px 20px 16px',
        borderBottom: '1px solid #f0f0f0',
        textAlign: 'center',
        background: 'linear-gradient(135deg, #1677ff 0%, #0958d9 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      >
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          <Avatar 
            size={collapsed ? 40 : 56} 
            icon={<RobotFilled />} 
            style={{ 
              backgroundColor: '#fff',
              color: '#1677ff',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }} 
          />
          {!collapsed && (
            <>
              <Title level={5} style={{ margin: 0, color: '#fff' }}>
                AI知识库
              </Title>
              <Text style={{ fontSize: '12px', color: 'rgba(255,255,255,0.85)' }}>
                半导体智能工厂
              </Text>
            </>
          )}
        </Space>
      </div>

      {/* 主菜单 */}
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={handleOpenChange}
        style={{ 
          borderRight: 0,
          padding: '8px 0',
        }}
        items={[
          ...menuItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.badge ? (
              <Space>
                {item.label}
                {typeof item.badge === 'number' ? (
                  <Badge count={item.badge} size="small" />
                ) : (
                  <Badge status="processing" text={item.badge} />
                )}
              </Space>
            ) : item.label,
            onClick: () => navigate(item.key)
          })),
          {
            key: graphMenuItems.key,
            icon: graphMenuItems.icon,
            label: graphMenuItems.badge ? (
              <Space>
                {graphMenuItems.label}
                <Badge status="processing" text={graphMenuItems.badge} />
              </Space>
            ) : graphMenuItems.label,
            children: graphMenuItems.children.map(child => ({
              key: child.key,
              icon: child.icon,
              label: child.label,
              onClick: () => navigate(child.key),
            })),
          },
          {
            key: authMenuItems.key,
            icon: authMenuItems.icon,
            label: authMenuItems.label,
            children: authMenuItems.children.map(child => ({
              key: child.key,
              icon: child.icon,
              label: child.label,
              onClick: () => navigate(child.key),
            })),
          },
        ]}
      />

      <Divider style={{ margin: '8px 0' }} />

      {/* 底部菜单 */}
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ borderRight: 0 }}
        items={bottomMenuItems.map(item => ({
          key: item.key,
          icon: item.icon,
          label: item.label,
          onClick: () => navigate(item.key)
        }))}
      />

      {/* 用户信息区域 */}
      <div style={{ 
        position: 'absolute', 
        bottom: 48, 
        left: 0, 
        right: 0,
        padding: '12px 16px',
        borderTop: '1px solid #f0f0f0',
        background: '#fff',
      }}>
        <Dropdown
          menu={{ items: userMenuItems }}
          placement="topLeft"
          arrow
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer',
            gap: 12,
          }}>
            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1677ff' }} />
            {!collapsed && (
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={{ 
                  fontSize: 14, 
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  管理员
                </div>
                <div style={{ 
                  fontSize: 12, 
                  color: '#999',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  admin@example.com
                </div>
              </div>
            )}
          </div>
        </Dropdown>
      </div>

      {/* 折叠按钮 */}
      <div style={{ 
        position: 'absolute', 
        bottom: 0, 
        left: 0, 
        right: 0,
        padding: '12px',
        borderTop: '1px solid #f0f0f0',
        background: '#fff',
        textAlign: 'center'
      }}>
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed(!collapsed)}
        />
      </div>
    </Sider>
  );
};

export default Sidebar;
