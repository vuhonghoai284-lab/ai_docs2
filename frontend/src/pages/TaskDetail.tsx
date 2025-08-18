import React, { useState, useEffect } from 'react';
import { Card, Button, Tag, Progress, Space, message, Spin, Empty, Input, Radio, Tabs, Collapse, Typography } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined, CheckOutlined, CloseOutlined, CodeOutlined, RobotOutlined, HistoryOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { taskAPI } from '../api';
import { TaskDetail as TaskDetailType, Issue, AIOutput } from '../types';
import TaskLogs from '../components/TaskLogs';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [taskDetail, setTaskDetail] = useState<TaskDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackLoading, setFeedbackLoading] = useState<{ [key: number]: boolean }>({});
  const [aiOutputs, setAiOutputs] = useState<AIOutput[]>([]);
  const [aiOutputsLoading, setAiOutputsLoading] = useState(false);

  const loadTaskDetail = async () => {
    if (!id) return;
    
    try {
      const data = await taskAPI.getTaskDetail(parseInt(id));
      setTaskDetail(data);
      
      // 加载AI输出记录
      if (data.task.status === 'completed' || data.task.status === 'processing') {
        loadAIOutputs();
      }
    } catch (error) {
      message.error('加载任务详情失败');
    }
    setLoading(false);
  };

  const loadAIOutputs = async () => {
    if (!id) return;
    
    setAiOutputsLoading(true);
    try {
      const outputs = await taskAPI.getTaskAIOutputs(parseInt(id));
      setAiOutputs(outputs);
    } catch (error) {
      console.error('加载AI输出失败:', error);
    }
    setAiOutputsLoading(false);
  };

  useEffect(() => {
    loadTaskDetail();
    // 如果任务还在处理中，定期刷新
    const interval = setInterval(() => {
      if (taskDetail?.task.status === 'processing' || taskDetail?.task.status === 'pending') {
        loadTaskDetail();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [id, taskDetail?.task.status]);

  const handleFeedback = async (issueId: number, feedbackType: 'accept' | 'reject', comment?: string) => {
    setFeedbackLoading({ ...feedbackLoading, [issueId]: true });
    try {
      await taskAPI.submitFeedback(issueId, feedbackType, comment);
      message.success('反馈已提交');
      loadTaskDetail();
    } catch (error) {
      message.error('提交反馈失败');
    }
    setFeedbackLoading({ ...feedbackLoading, [issueId]: false });
  };

  const handleDownloadReport = async () => {
    if (!taskDetail) return;
    
    try {
      await taskAPI.downloadReport(taskDetail.task.id);
      message.success('报告下载成功');
    } catch (error) {
      message.error('下载报告失败');
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: { [key: string]: { color: string; text: string } } = {
      pending: { color: 'default', text: '等待中' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    };
    const config = statusMap[status] || statusMap.pending;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getSeverityClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case '高':
        return 'severity-high';
      case '中':
        return 'severity-medium';
      case '低':
        return 'severity-low';
      default:
        return '';
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
    return <Empty description="任务不存在" />;
  }

  const { task, issues } = taskDetail;

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
              返回列表
            </Button>
            <span>任务详情：{task.title}</span>
          </Space>
        }
        extra={
          task.status === 'completed' && (
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownloadReport}>
              下载报告
            </Button>
          )
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 任务基本信息 */}
          <Card size="small" title="基本信息">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              <div>
                <span style={{ color: '#666' }}>文件名：</span>
                <strong>{task.file_name}</strong>
              </div>
              <div>
                <span style={{ color: '#666' }}>状态：</span>
                {getStatusTag(task.status)}
              </div>
              <div>
                <span style={{ color: '#666' }}>进度：</span>
                <Progress percent={Math.round(task.progress)} style={{ width: 150 }} />
              </div>
              <div>
                <span style={{ color: '#666' }}>文件类型：</span>
                <Tag>{task.file_type.toUpperCase()}</Tag>
              </div>
              <div>
                <span style={{ color: '#666' }}>创建时间：</span>
                {new Date(task.created_at).toLocaleString('zh-CN')}
              </div>
              {task.completed_at && (
                <div>
                  <span style={{ color: '#666' }}>完成时间：</span>
                  {new Date(task.completed_at).toLocaleString('zh-CN')}
                </div>
              )}
            </div>
            {task.error_message && (
              <div style={{ marginTop: 16, padding: 12, background: '#fff2f0', border: '1px solid #ffccc7', borderRadius: 4 }}>
                <strong style={{ color: '#ff4d4f' }}>错误信息：</strong> {task.error_message}
              </div>
            )}
          </Card>

          {/* 问题列表 */}
          {task.status === 'completed' && (
            <Card 
              size="small" 
              title={`检测到的问题（${issues.length}个）`}
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
                        <Space>
                          <span>#{index + 1}</span>
                          <Tag color="blue">{issue.issue_type}</Tag>
                          <span className={getSeverityClass(issue.severity)}>
                            严重程度：{issue.severity}
                          </span>
                        </Space>
                      }
                      extra={
                        issue.feedback_type && (
                          <Tag color={issue.feedback_type === 'accept' ? 'green' : 'red'}>
                            {issue.feedback_type === 'accept' ? '已接受' : '已拒绝'}
                          </Tag>
                        )
                      }
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                          <strong>问题描述：</strong>
                          <p style={{ margin: '8px 0' }}>{issue.description}</p>
                        </div>
                        <div>
                          <strong>位置：</strong> {issue.location}
                        </div>
                        <div>
                          <strong>改进建议：</strong>
                          <p style={{ margin: '8px 0' }}>{issue.suggestion}</p>
                        </div>
                        
                        {/* 反馈区域 */}
                        <Card size="small" style={{ background: '#f5f5f5' }}>
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                              <strong>用户反馈：</strong>
                              <Radio.Group
                                value={issue.feedback_type}
                                onChange={(e) => handleFeedback(issue.id, e.target.value, issue.feedback_comment)}
                                disabled={feedbackLoading[issue.id]}
                                style={{ marginLeft: 16 }}
                              >
                                <Radio.Button value="accept">
                                  <CheckOutlined /> 接受
                                </Radio.Button>
                                <Radio.Button value="reject">
                                  <CloseOutlined /> 拒绝
                                </Radio.Button>
                              </Radio.Group>
                            </div>
                            <Input.TextArea
                              placeholder="请输入评价（可选）"
                              rows={2}
                              value={issue.feedback_comment || ''}
                              onChange={(e) => {
                                // 更新本地状态
                                const newIssues = [...issues];
                                const idx = newIssues.findIndex(i => i.id === issue.id);
                                if (idx >= 0) {
                                  newIssues[idx].feedback_comment = e.target.value;
                                  setTaskDetail({ ...taskDetail, issues: newIssues });
                                }
                              }}
                              onBlur={(e) => {
                                // 失去焦点时保存
                                if (issue.feedback_type) {
                                  handleFeedback(issue.id, issue.feedback_type, e.target.value);
                                }
                              }}
                            />
                          </Space>
                        </Card>
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

          {/* AI模型输出记录和实时日志 */}
          {(task.status === 'completed' || task.status === 'processing' || task.status === 'pending') && (
            <Card 
              size="small" 
              title="任务处理详情"
            >
              <Tabs defaultActiveKey={task.status === 'processing' ? 'logs' : 'ai-output'}>
                {/* 实时日志Tab */}
                <Tabs.TabPane 
                  tab={
                    <Space>
                      <HistoryOutlined />
                      <span>实时日志</span>
                    </Space>
                  } 
                  key="logs"
                >
                  <TaskLogs taskId={id} taskStatus={task.status} />
                </Tabs.TabPane>

                {/* AI模型输出Tab */}
                <Tabs.TabPane 
                  tab={
                    <Space>
                      <RobotOutlined />
                      <span>AI处理过程</span>
                      <Button 
                        size="small" 
                        type="link" 
                        onClick={loadAIOutputs} 
                        loading={aiOutputsLoading}
                        style={{ padding: 0, height: 'auto' }}
                      >
                        刷新
                      </Button>
                    </Space>
                  } 
                  key="ai-output"
                >
                  {aiOutputsLoading ? (
                    <div style={{ textAlign: 'center', padding: 20 }}>
                      <Spin />
                    </div>
                  ) : aiOutputs.length === 0 ? (
                    <Empty description="暂无AI处理记录" />
                  ) : (
                    <Tabs defaultActiveKey="preprocess">
                      <Tabs.TabPane tab="文档预处理" key="preprocess">
                    <Collapse>
                      {aiOutputs
                        .filter(output => output.operation_type === 'preprocess')
                        .map((output, index) => (
                          <Panel 
                            header={
                              <Space>
                                <Text>预处理 #{index + 1}</Text>
                                <Tag color={output.status === 'success' ? 'green' : output.status === 'failed' ? 'red' : 'orange'}>
                                  {output.status}
                                </Tag>
                                {output.processing_time && (
                                  <Text type="secondary">耗时: {output.processing_time.toFixed(2)}秒</Text>
                                )}
                              </Space>
                            }
                            key={output.id}
                          >
                            <Space direction="vertical" style={{ width: '100%' }}>
                              <div>
                                <Text strong>输入文本（前1000字符）：</Text>
                                <Paragraph 
                                  style={{ 
                                    background: '#f5f5f5', 
                                    padding: 10, 
                                    borderRadius: 4,
                                    maxHeight: 200,
                                    overflow: 'auto'
                                  }}
                                >
                                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                    {output.input_text.substring(0, 1000)}...
                                  </pre>
                                </Paragraph>
                              </div>
                              
                              <div>
                                <Text strong>AI原始输出：</Text>
                                <Paragraph 
                                  style={{ 
                                    background: '#f0f2f5', 
                                    padding: 10, 
                                    borderRadius: 4,
                                    maxHeight: 300,
                                    overflow: 'auto'
                                  }}
                                >
                                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                    {output.raw_output}
                                  </pre>
                                </Paragraph>
                              </div>
                              
                              {output.parsed_output && (
                                <div>
                                  <Text strong>解析结果：</Text>
                                  <Paragraph 
                                    style={{ 
                                      background: '#e6f7ff', 
                                      padding: 10, 
                                      borderRadius: 4,
                                      maxHeight: 300,
                                      overflow: 'auto'
                                    }}
                                  >
                                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                      {JSON.stringify(output.parsed_output, null, 2)}
                                    </pre>
                                  </Paragraph>
                                </div>
                              )}
                              
                              {output.error_message && (
                                <div>
                                  <Text strong type="danger">错误信息：</Text>
                                  <Paragraph type="danger">
                                    {output.error_message}
                                  </Paragraph>
                                </div>
                              )}
                            </Space>
                          </Panel>
                        ))}
                    </Collapse>
                  </Tabs.TabPane>
                  
                  <Tabs.TabPane tab="问题检测" key="detect_issues">
                    <Collapse>
                      {aiOutputs
                        .filter(output => output.operation_type === 'detect_issues')
                        .map((output) => (
                          <Panel 
                            header={
                              <Space>
                                <Text>{output.section_title || `章节 ${(output.section_index ?? 0) + 1}`}</Text>
                                <Tag color={output.status === 'success' ? 'green' : output.status === 'failed' ? 'red' : 'orange'}>
                                  {output.status}
                                </Tag>
                                {output.processing_time && (
                                  <Text type="secondary">耗时: {output.processing_time.toFixed(2)}秒</Text>
                                )}
                              </Space>
                            }
                            key={output.id}
                          >
                            <Space direction="vertical" style={{ width: '100%' }}>
                              <div>
                                <Text strong>章节内容（前1000字符）：</Text>
                                <Paragraph 
                                  style={{ 
                                    background: '#f5f5f5', 
                                    padding: 10, 
                                    borderRadius: 4,
                                    maxHeight: 200,
                                    overflow: 'auto'
                                  }}
                                >
                                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                    {output.input_text.substring(0, 1000)}...
                                  </pre>
                                </Paragraph>
                              </div>
                              
                              <div>
                                <Text strong>AI检测输出：</Text>
                                <Paragraph 
                                  style={{ 
                                    background: '#f0f2f5', 
                                    padding: 10, 
                                    borderRadius: 4,
                                    maxHeight: 300,
                                    overflow: 'auto'
                                  }}
                                >
                                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                    {output.raw_output}
                                  </pre>
                                </Paragraph>
                              </div>
                              
                              {output.parsed_output && (
                                <div>
                                  <Text strong>检测到的问题：</Text>
                                  <Paragraph 
                                    style={{ 
                                      background: '#fff1f0', 
                                      padding: 10, 
                                      borderRadius: 4,
                                      maxHeight: 300,
                                      overflow: 'auto'
                                    }}
                                  >
                                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                      {JSON.stringify(output.parsed_output, null, 2)}
                                    </pre>
                                  </Paragraph>
                                </div>
                              )}
                              
                              {output.error_message && (
                                <div>
                                  <Text strong type="danger">错误信息：</Text>
                                  <Paragraph type="danger">
                                    {output.error_message}
                                  </Paragraph>
                                </div>
                              )}
                            </Space>
                          </Panel>
                        ))}
                    </Collapse>
                  </Tabs.TabPane>
                    </Tabs>
                  )}
                </Tabs.TabPane>
              </Tabs>
            </Card>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default TaskDetail;