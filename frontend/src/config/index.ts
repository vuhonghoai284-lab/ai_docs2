/**
 * 应用配置管理
 */

interface AppConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  appTitle: string;
  appVersion: string;
  isDev: boolean;
  isProd: boolean;
}

// 从环境变量获取配置
const config: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8080',
  appTitle: import.meta.env.VITE_APP_TITLE || 'AI文档测试系统',
  appVersion: import.meta.env.VITE_APP_VERSION || '2.0.0',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
};

// 验证必要的配置
if (!config.apiBaseUrl) {
  throw new Error('VITE_API_BASE_URL is required');
}

if (!config.wsBaseUrl) {
  throw new Error('VITE_WS_BASE_URL is required');
}

// 日志配置信息（仅开发环境）
if (config.isDev) {
  console.log('应用配置:', {
    apiBaseUrl: config.apiBaseUrl,
    wsBaseUrl: config.wsBaseUrl,
    appTitle: config.appTitle,
    appVersion: config.appVersion,
    environment: config.isDev ? '开发环境' : '生产环境',
  });
}

export default config;