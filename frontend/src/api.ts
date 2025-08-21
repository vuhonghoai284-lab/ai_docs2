// API服务封装
import axios from 'axios';
import { Task, TaskDetail, AIOutput } from './types';
import config from './config';

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

export const taskAPI = {
  // 创建任务
  createTask: async (file: File, title?: string, modelIndex?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    if (modelIndex !== undefined) {
      formData.append('model_index', modelIndex.toString());
    }
    
    const response = await api.post<Task>('/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 获取任务列表
  getTasks: async () => {
    const response = await api.get<Task[]>('/tasks');
    return response.data;
  },

  // 获取任务详情
  getTaskDetail: async (taskId: number) => {
    const response = await api.get<TaskDetail>(`/tasks/${taskId}`);
    return response.data;
  },

  // 删除任务
  deleteTask: async (taskId: number) => {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  },

  // 提交问题反馈
  submitFeedback: async (issueId: number, feedbackType: string, comment?: string) => {
    const response = await api.put(`/issues/${issueId}/feedback`, {
      feedback_type: feedbackType,
      comment,
    });
    return response.data;
  },

  // 下载报告
  downloadReport: async (taskId: number) => {
    const response = await api.get(`/tasks/${taskId}/report`, {
      responseType: 'blob',
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `report_${taskId}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // 获取任务的AI输出记录
  getTaskAIOutputs: async (taskId: number, operationType?: string) => {
    const params = operationType ? { operation_type: operationType } : {};
    const response = await api.get<AIOutput[]>(`/tasks/${taskId}/ai-outputs`, { params });
    return response.data;
  },

  // 获取单个AI输出详情
  getAIOutputDetail: async (outputId: number) => {
    const response = await api.get<AIOutput>(`/ai-outputs/${outputId}`);
    return response.data;
  },

  // 重试任务
  retryTask: async (taskId: number) => {
    const response = await api.post(`/tasks/${taskId}/retry`);
    return response.data;
  },
};