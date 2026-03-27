import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Documents from './pages/Documents';
import Search from './pages/Search';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import Auth from './pages/Auth';
import UserManagement from './pages/UserManagement';
import RoleManagement from './pages/RoleManagement';
import Profile from './pages/Profile';
import KnowledgeGraph from './pages/KnowledgeGraph';
import EntitySearchPage from './pages/EntitySearchPage';
import GraphManagement from './pages/GraphManagement';
import { authService } from './services/authService';
import './App.css';
import './styles/global.css';

const { Content } = Layout;

// 路由守卫组件
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// 公开路由（已登录用户跳转首页）
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

// 主布局组件
const MainLayout: React.FC<{ collapsed: boolean; setCollapsed: (v: boolean) => void }> = ({
  collapsed,
  setCollapsed,
}) => {
  return (
    <Layout style={{ 
      minHeight: '100vh', 
      background: '#f0f2f5',
    }}>
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <Layout
        style={{
          marginLeft: collapsed ? 80 : 240,
          transition: 'all 0.2s',
        }}
      >
        <Content style={{ 
          margin: 24, 
          padding: 24, 
          minHeight: 280,
        }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
            <Route path="/entity-search" element={<EntitySearchPage />} />
            <Route path="/graph-management" element={<GraphManagement />} />
            <Route path="/users" element={<UserManagement />} />
            <Route path="/roles" element={<RoleManagement />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Routes>
          {/* 登录/注册页面 */}
          <Route
            path="/auth"
            element={
              <PublicRoute>
                <Auth />
              </PublicRoute>
            }
          />

          {/* 需要登录的主布局 */}
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <MainLayout collapsed={collapsed} setCollapsed={setCollapsed} />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;