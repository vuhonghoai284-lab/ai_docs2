import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Tag, Progress, Space, message, Popconfirm, 
  Badge, Tooltip, Dropdown, Menu, Input, Select, Row, Col, Statistic,
  Empty, Typography, Segmented
} from 'antd';
import { 
  PlusOutlined, ReloadOutlined, DeleteOutlined, EyeOutlined,
  DownloadOutlined, FileTextOutlined, FilePdfOutlined, FileWordOutlined,
  FileMarkdownOutlined, FileUnknownOutlined, SearchOutlined,
  FilterOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ClockCircleOutlined, SyncOutlined, ExclamationCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { taskAPI } from '../api';
import { Task } from '../types';

const { Text } = Typography;
const { Option } = Select;

const TaskList: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const navigate = useNavigate();

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await taskAPI.getTasks();
      setTasks(data);
      filterTasks(data, searchText, statusFilter);
    } catch (error) {
      message.error('加载任务列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadTasks();
    // 每5秒刷新一次，获取进度更新（减少频率）
    const interval = setInterval(loadTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filterTasks(tasks, searchText, statusFilter);
  }, [tasks, searchText, statusFilter]);

  const filterTasks = (taskList: Task[], search: string, status: string) => {
    let filtered = [...taskList];
    
    // 搜索过滤
    if (search) {
      filtered = filtered.filter(task => 
        task.title?.toLowerCase().includes(search.toLowerCase()) ||
        task.file_name.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    // 状态过滤
    if (status !== 'all') {
      filtered = filtered.filter(task => task.status === status);
    }
    
    setFilteredTasks(filtered);
  };

  const handleDelete = async (taskId: number) => {
    try {
      await taskAPI.deleteTask(taskId);
      message.success('任务已删除');
      loadTasks();
    } catch (error) {
      message.error('删除任务失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的任务');
      return;
    }
    
    try {
      // 批量删除（需要后端支持）
      for (const taskId of selectedRowKeys) {
        await taskAPI.deleteTask(Number(taskId));
      }
      message.success(`成功删除 ${selectedRowKeys.length} 个任务`);
      setSelectedRowKeys([]);
      loadTasks();
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  const handleRetry = async (taskId: number) => {
    try {
      await taskAPI.retryTask(taskId);
      message.success('任务已重新启动');
      loadTasks();
    } catch (error) {
      message.error('重试失败');
    }
  };

  const handleDownloadReport = async (taskId: number) => {
    try {
      await taskAPI.downloadReport(taskId);
      message.success('报告下载成功');
    } catch (error) {
      message.error('下载报告失败');
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: { [key: string]: { color: string; text: string; icon: React.ReactNode } } = {
      pending: { color: 'default', text: '等待中', icon: <ClockCircleOutlined /> },
      processing: { color: 'processing', text: '处理中', icon: <SyncOutlined spin /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', text: '失败', icon: <CloseCircleOutlined /> },
    };
    const config = statusMap[status] || statusMap.pending;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />;
      case 'doc':
      case 'docx':
        return <FileWordOutlined style={{ color: '#1890ff', fontSize: 16 }} />;
      case 'md':
        return <FileMarkdownOutlined style={{ color: '#52c41a', fontSize: 16 }} />;
      case 'txt':
        return <FileTextOutlined style={{ color: '#722ed1', fontSize: 16 }} />;
      default:
        return <FileUnknownOutlined style={{ color: '#8c8c8c', fontSize: 16 }} />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 计算统计数据
  const statistics = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    processing: tasks.filter(t => t.status === 'processing').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${Math.round(seconds)}秒`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}分${secs}秒`;
  };

  const formatChars = (chars?: number) => {
    if (!chars) return '-';
    if (chars < 1000) return `${chars}字`;
    if (chars < 10000) return `${(chars / 1000).toFixed(1)}千字`;
    return `${(chars / 10000).toFixed(1)}万字`;
  };

  const columns = [
    {
      title: '文件',
      key: 'file',
      width: '25%',
      render: (_: any, record: Task) => (
        <Space>
          {getFileIcon(record.file_name)}
          <div>
            <div style={{ fontWeight: 500 }}>{record.title || record.file_name}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.file_name} · {formatFileSize(record.file_size)}
            </Text>
            {record.document_chars && (
              <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
                文档: {formatChars(record.document_chars)}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: '模型',
      key: 'model',
      width: '12%',
      render: (_: any, record: Task) => (
        record.model_label ? (
          <Tooltip title={record.model_label}>
            <Tag color="blue" style={{ fontSize: 11 }}>
              {record.model_label.length > 10 
                ? record.model_label.substring(0, 10) + '...' 
                : record.model_label}
            </Tag>
          </Tooltip>
        ) : '-'
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: '10%',
      render: (status: string) => getStatusTag(status),
      filters: [
        { text: '等待中', value: 'pending' },
        { text: '处理中', value: 'processing' },
        { text: '已完成', value: 'completed' },
        { text: '失败', value: 'failed' },
      ],
      onFilter: (value: any, record: Task) => record.status === value,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: '12%',
      render: (progress: number, record: Task) => (
        record.status === 'completed' ? (
          <Space direction="vertical" size={0}>
            <Space size={4}>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <Text type="success">完成</Text>
            </Space>
            {record.processing_time && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                耗时: {formatTime(record.processing_time)}
              </Text>
            )}
          </Space>
        ) : record.status === 'failed' ? (
          <Space>
            <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
            <Text type="danger">失败</Text>
          </Space>
        ) : (
          <Progress 
            percent={Math.round(progress)} 
            size="small"
          />
        )
      ),
    },
    {
      title: '问题数',
      key: 'issues',
      width: '8%',
      render: (_: any, record: Task) => (
        record.status === 'completed' ? (
          <Badge count={record.issue_count || 0} showZero>
            <ExclamationCircleOutlined style={{ fontSize: 16 }} />
          </Badge>
        ) : '-'
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: '12%',
      render: (date: string) => (
        <Tooltip title={new Date(date).toLocaleString('zh-CN')}>
          <Text style={{ fontSize: 12 }}>
            {new Date(date).toLocaleDateString('zh-CN')}
          </Text>
        </Tooltip>
      ),
      sorter: (a: Task, b: Task) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '操作',
      key: 'action',
      width: '15%',
      render: (_: any, record: Task) => {
        const menu = (
          <Menu>
            <Menu.Item key="view" icon={<EyeOutlined />} onClick={() => navigate(`/task/${record.id}`)}>
              查看详情
            </Menu.Item>
            {record.status === 'completed' && (
              <Menu.Item key="download" icon={<DownloadOutlined />} onClick={() => handleDownloadReport(record.id)}>
                下载报告
              </Menu.Item>
            )}
            {record.status === 'failed' && (
              <Menu.Item key="retry" icon={<ReloadOutlined />} onClick={() => handleRetry(record.id)}>
                重试任务
              </Menu.Item>
            )}
            <Menu.Divider />
            <Menu.Item key="delete" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>
              删除任务
            </Menu.Item>
          </Menu>
        );

        return (
          <Space size="small">
            <Button
              type="primary"
              size="small"
              ghost
              icon={<EyeOutlined />}
              onClick={() => navigate(`/task/${record.id}`)}
            >
              查看
            </Button>
            <Dropdown overlay={menu} trigger={['click']}>
              <Button size="small">
                更多 <FilterOutlined />
              </Button>
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  const renderTaskCard = (task: Task) => (
    <Col xs={24} sm={12} md={8} lg={6} key={task.id}>
      <Card
        hoverable
        size="small"
        style={{ marginBottom: 16 }}
        actions={[
          <Tooltip title="查看详情">
            <EyeOutlined onClick={() => navigate(`/task/${task.id}`)} />
          </Tooltip>,
          task.status === 'completed' ? (
            <Tooltip title="下载报告">
              <DownloadOutlined onClick={() => handleDownloadReport(task.id)} />
            </Tooltip>
          ) : task.status === 'failed' ? (
            <Tooltip title="重试">
              <ReloadOutlined onClick={() => handleRetry(task.id)} />
            </Tooltip>
          ) : (
            <BarChartOutlined style={{ color: '#d9d9d9' }} />
          ),
          <Popconfirm
            title="确定删除该任务吗？"
            onConfirm={() => handleDelete(task.id)}
            okText="确定"
            cancelText="取消"
          >
            <DeleteOutlined style={{ color: '#ff4d4f' }} />
          </Popconfirm>,
        ]}
      >
        <Card.Meta
          avatar={getFileIcon(task.file_name)}
          title={
            <div style={{ fontSize: 14 }}>
              {task.title || task.file_name}
              <div style={{ marginTop: 4 }}>
                {getStatusTag(task.status)}
              </div>
            </div>
          }
          description={
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {task.file_name}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatFileSize(task.file_size)}
                {task.document_chars && ` · ${formatChars(task.document_chars)}`}
              </Text>
              {task.model_label && (
                <Tag color="blue" style={{ fontSize: 10, marginTop: 4 }}>
                  {task.model_label}
                </Tag>
              )}
              {task.status === 'processing' && (
                <Progress percent={Math.round(task.progress)} size="small" />
              )}
              {task.status === 'completed' && (
                <Space>
                  <Badge count={task.issue_count || 0} showZero>
                    <Text style={{ fontSize: 12 }}>检测到问题</Text>
                  </Badge>
                  {task.processing_time && (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      耗时{formatTime(task.processing_time)}
                    </Text>
                  )}
                </Space>
              )}
              <Text type="secondary" style={{ fontSize: 11 }}>
                {new Date(task.created_at).toLocaleDateString('zh-CN')}
              </Text>
            </Space>
          }
        />
      </Card>
    </Col>
  );

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={4}>
          <Card size="small">
            <Statistic
              title="总任务数"
              value={statistics.total}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={5}>
          <Card size="small">
            <Statistic
              title="等待中"
              value={statistics.pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={5}>
          <Card size="small">
            <Statistic
              title="处理中"
              value={statistics.processing}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={5}>
          <Card size="small">
            <Statistic
              title="已完成"
              value={statistics.completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={5}>
          <Card size="small">
            <Statistic
              title="失败"
              value={statistics.failed}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容卡片 */}
      <Card
        title={
          <Space>
            <span>任务管理</span>
            <Badge count={statistics.processing} dot={statistics.processing > 0}>
              <span style={{ fontSize: 14, color: '#8c8c8c' }}>
                {statistics.processing > 0 && `(${statistics.processing} 个进行中)`}
              </span>
            </Badge>
          </Space>
        }
        extra={
          <Space>
            <Segmented
              options={[
                { value: 'table', icon: <FilterOutlined /> },
                { value: 'card', icon: <BarChartOutlined /> },
              ]}
              value={viewMode}
              onChange={(value) => setViewMode(value as 'table' | 'card')}
            />
            <Button icon={<ReloadOutlined />} onClick={loadTasks}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/create')}
            >
              新建任务
            </Button>
          </Space>
        }
      >
        {/* 搜索和筛选栏 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="搜索文件名或标题..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="状态筛选"
              value={statusFilter}
              onChange={setStatusFilter}
            >
              <Option value="all">全部状态</Option>
              <Option value="pending">等待中</Option>
              <Option value="processing">处理中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
            </Select>
          </Col>
          {selectedRowKeys.length > 0 && (
            <Col xs={24} sm={12} md={10}>
              <Space>
                <Text>已选择 {selectedRowKeys.length} 项</Text>
                <Popconfirm
                  title={`确定删除选中的 ${selectedRowKeys.length} 个任务吗？`}
                  onConfirm={handleBatchDelete}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button danger size="small" icon={<DeleteOutlined />}>
                    批量删除
                  </Button>
                </Popconfirm>
                <Button size="small" onClick={() => setSelectedRowKeys([])}>
                  取消选择
                </Button>
              </Space>
            </Col>
          )}
        </Row>

        {/* 任务列表/卡片视图 */}
        {viewMode === 'table' ? (
          <Table
            rowSelection={rowSelection}
            columns={columns}
            dataSource={filteredTasks}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`,
              showQuickJumper: true,
            }}
            locale={{
              emptyText: (
                <Empty
                  description={searchText || statusFilter !== 'all' ? '没有符合条件的任务' : '暂无任务'}
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ),
            }}
          />
        ) : (
          <Row gutter={[16, 16]}>
            {filteredTasks.length > 0 ? (
              filteredTasks.map(task => renderTaskCard(task))
            ) : (
              <Col span={24}>
                <Empty
                  description={searchText || statusFilter !== 'all' ? '没有符合条件的任务' : '暂无任务'}
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              </Col>
            )}
          </Row>
        )}
      </Card>
    </Space>
  );
};

export default TaskList;