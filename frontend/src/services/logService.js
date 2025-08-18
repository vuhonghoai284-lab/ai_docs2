/**
 * 任务日志服务 - WebSocket连接和日志管理
 */

class LogService {
  constructor() {
    this.websocket = null;
    this.listeners = new Map(); // 存储各种事件的监听器
    this.logs = new Map(); // 存储任务日志
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  /**
   * 连接到任务日志WebSocket
   * @param {string} taskId - 任务ID
   */
  connect(taskId) {
    if (this.websocket) {
      this.disconnect();
    }

    const wsUrl = `ws://localhost:8080/ws/task/${taskId}/logs`;
    console.log('Connecting to WebSocket:', wsUrl);

    try {
      this.websocket = new WebSocket(wsUrl);
      this.setupEventHandlers(taskId);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleReconnect(taskId);
    }
  }

  /**
   * 设置WebSocket事件处理器
   */
  setupEventHandlers(taskId) {
    if (!this.websocket) return;

    // 连接打开
    this.websocket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected', { taskId });
      
      // 启动心跳
      this.startHeartbeat();
    };

    // 接收消息
    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    // 连接关闭
    this.websocket.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopHeartbeat();
      this.emit('disconnected', { taskId });
      this.handleReconnect(taskId);
    };

    // 连接错误
    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
  }

  /**
   * 处理接收到的消息
   */
  handleMessage(data) {
    const { type, task_id } = data;

    // 根据消息类型处理
    switch (type) {
      case 'connection':
        console.log('Connection established:', data);
        break;
      
      case 'status':
        // 任务状态更新
        this.emit('status', data);
        break;
      
      default:
        // 普通日志消息
        this.addLog(task_id, data);
        this.emit('log', data);
        
        // 如果是进度更新，单独触发进度事件
        if (data.level === 'PROGRESS') {
          this.emit('progress', {
            taskId: task_id,
            progress: data.progress,
            message: data.message
          });
        }
        break;
    }
  }

  /**
   * 添加日志到缓存
   */
  addLog(taskId, log) {
    if (!this.logs.has(taskId)) {
      this.logs.set(taskId, []);
    }
    
    const logs = this.logs.get(taskId);
    logs.push(log);
    
    // 限制缓存大小
    if (logs.length > 1000) {
      logs.shift();
    }
  }

  /**
   * 获取任务的所有日志
   */
  getLogs(taskId) {
    return this.logs.get(taskId) || [];
  }

  /**
   * 清除任务日志
   */
  clearLogs(taskId) {
    this.logs.delete(taskId);
  }

  /**
   * 处理重连
   */
  handleReconnect(taskId) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('reconnect_failed', { taskId });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    this.emit('reconnecting', { 
      taskId, 
      attempt: this.reconnectAttempts,
      delay 
    });

    this.reconnectTimer = setTimeout(() => {
      this.connect(taskId);
    }, delay);
  }

  /**
   * 心跳机制
   */
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send('ping');
      }
    }, 30000); // 每30秒发送一次心跳
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    this.reconnectAttempts = 0;
  }

  /**
   * 事件监听器管理
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return;
    
    const callbacks = this.listeners.get(event);
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  /**
   * 获取历史日志（从API）
   */
  async fetchHistory(taskId, limit = 100) {
    try {
      const response = await fetch(`http://localhost:8080/api/tasks/${taskId}/logs/history?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 将历史日志添加到缓存
      if (data.logs && data.logs.length > 0) {
        data.logs.forEach(log => {
          this.addLog(taskId, log);
        });
      }
      
      return data;
    } catch (error) {
      console.error('Error fetching log history:', error);
      throw error;
    }
  }
}

// 创建单例实例
const logService = new LogService();

export default logService;