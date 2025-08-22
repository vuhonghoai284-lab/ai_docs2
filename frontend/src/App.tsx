import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, message } from 'antd';
import { FileAddOutlined, UnorderedListOutlined, UserOutlined, BarChartOutlined } from '@ant-design/icons';
import TaskCreate from './pages/TaskCreate';
import TaskList from './pages/TaskList';
import TaskDetailEnhanced from './pages/TaskDetailEnhanced';
import Analytics from './pages/Analytics';
import LoginPage from './pages/LoginPage';
import CallbackHandler from './pages/CallbackHandler';
import { getCurrentUser, logout } from './services/authService';
import { User } from './types';
import { ThemeProvider } from './components/ThemeProvider';
import { useTheme } from './hooks/useTheme';
import './App.css';

const { Header, Content } = Layout;

// 认证保护组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

// 管理员权限保护组件
const AdminRoute: React.FC<{ children: React.ReactNode; user: User | null }> = ({ children, user }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (!user || (!user.is_admin && !user.is_system_admin)) {
    message.error('您没有权限访问此页面');
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
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

// 主题化Header组件
const ThemedHeader: React.FC<{ user: User | null; onLogout: () => void }> = ({ user, onLogout }) => {
  const { themeConfig } = useTheme();
  
  return (
    <Header 
      style={{ 
        background: themeConfig.background,
        borderBottom: 'none',
        position: 'fixed',
        zIndex: 1000,
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
        <h1 style={{ 
          color: 'white', 
          margin: '0 20px 0 0',
          fontSize: '20px',
          fontWeight: 'bold',
          background: 'linear-gradient(45deg, #fff, #e8f4fd)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textShadow: 'none'
        }}>
          AI文档测试系统
        </h1>
        <Menu 
          theme="dark" 
          mode="horizontal" 
          defaultSelectedKeys={['list']}
          style={{ 
            background: 'transparent',
            borderBottom: 'none',
            lineHeight: '64px'
          }}
          items={[
            {
              key: 'list',
              icon: <UnorderedListOutlined />,
              label: <Link to="/">任务列表</Link>
            },
            {
              key: 'create',
              icon: <FileAddOutlined />,
              label: <Link to="/create">创建任务</Link>
            },
            ...(user?.is_admin ? [{
              key: 'analytics',
              icon: <BarChartOutlined />,
              label: <Link to="/analytics">运营统计</Link>
            }] : [])
          ]}
        />
        {user && <UserInfo user={user} onLogout={onLogout} />}
      </div>
    </Header>
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

  // 监听storage变化，当登录状态改变时更新用户信息
  useEffect(() => {
    const handleStorageChange = async () => {
      const token = localStorage.getItem('token');
      if (token && !user) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error('获取用户信息失败', error);
        }
      } else if (!token && user) {
        setUser(null);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // 手动检查token变化（用于同一页面内的登录）
    const checkTokenInterval = setInterval(async () => {
      const token = localStorage.getItem('token');
      const userString = localStorage.getItem('user');
      
      if (token && userString && !user) {
        try {
          const storedUser = JSON.parse(userString);
          setUser(storedUser);
        } catch (error) {
          try {
            const currentUser = await getCurrentUser();
            setUser(currentUser);
          } catch (e) {
            console.error('获取用户信息失败', e);
          }
        }
      }
    }, 1000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(checkTokenInterval);
    };
  }, [user]);

  const handleLogout = () => {
    logout();
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/callback" element={<CallbackHandler />} />
      <Route path="/*" element={
        <Layout style={{ minHeight: '100vh' }}>
          <ThemedHeader user={user} onLogout={handleLogout} />
          <Content style={{ marginTop: '64px', background: '#f8fafc', minHeight: 'calc(100vh - 64px)' }}>
            <Routes>
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
              <Route 
                path="/analytics" 
                element={
                  <AdminRoute user={user}>
                    <Analytics />
                  </AdminRoute>
                } 
              />
            </Routes>
          </Content>
        </Layout>
      } />
    </Routes>
  );
};

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;