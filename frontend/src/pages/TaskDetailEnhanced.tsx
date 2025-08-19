import React, { useState, useEffect } from 'react';
import { 
  Card, Button, Tag, Progress, Space, message, Spin, Empty, 
  Input, Radio, Tabs, Typography, Pagination, Collapse, Badge,
  Divider, Row, Col, Tooltip, Alert
} from 'antd';
import { 
  ArrowLeftOutlined, DownloadOutlined, CheckOutlined, CloseOutlined, 
  FileTextOutlined, ExclamationCircleOutlined, BulbOutlined,
  ThunderboltOutlined, UserOutlined, QuestionCircleOutlined,
  HistoryOutlined, RobotOutlined, InfoCircleOutlined, SwapOutlined,
  EnvironmentOutlined, EditOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { taskAPI } from '../api';
import { TaskDetail as TaskDetailType, Issue } from '../types';
import TaskLogs from '../components/TaskLogs';
import './TaskDetailEnhanced.css';

const { Text, Paragraph, Title } = Typography;
const { Panel } = Collapse;
const { TextArea } = Input;

// 扩展Issue类型以包含新字段
interface EnhancedIssue extends Issue {
  original_text?: string;
  user_impact?: string;
  reasoning?: string;
  context?: string;
}

interface EnhancedTaskDetail extends TaskDetailType {
  issues: EnhancedIssue[];
}

const TaskDetailEnhanced: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [taskDetail, setTaskDetail] = useState<EnhancedTaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackLoading, setFeedbackLoading] = useState<{ [key: number]: boolean }>({});
  
  // 分页相关状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<{ [key: number]: Set<string> }>({});
  const [expandedComments, setExpandedComments] = useState<Set<number>>(new Set());
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const loadTaskDetail = async () => {
    if (!id) return;
    
    try {
      const data = await taskAPI.getTaskDetail(parseInt(id));
      setTaskDetail(data as EnhancedTaskDetail);
    } catch (error) {
      message.error('加载任务详情失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadTaskDetail();
    // 如果任务还在处理中，定期刷新
    const interval = setInterval(() => {
      if (taskDetail?.task.status === 'processing' || taskDetail?.task.status === 'pending') {
        loadTaskDetail();
      }
    }, 3000);
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

  const getSeverityBadge = (severity: string) => {
    const severityMap: { [key: string]: { color: string; icon: React.ReactNode; tagColor: string } } = {
      '致命': { color: 'red', icon: <ExclamationCircleOutlined />, tagColor: 'error' },
      '严重': { color: 'orange', icon: <ExclamationCircleOutlined />, tagColor: 'warning' },
      '一般': { color: 'blue', icon: <QuestionCircleOutlined />, tagColor: 'processing' },
      '提示': { color: 'green', icon: <BulbOutlined />, tagColor: 'success' }
    };
    const config = severityMap[severity] || severityMap['一般'];
    return (
      <Tag color={config.tagColor} icon={config.icon}>
        {severity}
      </Tag>
    );
  };

  const toggleIssueExpanded = (issueId: number) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };

  const toggleSection = (issueId: number, section: string) => {
    setExpandedSections(prev => {
      const current = prev[issueId] || new Set();
      const newSet = new Set(current);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return { ...prev, [issueId]: newSet };
    });
  };

  const toggleComment = (issueId: number) => {
    const newExpanded = new Set(expandedComments);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedComments(newExpanded);
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
  
  // 过滤处理
  const filteredIssues = issues.filter(issue => {
    // 级别过滤
    if (severityFilter !== 'all' && issue.severity !== severityFilter) {
      return false;
    }
    // 状态过滤
    if (statusFilter === 'accepted' && issue.feedback_type !== 'accept') {
      return false;
    }
    if (statusFilter === 'rejected' && issue.feedback_type !== 'reject') {
      return false;
    }
    if (statusFilter === 'pending' && issue.feedback_type) {
      return false;
    }
    return true;
  });

  // 分页处理
  const totalIssues = issues.length;
  const filteredCount = filteredIssues.length;
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedIssues = filteredIssues.slice(startIndex, endIndex);

  // 统计信息
  const processedCount = issues.filter(i => i.feedback_type).length;
  const acceptedCount = issues.filter(i => i.feedback_type === 'accept').length;
  const severityCounts = {
    '致命': issues.filter(i => i.severity === '致命').length,
    '严重': issues.filter(i => i.severity === '严重').length,
    '一般': issues.filter(i => i.severity === '一般').length,
    '提示': issues.filter(i => i.severity === '提示').length
  };

  return (
    <div className="task-detail-enhanced" style={{ maxWidth: '100%', padding: '0 24px' }}>
      {/* Enhanced Task Detail Page v3 - Compact Layout */}
      <Card
        className="main-card"
        title={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
              返回列表
            </Button>
            <span className="task-title">{task.title}</span>
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
        {/* 任务基本信息 */}
        <Card className="info-card" size="small" title="任务信息">
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Text type="secondary">文件名</Text>
              <div>{task.file_name}</div>
            </Col>
            <Col span={5}>
              <Text type="secondary">状态</Text>
              <div>{getStatusTag(task.status)}</div>
            </Col>
            <Col span={7}>
              <Text type="secondary">进度</Text>
              <Progress percent={Math.round(task.progress)} size="small" />
            </Col>
            <Col span={4}>
              <Text type="secondary">文件类型</Text>
              <div><Tag>{task.file_type.toUpperCase()}</Tag></div>
            </Col>
          </Row>
        </Card>

        {/* 标签页 */}
        <Tabs defaultActiveKey={task.status === 'processing' ? 'logs' : 'issues'}>
          {/* 问题列表标签页 */}
          <Tabs.TabPane 
            tab={
              <Space>
                <FileTextOutlined />
                <span>检测问题 ({totalIssues})</span>
              </Space>
            } 
            key="issues"
          >
            {task.status === 'completed' && (
              <>
                {totalIssues === 0 ? (
                  <Empty description="未发现任何问题" />
                ) : (
                  <>
                    {/* 筛选器 */}
                    <Card className="filter-card" size="small" style={{ marginBottom: 16 }}>
                      <Space size={16} wrap>
                        <Space size={8}>
                          <Text strong>问题级别:</Text>
                          <Radio.Group 
                            value={severityFilter} 
                            onChange={(e) => {
                              setSeverityFilter(e.target.value);
                              setCurrentPage(1);
                            }}
                            size="small"
                          >
                            <Radio.Button value="all">全部</Radio.Button>
                            <Radio.Button value="致命">
                              <Tag color="error">致命 ({issues.filter(i => i.severity === '致命').length})</Tag>
                            </Radio.Button>
                            <Radio.Button value="严重">
                              <Tag color="warning">严重 ({issues.filter(i => i.severity === '严重').length})</Tag>
                            </Radio.Button>
                            <Radio.Button value="一般">
                              <Tag color="processing">一般 ({issues.filter(i => i.severity === '一般').length})</Tag>
                            </Radio.Button>
                            <Radio.Button value="提示">
                              <Tag color="success">提示 ({issues.filter(i => i.severity === '提示').length})</Tag>
                            </Radio.Button>
                          </Radio.Group>
                        </Space>
                        <Divider type="vertical" />
                        <Space size={8}>
                          <Text strong>处理状态:</Text>
                          <Radio.Group 
                            value={statusFilter} 
                            onChange={(e) => {
                              setStatusFilter(e.target.value);
                              setCurrentPage(1);
                            }}
                            size="small"
                          >
                            <Radio.Button value="all">全部 ({totalIssues})</Radio.Button>
                            <Radio.Button value="accepted">
                              <CheckOutlined style={{ color: '#52c41a' }} /> 已接受 ({acceptedCount})
                            </Radio.Button>
                            <Radio.Button value="rejected">
                              <CloseOutlined style={{ color: '#ff4d4f' }} /> 已拒绝 ({processedCount - acceptedCount})
                            </Radio.Button>
                            <Radio.Button value="pending">
                              <QuestionCircleOutlined /> 未处理 ({totalIssues - processedCount})
                            </Radio.Button>
                          </Radio.Group>
                        </Space>
                        {filteredCount < totalIssues && (
                          <Tag color="blue">显示 {filteredCount}/{totalIssues} 个问题</Tag>
                        )}
                      </Space>
                    </Card>

                    {/* 问题统计 - 改进版 */}
                    <Card className="statistics-card" size="small" style={{ marginBottom: 16 }}>
                      <Row gutter={24}>
                        <Col span={8}>
                          <div className="stat-section">
                            <Text type="secondary">处理进度</Text>
                            <Progress 
                              percent={Math.round((processedCount / totalIssues) * 100)} 
                              status="active"
                              strokeColor="#1890ff"
                            />
                            <div className="stat-detail">
                              <Text>已处理: {processedCount}/{totalIssues}</Text>
                              <Text type="success"> | 已接受: {acceptedCount}</Text>
                            </div>
                          </div>
                        </Col>
                        <Col span={8}>
                          <div className="stat-section">
                            <Text type="secondary">问题级别分布</Text>
                            <div className="severity-bars">
                              <div className="bar-item">
                                <Text>致命</Text>
                                <Progress 
                                  percent={totalIssues ? Math.round((severityCounts['致命'] / totalIssues) * 100) : 0} 
                                  size="small"
                                  strokeColor="#ff4d4f"
                                  format={() => severityCounts['致命']}
                                />
                              </div>
                              <div className="bar-item">
                                <Text>严重</Text>
                                <Progress 
                                  percent={totalIssues ? Math.round((severityCounts['严重'] / totalIssues) * 100) : 0}
                                  size="small"
                                  strokeColor="#faad14"
                                  format={() => severityCounts['严重']}
                                />
                              </div>
                              <div className="bar-item">
                                <Text>一般</Text>
                                <Progress 
                                  percent={totalIssues ? Math.round((severityCounts['一般'] / totalIssues) * 100) : 0}
                                  size="small"
                                  strokeColor="#1890ff"
                                  format={() => severityCounts['一般']}
                                />
                              </div>
                              <div className="bar-item">
                                <Text>提示</Text>
                                <Progress 
                                  percent={totalIssues ? Math.round((severityCounts['提示'] / totalIssues) * 100) : 0}
                                  size="small"
                                  strokeColor="#52c41a"
                                  format={() => severityCounts['提示']}
                                />
                              </div>
                            </div>
                          </div>
                        </Col>
                        <Col span={8}>
                          <div className="stat-section">
                            <Text type="secondary">接受率</Text>
                            <div className="acceptance-rate">
                              <Progress 
                                type="circle" 
                                percent={processedCount ? Math.round((acceptedCount / processedCount) * 100) : 0}
                                width={80}
                                strokeColor={{
                                  '0%': '#52c41a',
                                  '100%': '#87d068',
                                }}
                              />
                              <div className="rate-detail">
                                <Text>接受: {acceptedCount}</Text>
                                <br />
                                <Text>拒绝: {processedCount - acceptedCount}</Text>
                              </div>
                            </div>
                          </div>
                        </Col>
                      </Row>
                    </Card>

                    {/* 问题列表 */}
                    <div className="issues-list">
                      {paginatedIssues.map((issue) => (
                        <Card 
                          key={issue.id} 
                          className={`issue-card issue-severity-${issue.severity.toLowerCase()}`}
                          size="small"
                        >
                          {/* 问题标题栏 - 新布局 */}
                          <div className="issue-header-new">
                            <div className="issue-title">
                              <span className="issue-number">#{startIndex + paginatedIssues.indexOf(issue) + 1}</span>
                              <Text className="issue-desc">{issue.description}</Text>
                            </div>
                            <Space className="issue-tags" size={6}>
                              {getSeverityBadge(issue.severity)}
                              <Tag color="blue">{issue.issue_type}</Tag>
                              {issue.feedback_type ? (
                                <Tag icon={issue.feedback_type === 'accept' ? <CheckOutlined /> : <CloseOutlined />} 
                                     color={issue.feedback_type === 'accept' ? 'success' : 'error'}>
                                  {issue.feedback_type === 'accept' ? '已接受' : '已拒绝'}
                                </Tag>
                              ) : (
                                <Tag color="default">待处理</Tag>
                              )}
                            </Space>
                          </div>

                          {/* 对比展示区 - 原文 vs 改进建议 */}
                          <div className="issue-comparison">
                            <Row gutter={16}>
                              <Col span={12}>
                                <div className="comparison-section original">
                                  <div className="comparison-header">
                                    <FileTextOutlined style={{ color: '#ff4d4f' }} />
                                    <Text strong> 原文内容</Text>
                                  </div>
                                  <div className="comparison-content">
                                    {issue.original_text || '未提供原文'}
                                  </div>
                                </div>
                              </Col>
                              <Col span={12}>
                                <div className="comparison-section suggestion">
                                  <div className="comparison-header">
                                    <EditOutlined style={{ color: '#52c41a' }} />
                                    <Text strong> 改进建议</Text>
                                  </div>
                                  <div className="comparison-content">
                                    {issue.suggestion || '未提供建议'}
                                  </div>
                                </div>
                              </Col>
                            </Row>
                          </div>

                          {/* 更多信息 - 默认折叠 */}
                          {(issue.location || issue.reasoning || issue.user_impact || issue.context) && (
                              <Collapse 
                                ghost 
                                className="more-info-collapse"
                                activeKey={expandedSections[issue.id]?.has('moreInfo') ? ['moreInfo'] : []}
                                onChange={() => toggleSection(issue.id, 'moreInfo')}
                              >
                                <Panel
                                  header={
                                    <Space size={4}>
                                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                      <Text>更多信息</Text>
                                    </Space>
                                  }
                                  key="moreInfo"
                                >
                                  <div className="more-info-content">
                                    {issue.location && (
                                      <div className="info-item">
                                        <EnvironmentOutlined style={{ color: '#8c8c8c' }} />
                                        <Text strong> 章节位置：</Text>
                                        <Text>{issue.location}</Text>
                                      </div>
                                    )}
                                    {issue.reasoning && (
                                      <div className="info-item">
                                        <ThunderboltOutlined style={{ color: '#1890ff' }} />
                                        <Text strong> 判定原因：</Text>
                                        <Text>{issue.reasoning}</Text>
                                      </div>
                                    )}
                                    {issue.user_impact && (
                                      <div className="info-item">
                                        <UserOutlined style={{ color: '#faad14' }} />
                                        <Text strong> 用户影响：</Text>
                                        <Text>{issue.user_impact}</Text>
                                      </div>
                                    )}
                                    {issue.context && (
                                      <div className="info-item">
                                        <FileTextOutlined style={{ color: '#722ed1' }} />
                                        <Text strong> 上下文环境：</Text>
                                        <Text>{issue.context}</Text>
                                      </div>
                                    )}
                                  </div>
                                </Panel>
                              </Collapse>
                            )}

                            {/* 用户反馈区（紧凑布局） */}
                            <div className="feedback-section-compact">
                              <div className="feedback-actions">
                                <Space size={8}>
                                  <UserOutlined style={{ color: '#1890ff' }} />
                                  <Text strong>用户操作：</Text>
                                  <Radio.Group
                                    size="small"
                                    value={issue.feedback_type}
                                    onChange={(e) => handleFeedback(issue.id, e.target.value, issue.feedback_comment)}
                                    disabled={feedbackLoading[issue.id]}
                                  >
                                    <Radio.Button value="accept">
                                      <CheckOutlined /> 接受
                                    </Radio.Button>
                                    <Radio.Button value="reject">
                                      <CloseOutlined /> 拒绝
                                    </Radio.Button>
                                  </Radio.Group>
                                  {issue.feedback_type && (
                                    <Tag color={issue.feedback_type === 'accept' ? 'green' : 'red'}>
                                      {issue.feedback_type === 'accept' ? '已接受' : '已拒绝'}
                                    </Tag>
                                  )}
                                  <Button
                                    type="link"
                                    size="small"
                                    icon={expandedComments.has(issue.id) ? <CloseOutlined /> : <FileTextOutlined />}
                                    onClick={() => toggleComment(issue.id)}
                                  >
                                    {expandedComments.has(issue.id) ? '收起评论' : 
                                     issue.feedback_comment ? '编辑评论' : '添加评论'}
                                  </Button>
                                  {issue.feedback_comment && !expandedComments.has(issue.id) && (
                                    <Tooltip title={issue.feedback_comment}>
                                      <Tag icon={<FileTextOutlined />} color="blue">已评论</Tag>
                                    </Tooltip>
                                  )}
                                </Space>
                              </div>
                              
                              {/* 评论输入框（可展开） */}
                              {expandedComments.has(issue.id) && (
                                <div className="feedback-comment-area">
                                  <TextArea
                                    placeholder="请输入反馈意见..."
                                    rows={2}
                                    size="small"
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
                                      if (issue.feedback_type && e.target.value) {
                                        handleFeedback(issue.id, issue.feedback_type, e.target.value);
                                      }
                                    }}
                                  />
                                  <div className="comment-actions">
                                    <Space size={4}>
                                      <Button 
                                        size="small" 
                                        type="primary"
                                        onClick={() => {
                                          if (issue.feedback_type) {
                                            handleFeedback(issue.id, issue.feedback_type, issue.feedback_comment);
                                            toggleComment(issue.id);
                                          }
                                        }}
                                      >
                                        保存
                                      </Button>
                                      <Button 
                                        size="small"
                                        onClick={() => toggleComment(issue.id)}
                                      >
                                        取消
                                      </Button>
                                    </Space>
                                  </div>
                                </div>
                              )}
                            </div>
                        </Card>
                      ))}
                    </div>

                    {/* 分页器 */}
                    <div className="pagination-container">
                      <Pagination
                        current={currentPage}
                        pageSize={pageSize}
                        total={filteredCount}
                        onChange={setCurrentPage}
                        onShowSizeChange={(_, size) => {
                          setPageSize(size);
                          setCurrentPage(1);
                        }}
                        showSizeChanger
                        showQuickJumper
                        showTotal={(total) => `筛选后 ${total} 个问题`}
                        pageSizeOptions={['5', '10', '20', '50']}
                      />
                    </div>
                  </>
                )}
              </>
            )}

            {/* 处理中状态 */}
            {(task.status === 'pending' || task.status === 'processing') && (
              <Card>
                <div style={{ textAlign: 'center', padding: 50 }}>
                  <Spin size="large" />
                  <p style={{ marginTop: 16 }}>任务正在处理中，请稍候...</p>
                  <Progress percent={Math.round(task.progress)} />
                </div>
              </Card>
            )}
          </Tabs.TabPane>

          {/* 实时日志标签页 */}
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
        </Tabs>
      </Card>
    </div>
  );
};

export default TaskDetailEnhanced;