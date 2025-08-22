import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Form, Input, Card, message, Tabs, Space, Segmented } from 'antd';
import { 
  UserOutlined, 
  LockOutlined, 
  RobotOutlined, 
  FileTextOutlined, 
  ThunderboltOutlined, 
  SafetyOutlined,
  CheckCircleOutlined,
  BgColorsOutlined,
  CloudOutlined,
  StarOutlined,
  HeartOutlined,
  SunOutlined
} from '@ant-design/icons';
import { loginWithThirdParty, loginWithSystem } from '../services/authService';
import config from '../config';
import { useTheme } from '../hooks/useTheme';
import './LoginPage.css';

const { TabPane } = Tabs;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { currentTheme, setTheme, themes } = useTheme();
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
        localStorage.setItem('token', result.access_token || '');
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
      const response = await fetch(`${config.apiBaseUrl}/auth/thirdparty/url`);
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
          localStorage.setItem('token', result.access_token || '');
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
        localStorage.setItem('token', result.access_token || '');
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

  const { themeConfig } = useTheme();

  return (
    <div className="login-container" style={{ background: themeConfig.background }}>
      {/* 主题切换器 */}
      <div className="theme-switcher">
        <div className="theme-switcher-title">
          <BgColorsOutlined /> 选择主题
        </div>
        <div className="theme-options">
          {Object.entries(themes).map(([key, themeConfig]) => (
            <div
              key={key}
              className={`theme-option ${currentTheme === key ? 'active' : ''}`}
              onClick={() => setTheme(key as keyof typeof themes)}
              title={themeConfig.description}
            >
              {themeConfig.icon}
              <span>{themeConfig.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 浮动装饰元素 */}
      <div className="floating-elements">
        <div className="floating-circle"></div>
        <div className="floating-circle"></div>
        <div className="floating-circle"></div>
        <div className="floating-circle"></div>
      </div>

      {/* 主要内容区域 */}
      <div className="login-main-content">
        {/* 左侧介绍 */}
        <div className="login-left-section">
          <div className="brand-container">
            <div className="login-logo">
              <span className="logo-ai">AI</span>
              <span className="logo-docs">Docs</span>
              <span className="logo-pro">Pro</span>
            </div>
            <div className="login-subtitle">
              智能文档质量评估专家
            </div>
            <div className="login-tagline">
              让每一份文档都达到专业标准
            </div>
          </div>
          
          <div className="value-proposition">
            <div className="value-item">
              <div className="value-icon">
                <RobotOutlined />
              </div>
              <div className="value-content">
                <div className="value-title">AI深度分析</div>
                <div className="value-desc">基于大语言模型的智能文档质量评估</div>
              </div>
            </div>
            
            <div className="value-item">
              <div className="value-icon">
                <FileTextOutlined />
              </div>
              <div className="value-content">
                <div className="value-title">全格式兼容</div>
                <div className="value-desc">支持PDF、Word、Markdown等主流格式</div>
              </div>
            </div>
            
            <div className="value-item">
              <div className="value-icon">
                <CheckCircleOutlined />
              </div>
              <div className="value-content">
                <div className="value-title">专业报告</div>
                <div className="value-desc">生成结构化质量评估报告和改进建议</div>
              </div>
            </div>
          </div>
          
          <div className="trust-indicators">
            <div className="trust-item">
              <ThunderboltOutlined className="trust-icon" />
              <span>毫秒级响应</span>
            </div>
            <div className="trust-item">
              <SafetyOutlined className="trust-icon" />
              <span>企业级安全</span>
            </div>
            <div className="trust-item">
              <StarOutlined className="trust-icon" />
              <span>专业可靠</span>
            </div>
          </div>
        </div>

        {/* 右侧登录 */}
        <div className="login-right-section">
          <Card className="login-card" title="登录系统" bordered={false}>
          <Tabs defaultActiveKey="1" className="login-tabs">
            <TabPane tab="第三方登录" key="1">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button 
                  type="primary" 
                  onClick={handleThirdPartyLogin}
                  loading={loading}
                  className="login-button"
                  style={{ 
                    width: '100%',
                    background: `linear-gradient(135deg, ${themeConfig.colors.primary} 0%, ${themeConfig.colors.secondary} 100%)`,
                    boxShadow: `0 4px 15px ${themeConfig.colors.primary}40`
                  }}
                  icon={<UserOutlined />}
                >
                  第三方登录
                </Button>
                <div className="login-tips">
                  {process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost' 
                    ? '💡 开发模式：将模拟第三方登录流程' 
                    : '🔗 生产模式：将跳转到第三方认证页面'}
                </div>
              </Space>
            </TabPane>
            <TabPane tab="系统登录" key="2">
              <Form
                name="system_login"
                onFinish={handleSystemLogin}
                autoComplete="off"
                layout="vertical"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名!' }]}
                  className="login-form-item"
                >
                  <Input 
                    prefix={<UserOutlined />} 
                    placeholder="请输入用户名"
                    className="login-input"
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码!' }]}
                  className="login-form-item"
                >
                  <Input
                    prefix={<LockOutlined />}
                    type="password"
                    placeholder="请输入密码"
                    className="login-input"
                  />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    className="login-button"
                    style={{ 
                      width: '100%',
                      background: `linear-gradient(135deg, ${themeConfig.colors.primary} 0%, ${themeConfig.colors.secondary} 100%)`,
                      boxShadow: `0 4px 15px ${themeConfig.colors.primary}40`
                    }}
                  >
                    立即登录
                  </Button>
                </Form.Item>
                
                <div className="login-tips">
                  🔑 系统管理员账号: admin / admin123
                </div>
              </Form>
            </TabPane>
          </Tabs>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;