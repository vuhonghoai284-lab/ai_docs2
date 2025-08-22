import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin, message, Result } from 'antd';
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { loginWithThirdParty } from '../services/authService';

interface CallbackState {
  loading: boolean;
  success: boolean;
  error: string | null;
}

/**
 * 第三方登录回调处理组件
 * 处理从第三方认证服务重定向回来的回调请求
 */
const CallbackHandler: React.FC = () => {
  const [state, setState] = useState<CallbackState>({
    loading: true,
    success: false,
    error: null
  });
  const navigate = useNavigate();

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // 1. 从URL中获取授权码
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const error = urlParams.get('error');
      const state = urlParams.get('state');

      // 2. 检查是否有错误参数
      if (error) {
        setState({
          loading: false,
          success: false,
          error: `第三方认证失败: ${error}`
        });
        return;
      }

      // 3. 检查是否有授权码
      if (!code) {
        setState({
          loading: false,
          success: false,
          error: '未收到有效的授权码，请重新登录'
        });
        return;
      }

      console.log('收到第三方认证回调:', { code, state });

      // 4. 使用授权码进行登录
      const result = await loginWithThirdParty(code);

      if (result.success) {
        // 5. 登录成功，保存用户信息
        localStorage.setItem('user', JSON.stringify(result.user));
        localStorage.setItem('token', result.access_token || '');
        
        setState({
          loading: false,
          success: true,
          error: null
        });

        // 6. 显示成功消息并跳转
        message.success('第三方登录成功！');
        
        // 延迟跳转，让用户看到成功状态
        setTimeout(() => {
          // 检查是否有保存的跳转目标
          const preLoginLocation = sessionStorage.getItem('preLoginLocation');
          sessionStorage.removeItem('preLoginLocation');
          
          navigate(preLoginLocation || '/', { replace: true });
        }, 1500);

      } else {
        setState({
          loading: false,
          success: false,
          error: result.message || '登录失败'
        });
      }

    } catch (error) {
      console.error('第三方登录回调处理失败:', error);
      setState({
        loading: false,
        success: false,
        error: '登录过程中发生错误，请稍后重试'
      });
    }
  };

  const handleRetry = () => {
    // 返回登录页面重新尝试
    navigate('/login', { replace: true });
  };

  // 加载状态
  if (state.loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Spin 
          size="large" 
          indicator={<LoadingOutlined style={{ fontSize: 48, color: 'white' }} spin />}
        />
        <div style={{ 
          color: 'white', 
          fontSize: '18px', 
          marginTop: '24px',
          textAlign: 'center'
        }}>
          正在处理第三方登录回调...
          <br />
          <span style={{ fontSize: '14px', opacity: 0.8 }}>
            请稍候，正在验证您的身份
          </span>
        </div>
      </div>
    );
  }

  // 成功状态
  if (state.success) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'
      }}>
        <Result
          icon={<CheckCircleOutlined style={{ color: 'white', fontSize: '72px' }} />}
          title={<span style={{ color: 'white', fontSize: '24px' }}>登录成功！</span>}
          subTitle={<span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '16px' }}>
            正在跳转到主页面...
          </span>}
        />
      </div>
    );
  }

  // 错误状态
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)'
    }}>
      <Result
        icon={<CloseCircleOutlined style={{ color: 'white', fontSize: '72px' }} />}
        title={<span style={{ color: 'white', fontSize: '24px' }}>登录失败</span>}
        subTitle={<span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '16px' }}>
          {state.error}
        </span>}
        extra={
          <div style={{ textAlign: 'center' }}>
            <button
              onClick={handleRetry}
              style={{
                padding: '12px 24px',
                fontSize: '16px',
                backgroundColor: 'white',
                color: '#fc4a1a',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              }}
            >
              返回登录页面
            </button>
            <div style={{ 
              color: 'rgba(255,255,255,0.6)', 
              fontSize: '14px', 
              marginTop: '12px' 
            }}>
              您将在5秒后自动跳转到登录页面
            </div>
          </div>
        }
      />
    </div>
  );
};

export default CallbackHandler;