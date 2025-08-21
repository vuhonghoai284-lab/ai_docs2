import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Form, Input, Card, message, Tabs, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { loginWithThirdParty, loginWithSystem } from '../services/authService';

const { TabPane } = Tabs;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // 检查URL中是否有第三方登录回调的code参数
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code) {
      // 自动处理第三方登录回调
      handleThirdPartyCallback(code);
    }
  }, []);

  const handleThirdPartyCallback = async (code: string) => {
    setLoading(true);
    try {
      const result = await loginWithThirdParty(code);
      
      if (result.success) {
        message.success('登录成功');
        localStorage.setItem('user', JSON.stringify(result.user));
        localStorage.setItem('token', result.access_token);
        // 清除URL中的code参数
        window.history.replaceState({}, document.title, window.location.pathname);
        navigate('/');
      } else {
        message.error(result.message || '登录失败');
      }
    } catch (error) {
      message.error('登录过程中发生错误');
    } finally {
      setLoading(false);
    }
  };

  const handleThirdPartyLogin = async () => {
    setLoading(true);
    try {
      // 1. 获取第三方认证URL
      const response = await fetch('http://localhost:8080/api/auth/thirdparty/url');
      const { auth_url } = await response.json();
      
      // 2. 检查是否是开发/测试环境
      const isDevelopment = process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost';
      
      if (isDevelopment) {
        // 开发/测试环境：模拟第三方认证流程
        // 生成模拟的authorization code
        const mockCode = `mock_auth_code_${Date.now()}`;
        
        // 直接使用模拟code进行登录（业务流程与生产环境完全一致）
        const result = await loginWithThirdParty(mockCode);
        
        if (result.success) {
          message.success('登录成功（测试模式）');
          localStorage.setItem('user', JSON.stringify(result.user));
          localStorage.setItem('token', result.access_token);
          navigate('/');
        } else {
          message.error(result.message || '登录失败');
        }
      } else {
        // 生产环境：跳转到真实的第三方认证页面
        // 保存当前页面状态，以便认证后返回
        sessionStorage.setItem('preLoginLocation', window.location.pathname);
        
        // 跳转到第三方认证页面
        window.location.href = auth_url;
      }
    } catch (error) {
      console.error('第三方登录错误:', error);
      message.error('登录过程中发生错误');
    } finally {
      setLoading(false);
    }
  };

  const handleSystemLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await loginWithSystem(values.username, values.password);
      
      if (result.success) {
        message.success('登录成功');
        // 保存用户信息和token到localStorage
        localStorage.setItem('user', JSON.stringify(result.user));
        localStorage.setItem('token', result.access_token);
        // 跳转到主页
        navigate('/');
      } else {
        message.error(result.message || '登录失败');
      }
    } catch (error) {
      message.error('登录过程中发生错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#f0f2f5'
    }}>
      <Card style={{ width: 400 }} title="AI文档测试系统" bordered={false}>
        <Tabs defaultActiveKey="1">
          <TabPane tab="第三方登录" key="1">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="primary" 
                onClick={handleThirdPartyLogin}
                loading={loading}
                style={{ width: '100%' }}
              >
                第三方登录
              </Button>
              <p style={{ textAlign: 'center', fontSize: '12px', color: '#999' }}>
                {process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost' 
                  ? '开发模式：将模拟第三方登录流程' 
                  : '生产模式：将跳转到第三方认证页面'}
              </p>
            </Space>
          </TabPane>
          <TabPane tab="系统登录" key="2">
            <Form
              name="system_login"
              onFinish={handleSystemLogin}
              autoComplete="off"
            >
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名!' }]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="用户名" 
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码!' }]}
              >
                <Input
                  prefix={<LockOutlined />}
                  type="password"
                  placeholder="密码"
                />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  style={{ width: '100%' }}
                >
                  登录
                </Button>
              </Form.Item>
              
              <p style={{ textAlign: 'center', fontSize: '12px', color: '#999' }}>
                系统管理员账号: admin / admin123
              </p>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default LoginPage;