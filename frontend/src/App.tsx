import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, message } from 'antd';
import { FileAddOutlined, UnorderedListOutlined, UserOutlined } from '@ant-design/icons';
import TaskCreate from './pages/TaskCreate';
import TaskList from './pages/TaskList';
import TaskDetailEnhanced from './pages/TaskDetailEnhanced';
import LoginPage from './pages/LoginPage';
import { getCurrentUser, logout } from './services/authService';
import { User } from './types';
import './App.css';

const { Header, Content } = Layout;

// 认证保护组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

// 用户信息组件
const UserInfo: React.FC<{ user: User; onLogout: () => void }> = ({ user, onLogout }) => {
  const menuItems = [
    {
      key: 'logout',
      label: '退出登录',
      onClick: onLogout,
    },
  ];

  return (
    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
      <Dropdown menu={{ items: menuItems }} placement="bottomRight">
        <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
          {user.avatar_url ? (
            <Avatar src={user.avatar_url} />
          ) : (
            <Avatar icon={<UserOutlined />} />
          )}
          <span style={{ color: 'white', marginLeft: 8 }}>
            {user.display_name || user.uid}
            {user.is_admin && ' (管理员)'}
            {user.is_system_admin && ' (系统管理员)'}
          </span>
        </div>
      </Dropdown>
    </div>
  );
};

// 主应用组件
const AppContent: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          message.error('获取用户信息失败');
          handleLogout();
        }
      }
      setLoading(false);
    };

    initUser();
  }, []);

  const handleLogout = () => {
    logout();
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {user ? (
        <Header>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <h1 style={{ color: 'white', margin: '0 20px 0 0' }}>AI文档测试系统</h1>
            <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['list']}>
              <Menu.Item key="list" icon={<UnorderedListOutlined />}>
                <Link to="/">任务列表</Link>
              </Menu.Item>
              <Menu.Item key="create" icon={<FileAddOutlined />}>
                <Link to="/create">创建任务</Link>
              </Menu.Item>
            </Menu>
            <UserInfo user={user} onLogout={handleLogout} />
          </div>
        </Header>
      ) : null}
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <TaskList />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/create" 
            element={
              <ProtectedRoute>
                <TaskCreate />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/task/:id" 
            element={
              <ProtectedRoute>
                <TaskDetailEnhanced />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Content>
    </Layout>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;