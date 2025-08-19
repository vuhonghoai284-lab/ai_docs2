import React, { useState, useEffect } from 'react';
import { Card, Upload, Button, Input, message, Progress, Space, Tag, Select, Tooltip } from 'antd';
import { InboxOutlined, LoadingOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { taskAPI } from '../api';
import { useNavigate } from 'react-router-dom';

const { Dragger } = Upload;
const { Option } = Select;

interface UploadTask {
  file: File;
  status: 'uploading' | 'success' | 'error';
  taskId?: number;
  error?: string;
}

interface ModelInfo {
  index: number;
  label: string;
  description: string;
  provider: string;
  is_default: boolean;
}

const TaskCreate: React.FC = () => {
  const [uploadTasks, setUploadTasks] = useState<UploadTask[]>([]);
  const [uploading, setUploading] = useState(false);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    // 获取可用模型列表
    const fetchModels = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/models');
        const data = await response.json();
        setModels(data.models);
        setSelectedModel(data.default_index);
      } catch (error) {
        console.error('Failed to fetch models:', error);
        message.warning('无法获取模型列表，将使用默认模型');
      }
    };
    fetchModels();
  }, []);

  const handleFilesUpload = async (fileList: File[]) => {
    setUploading(true);
    const tasks: UploadTask[] = fileList.map(file => ({
      file,
      status: 'uploading',
    }));
    setUploadTasks(tasks);

    for (let i = 0; i < tasks.length; i++) {
      try {
        const task = await taskAPI.createTask(tasks[i].file, undefined, selectedModel);
        tasks[i].status = 'success';
        tasks[i].taskId = task.id;
        setUploadTasks([...tasks]);
        message.success(`${tasks[i].file.name} 上传成功`);
      } catch (error: any) {
        tasks[i].status = 'error';
        tasks[i].error = error.response?.data?.detail || '上传失败';
        setUploadTasks([...tasks]);
        message.error(`${tasks[i].file.name} 上传失败: ${tasks[i].error}`);
      }
    }

    setUploading(false);
  };

  const uploadProps = {
    name: 'files',
    multiple: true,
    accept: '.pdf,.docx,.md',
    beforeUpload: () => false, // 阻止自动上传
    onChange: (info: any) => {
      const fileList = info.fileList.map((item: any) => item.originFileObj).filter(Boolean);
      if (fileList.length > 0) {
        handleFilesUpload(fileList);
      }
    },
    showUploadList: false,
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'uploading':
        return <Tag color="blue">上传中</Tag>;
      case 'success':
        return <Tag color="green">成功</Tag>;
      case 'error':
        return <Tag color="red">失败</Tag>;
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Card title="创建文档测试任务" extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回列表
        </Button>
      }>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 模型选择 */}
          {models.length > 0 && (
            <div>
              <h3>选择分析模型</h3>
              <Select
                style={{ width: '100%' }}
                value={selectedModel}
                onChange={setSelectedModel}
                disabled={uploading}
              >
                {models.map(model => (
                  <Option key={model.index} value={model.index}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>
                        {model.label}
                        {model.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>默认</Tag>}
                      </span>
                      <Tooltip title={model.description}>
                        <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
                      </Tooltip>
                    </div>
                    <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                      提供商: {model.provider} | {model.description}
                    </div>
                  </Option>
                ))}
              </Select>
            </div>
          )}

          <div>
            <h3>上传文档文件</h3>
            <p>支持的文件格式：PDF、Word (.docx)、Markdown (.md)，最大文件大小：10MB</p>
            <Dragger {...uploadProps} disabled={uploading}>
              <p className="ant-upload-drag-icon">
                {uploading ? <LoadingOutlined /> : <InboxOutlined />}
              </p>
              <p className="ant-upload-text">
                {uploading ? '正在上传文件...' : '点击或拖拽文件到此区域上传'}
              </p>
              <p className="ant-upload-hint">
                支持批量上传，系统将为每个文件创建独立的测试任务
              </p>
            </Dragger>
          </div>

          {uploadTasks.length > 0 && (
            <div>
              <h3>上传结果</h3>
              {uploadTasks.map((task, index) => (
                <Card
                  key={index}
                  size="small"
                  style={{ marginBottom: 8 }}
                  bodyStyle={{ padding: '12px 16px' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{task.file.name}</strong>
                      <span style={{ marginLeft: 8, color: '#666' }}>
                        ({formatFileSize(task.file.size)})
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {getStatusTag(task.status)}
                      {task.status === 'success' && task.taskId && (
                        <Button 
                          size="small" 
                          type="link"
                          onClick={() => navigate(`/task/${task.taskId}`)}
                        >
                          查看详情
                        </Button>
                      )}
                    </div>
                  </div>
                  {task.error && (
                    <div style={{ color: '#ff4d4f', marginTop: 4 }}>
                      错误：{task.error}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}

          {uploadTasks.filter(t => t.status === 'success').length > 0 && (
            <div style={{ textAlign: 'center' }}>
              <Button type="primary" size="large" onClick={() => navigate('/')}>
                查看所有任务
              </Button>
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default TaskCreate;