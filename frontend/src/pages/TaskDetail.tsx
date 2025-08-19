import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, Space, Descriptions, Tag, Spin, Button, Progress, 
  message, Table, Empty, Radio, Input, Collapse, Alert 
} from 'antd';
import { 
  ArrowLeftOutlined, DownloadOutlined, CheckOutlined, 
  CloseOutlined, ReloadOutlined, ExclamationCircleOutlined,
  QuestionCircleOutlined, InfoCircleOutlined, BulbOutlined
} from '@ant-design/icons';
import { TaskDetail as TaskDetailType, Issue } from '../types';
import { getTaskDetail, submitFeedback, downloadReport, retryTask } from '../services/api';

const { Panel } = Collapse;

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [taskDetail, setTaskDetail] = useState<TaskDetailType | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState<{ [key: number]: boolean }>({});
  const [activePanel, setActivePanel] = useState<string[]>(['issues']);

  const loadTaskDetail = async () => {
    if (!id) return;
    
    try {
      const data = await getTaskDetail(parseInt(id));
      setTaskDetail(data);
    } catch (error) {
      message.error('加载任务详情失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTaskDetail();
    
    // 如果任务正在处理中，定时刷新
    const interval = setInterval(() => {
      if (taskDetail?.task.status === 'processing' || taskDetail?.task.status === 'pending') {
        loadTaskDetail();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [id, taskDetail?.task.status]);

  const handleFeedback = async (issueId: number, feedbackType: string, comment: string = '') => {
    setFeedbackLoading({ ...feedbackLoading, [issueId]: true });
    
    try {
      await submitFeedback(issueId, feedbackType, comment);
      message.success('反馈已提交');
      loadTaskDetail(); // 重新加载数据
    } catch (error) {
      message.error('提交反馈失败');
      console.error(error);
    } finally {
      setFeedbackLoading({ ...feedbackLoading, [issueId]: false });
    }
  };

  const handleDownloadReport = async () => {
    if (!id) return;
    
    try {
      await downloadReport(parseInt(id));
      message.success('报告下载成功');
    } catch (error) {
      message.error('下载报告失败');
      console.error(error);
    }
  };

  const handleRetry = async () => {
    if (!id) return;
    
    try {
      await retryTask(parseInt(id));
      message.success('已重新启动任务');
      loadTaskDetail();
    } catch (error) {
      message.error('重试失败');
      console.error(error);
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: { [key: string]: { color: string; text: string } } = {
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' }
    };
    const config = statusMap[status] || statusMap.pending;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case '致命':
        return 'severity-fatal';
      case '严重':
        return 'severity-critical';
      case '一般':
        return 'severity-normal';
      case '提示':
        return 'severity-info';
      default:
        return '';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case '致命':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case '严重':
        return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />;
      case '一般':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />;
      case '提示':
        return <BulbOutlined style={{ color: '#52c41a' }} />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!taskDetail) {
    return (
      <Card>
        <Empty description="任务不存在" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button onClick={() => navigate('/tasks')}>返回任务列表</Button>
        </div>
      </Card>
    );
  }

  const { task, issues } = taskDetail;

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 头部操作栏 */}
      <Card size="small">
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/tasks')}
          >
            返回列表
          </Button>
          <Space>
            {task.status === 'failed' && (
              <Button 
                icon={<ReloadOutlined />}
                onClick={handleRetry}
                type="primary"
              >
                重试
              </Button>
            )}
            {task.status === 'completed' && (
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={handleDownloadReport}
              >
                下载报告
              </Button>
            )}
          </Space>
        </Space>
      </Card>

      {/* 任务信息 */}
      <Card title="任务信息" size="small">
        <Descriptions bordered column={2}>
          <Descriptions.Item label="任务ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="状态">{getStatusTag(task.status)}</Descriptions.Item>
          <Descriptions.Item label="文件名">{task.file_name}</Descriptions.Item>
          <Descriptions.Item label="文件大小">{(task.file_size / 1024).toFixed(2)} KB</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(task.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 检测结果 */}
      {task.status === 'completed' && (
        <Card 
          title={`检测结果（共 ${issues.length} 个问题）`} 
          size="small"
        >
          {issues.length === 0 ? (
            <Empty description="未发现任何问题" />
          ) : (
            <Space direction="vertical" style={{ width: '100%' }}>
              {issues.map((issue, index) => (
                <Card
                  key={issue.id}
                  className="issue-card"
                  size="small"
                  title={
                    <div className="issue-card-header">
                      <div className="issue-card-header-left">
                        <span>#{index + 1}</span>
                        <Tag color="blue">{issue.issue_type}</Tag>
                        <span className={getSeverityClass(issue.severity)}>
                          {getSeverityIcon(issue.severity)} {issue.severity}
                        </span>
                        {issue.confidence && (
                          <Tag color="purple">
                            置信度：{(issue.confidence * 100).toFixed(0)}%
                          </Tag>
                        )}
                      </div>
                      <div className="issue-card-header-right">
                        {issue.feedback_type && (
                          <Tag color={issue.feedback_type === 'accept' ? 'green' : 'red'}>
                            {issue.feedback_type === 'accept' ? '已接受' : '已拒绝'}
                          </Tag>
                        )}
                      </div>
                    </div>
                  }
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {/* 问题描述放在第一行，加粗加大 */}
                    <div>
                      <p className="issue-description">{issue.description}</p>
                    </div>
                    
                    <Descriptions bordered size="small" column={1}>
                      <Descriptions.Item label="位置">{issue.location}</Descriptions.Item>
                      {issue.original_text && (
                        <Descriptions.Item label="原文">
                          <div style={{ background: '#fff5f5', padding: '8px', borderRadius: '4px' }}>
                            {issue.original_text}
                          </div>
                        </Descriptions.Item>
                      )}
                      <Descriptions.Item label="修改建议">
                        <div style={{ background: '#f6ffed', padding: '8px', borderRadius: '4px' }}>
                          {issue.suggestion}
                        </div>
                      </Descriptions.Item>
                      {issue.user_impact && (
                        <Descriptions.Item label="用户影响">{issue.user_impact}</Descriptions.Item>
                      )}
                      {issue.reasoning && (
                        <Descriptions.Item label="判定理由">{issue.reasoning}</Descriptions.Item>
                      )}
                    </Descriptions>
                    
                    {/* 用户操作放在最后一行右侧 */}
                    <div className="issue-feedback-actions">
                      {!issue.feedback_type ? (
                        <Radio.Group
                          onChange={(e) => handleFeedback(issue.id, e.target.value, '')}
                          disabled={feedbackLoading[issue.id]}
                        >
                          <Radio.Button value="accept">
                            <CheckOutlined /> 接受
                          </Radio.Button>
                          <Radio.Button value="reject">
                            <CloseOutlined /> 拒绝
                          </Radio.Button>
                        </Radio.Group>
                      ) : issue.feedback_type === 'reject' ? (
                        <Space>
                          <Input.TextArea
                            placeholder="请输入拒绝理由（可选）"
                            rows={1}
                            style={{ width: 300 }}
                            value={issue.feedback_comment || ''}
                            onChange={(e) => {
                              const newIssues = [...issues];
                              const idx = newIssues.findIndex(i => i.id === issue.id);
                              if (idx >= 0) {
                                newIssues[idx].feedback_comment = e.target.value;
                                setTaskDetail({ ...taskDetail, issues: newIssues });
                              }
                            }}
                            onBlur={(e) => {
                              handleFeedback(issue.id, 'reject', e.target.value);
                            }}
                          />
                          <Button
                            size="small"
                            onClick={() => handleFeedback(issue.id, '', '')}
                          >
                            撤销
                          </Button>
                        </Space>
                      ) : (
                        <Button
                          size="small"
                          onClick={() => handleFeedback(issue.id, '', '')}
                        >
                          撤销接受
                        </Button>
                      )}
                    </div>
                  </Space>
                </Card>
              ))}
            </Space>
          )}
        </Card>
      )}

      {/* 处理中状态 */}
      {(task.status === 'pending' || task.status === 'processing') && (
        <Card size="small">
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>任务正在处理中，请稍候...</p>
            <Progress percent={Math.round(task.progress)} />
          </div>
        </Card>
      )}

      {/* 失败状态 */}
      {task.status === 'failed' && (
        <Card size="small">
          <Alert
            message="任务处理失败"
            description={task.error_message || '未知错误'}
            type="error"
            showIcon
            action={
              <Button size="small" danger onClick={handleRetry}>
                重试
              </Button>
            }
          />
        </Card>
      )}
    </Space>
  );
};

export default TaskDetail;