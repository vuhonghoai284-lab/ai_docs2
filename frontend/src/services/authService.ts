// 认证服务
import axios from 'axios';
import { User } from '../types';
import config from '../config';

const API_BASE = config.apiBaseUrl;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器，自动添加认证头
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 添加响应拦截器，处理认证错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 认证失败，清除本地存储并跳转到登录页
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginResult {
  success: boolean;
  user?: User;
  access_token?: string;
  message?: string;
}

export const loginWithThirdParty = async (code: string): Promise<LoginResult> => {
  try {
    const response = await api.post('/auth/thirdparty/login', { code });
    return {
      success: true,
      user: response.data.user,
      access_token: response.data.access_token
    };
  } catch (error: any) {
    return {
      success: false,
      message: error.response?.data?.detail || '登录失败'
    };
  }
};

export const loginWithSystem = async (username: string, password: string): Promise<LoginResult> => {
  try {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/system/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return {
      success: true,
      user: response.data.user,
      access_token: response.data.access_token
    };
  } catch (error: any) {
    return {
      success: false,
      message: error.response?.data?.detail || '登录失败'
    };
  }
};

export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await api.get('/users/me');
    return response.data;
  } catch (error) {
    return null;
  }
};

export const logout = () => {
  localStorage.removeItem('user');
  localStorage.removeItem('token');
};

export default api;