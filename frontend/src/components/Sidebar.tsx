import React, { useState } from 'react';
import { Menu, Layout, Avatar, Space, Divider, Button, Dropdown } from 'antd';
import {
  HomeOutlined, FileTextOutlined, SearchOutlined, MessageOutlined,
  BarChartOutlined, SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
  UserOutlined, TeamOutlined, SafetyOutlined, LogoutOutlined,
  ProfileOutlined, ShareAltOutlined, NodeIndexOutlined, DatabaseOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';

const { Sider } = Layout;

const Sidebar: React.FC<{ collapsed?: boolean; setCollapsed?: (v: boolean) => void }> = ({ collapsed: propCollapsed, setCollapsed: propSetCollapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [openKeys, setOpenKeys] = useState<string[]>(['/knowledge-graph']);
  
  const collapsed = propCollapsed !== undefined ? propCollapsed : internalCollapsed;
  const setCollapsed = propSetCollapsed || setInternalCollapsed;

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/documents', icon: <FileTextOutlined />, label: '文档管理' },
    { key: '/search', icon: <SearchOutlined />, label: '智能搜索' },
    { key: '/chat', icon: <MessageOutlined />, label: 'AI问答' },
    { key: '/dashboard', icon: <BarChartOutlined />, label: '数据统计' },
  ];

  const graphMenu = {
    key: '/knowledge-graph', icon: <ShareAltOutlined />, label: '知识图谱',
    children: [
      { key: '/knowledge-graph', icon: <NodeIndexOutlined />, label: '图谱可视化' },
      { key: '/entity-search', icon: <SearchOutlined />, label: '实体搜索' },
      { key: '/graph-management', icon: <DatabaseOutlined />, label: '图谱管理' },
    ],
  };

  const authMenu = {
    key: '/auth-management', icon: <SafetyOutlined />, label: '权限管理',
    children: [
      { key: '/users', icon: <UserOutlined />, label: '用户管理' },
      { key: '/roles', icon: <TeamOutlined />, label: '角色权限' },
    ],
  };

  const bottomMenu = [{ key: '/settings', icon: <SettingOutlined />, label: '系统设置' }];

  const handleLogout = async () => { await authService.logout(); navigate('/auth'); };
  const userMenu = [
    { key: 'profile', icon: <ProfileOutlined />, label: '个人中心', onClick: () => navigate('/profile') },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true, onClick: handleLogout },
  ];

  return (
    <Sider trigger={null} collapsible collapsed={collapsed} width={200}
      style={{ position: 'fixed', left: 0, top: 0, bottom: 0, height: '100vh', background: '#fff', borderRight: '1px solid #e8e8e8', zIndex: 100, overflow: 'auto' }}
    >
      {/* Logo */}
      <div style={{ height: collapsed ? 56 : 64, padding: collapsed ? '12px 8px' : '16px', borderBottom: '1px solid #e8e8e8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Avatar style={{ background: '#1890ff', fontSize: 16 }}>AI</Avatar>
          {!collapsed && <span style={{ fontWeight: 600, fontSize: 15, color: '#262626' }}>AI知识库</span>}
        </div>
      </div>

      {/* Menu */}
      <Menu mode="inline" selectedKeys={[location.pathname]} openKeys={collapsed ? [] : openKeys} onOpenChange={keys => setOpenKeys(keys)}
        style={{ border: 'none', padding: '8px 0', background: 'transparent' }}
        items={[
          ...menuItems.map(i => ({ ...i, onClick: () => navigate(i.key) })),
          { ...graphMenu, children: graphMenu.children.map(i => ({ ...i, onClick: () => navigate(i.key) })) },
          { ...authMenu, children: authMenu.children.map(i => ({ ...i, onClick: () => navigate(i.key) })) },
        ]}
      />

      <Divider style={{ margin: '8px 0' }} />

      <Menu mode="inline" selectedKeys={[location.pathname]} style={{ border: 'none', background: 'transparent' }}
        items={bottomMenu.map(i => ({ ...i, onClick: () => navigate(i.key) }))}
      />

      {/* User */}
      <div style={{ position: 'absolute', bottom: 48, left: 0, right: 0, padding: '10px 12px', borderTop: '1px solid #e8e8e8', background: '#fff' }}>
        <Dropdown menu={{ items: userMenu }} placement="topLeft" arrow>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <Avatar size={28} icon={<UserOutlined />} style={{ background: '#1890ff' }} />
            {!collapsed && <span style={{ fontSize: 12, color: '#595959' }}>管理员</span>}
          </div>
        </Dropdown>
      </div>

      {/* Collapse */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '8px', borderTop: '1px solid #e8e8e8', background: '#fff', textAlign: 'center' }}>
        <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} />
      </div>
    </Sider>
  );
};

export default Sidebar;
