import React, { useState, useEffect, useRef } from 'react';
import { Card, Progress, Tag, Input, Select, Space, Empty, Badge, Alert, Button } from 'antd';
import { 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  SyncOutlined, 
  CloseCircleOutlined,
  FilterOutlined,
  ClearOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import logService from '../services/logService';
import './TaskLogs.css';

const { Search } = Input;
const { Option } = Select;

/**
 * 任务日志实时展示组件
 */
const TaskLogs = ({ taskId, taskStatus }) => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [currentStatus, setCurrentStatus] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef(null);
  const logsContainerRef = useRef(null);

  // 连接WebSocket并设置监听器
  useEffect(() => {
    if (!taskId) return;

    // 连接WebSocket
    logService.connect(taskId);

    // 设置事件监听器
    const handleLog = (log) => {
      setLogs(prev => [...prev, log]);
    };

    const handleStatus = (status) => {
      setCurrentStatus(status);
    };

    const handleProgress = (data) => {
      setCurrentStatus(prev => ({
        ...prev,
        progress: data.progress
      }));
    };

    const handleConnected = () => {
      setConnectionStatus('connected');
    };

    const handleDisconnected = () => {
      setConnectionStatus('disconnected');
    };

    const handleReconnecting = () => {
      setConnectionStatus('reconnecting');
    };

    // 注册监听器
    logService.on('log', handleLog);
    logService.on('status', handleStatus);
    logService.on('progress', handleProgress);
    logService.on('connected', handleConnected);
    logService.on('disconnected', handleDisconnected);
    logService.on('reconnecting', handleReconnecting);

    // 获取历史日志
    logService.fetchHistory(taskId).then(data => {
      if (data.logs) {
        setLogs(data.logs);
      }
      if (data.current_status) {
        setCurrentStatus(data.current_status);
      }
    });

    // 清理函数
    return () => {
      logService.off('log', handleLog);
      logService.off('status', handleStatus);
      logService.off('progress', handleProgress);
      logService.off('connected', handleConnected);
      logService.off('disconnected', handleDisconnected);
      logService.off('reconnecting', handleReconnecting);
      logService.disconnect();
    };
  }, [taskId]);

  // 过滤日志
  useEffect(() => {
    let filtered = logs;

    // 按级别过滤
    if (levelFilter !== 'ALL') {
      filtered = filtered.filter(log => log.level === levelFilter);
    }

    // 按关键词搜索
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase();
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(keyword) ||
        log.stage?.toLowerCase().includes(keyword) ||
        log.module?.toLowerCase().includes(keyword)
      );
    }

    setFilteredLogs(filtered);
  }, [logs, levelFilter, searchKeyword]);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs, autoScroll]);

  // 获取日志级别颜色
  const getLevelColor = (level) => {
    const colors = {
      'DEBUG': 'default',
      'INFO': 'blue',
      'WARNING': 'orange',
      'ERROR': 'red',
      'PROGRESS': 'green'
    };
    return colors[level] || 'default';
  };

  // 获取阶段图标
  const getStageIcon = (stage) => {
    const icons = {
      '初始化': <ClockCircleOutlined />,
      '文档解析': <SyncOutlined spin />,
      '内容分析': <SyncOutlined spin />,
      '报告生成': <SyncOutlined spin />,
      '完成': <CheckCircleOutlined />,
      '错误': <CloseCircleOutlined />
    };
    return icons[stage] || <SyncOutlined />;
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  // 清除日志
  const handleClearLogs = () => {
    setLogs([]);
    logService.clearLogs(taskId);
  };

  // 检查是否用户滚动
  const handleScroll = () => {
    if (!logsContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
    
    if (!isAtBottom && autoScroll) {
      setAutoScroll(false);
    } else if (isAtBottom && !autoScroll) {
      setAutoScroll(true);
    }
  };

  return (
    <div className="task-logs-container">
      {/* 状态栏 */}
      <Card className="status-bar" size="small">
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <span>连接状态:</span>
            <Badge 
              status={connectionStatus === 'connected' ? 'success' : 
                     connectionStatus === 'reconnecting' ? 'processing' : 'error'} 
              text={connectionStatus === 'connected' ? '已连接' :
                   connectionStatus === 'reconnecting' ? '重连中' : '未连接'} 
            />
          </Space>
          
          <Space>
            <span>当前阶段:</span>
            <Tag icon={getStageIcon(currentStatus.stage)}>
              {currentStatus.stage || '未知'}
            </Tag>
          </Space>

          <Space style={{ flex: 1 }}>
            <span>进度:</span>
            <Progress 
              percent={currentStatus.progress || 0} 
              style={{ width: 200 }}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </Space>
        </Space>
      </Card>

      {/* 过滤栏 */}
      <Card className="filter-bar" size="small">
        <Space>
          <FilterOutlined />
          
          <Select 
            value={levelFilter} 
            onChange={setLevelFilter}
            style={{ width: 120 }}
          >
            <Option value="ALL">所有级别</Option>
            <Option value="DEBUG">DEBUG</Option>
            <Option value="INFO">INFO</Option>
            <Option value="WARNING">WARNING</Option>
            <Option value="ERROR">ERROR</Option>
            <Option value="PROGRESS">PROGRESS</Option>
          </Select>

          <Search
            placeholder="搜索日志内容"
            allowClear
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 300 }}
          />

          <Button 
            icon={autoScroll ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setAutoScroll(!autoScroll)}
          >
            {autoScroll ? '暂停滚动' : '自动滚动'}
          </Button>

          <Button 
            icon={<ClearOutlined />} 
            onClick={handleClearLogs}
            danger
          >
            清除日志
          </Button>

          <span style={{ marginLeft: 'auto' }}>
            共 {filteredLogs.length} 条日志
          </span>
        </Space>
      </Card>

      {/* 日志内容区 */}
      <Card className="logs-content">
        <div 
          className="logs-list" 
          ref={logsContainerRef}
          onScroll={handleScroll}
        >
          {filteredLogs.length === 0 ? (
            <Empty description="暂无日志" />
          ) : (
            filteredLogs.map((log, index) => (
              <div key={index} className={`log-item log-level-${log.level.toLowerCase()}`}>
                <span className="log-time">{formatTimestamp(log.timestamp)}</span>
                <Tag color={getLevelColor(log.level)} className="log-level">
                  {log.level}
                </Tag>
                <span className="log-module">[{log.module}]</span>
                <span className="log-message">{log.message}</span>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <span className="log-metadata">
                    {JSON.stringify(log.metadata)}
                  </span>
                )}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </Card>

      {/* 错误提示 */}
      {connectionStatus === 'disconnected' && taskStatus === 'processing' && (
        <Alert
          message="连接已断开"
          description="无法接收实时日志更新，请检查网络连接"
          type="warning"
          showIcon
          closable
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
};

export default TaskLogs;