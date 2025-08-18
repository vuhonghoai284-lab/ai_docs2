import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { FileAddOutlined, UnorderedListOutlined } from '@ant-design/icons';
import TaskCreate from './pages/TaskCreate';
import TaskList from './pages/TaskList';
import TaskDetail from './pages/TaskDetail';
import './App.css';

const { Header, Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
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
          </div>
        </Header>
        <Content style={{ padding: '24px' }}>
          <Routes>
            <Route path="/" element={<TaskList />} />
            <Route path="/create" element={<TaskCreate />} />
            <Route path="/task/:id" element={<TaskDetail />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;