"""
WebSocket端点 - 用于实时推送任务日志（无Redis版本）
"""
from typing import Dict, Set
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from utils.task_logger import TaskLoggerFactory

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储每个任务的WebSocket连接
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # 存储每个WebSocket连接对应的回调函数
        self.websocket_callbacks: Dict[WebSocket, callable] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        
        # 添加到连接池
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        
        # 获取任务日志管理器
        logger = await TaskLoggerFactory.get_logger(task_id)
        
        # 注册推送回调
        async def push_to_client(log_data):
            try:
                await websocket.send_json(log_data)
            except:
                pass  # 连接可能已断开
        
        # 保存回调函数引用
        self.websocket_callbacks[websocket] = push_to_client
        logger.add_push_callback(push_to_client)
        
        # 发送历史日志
        history = logger.get_history(50)
        for log in history:
            try:
                await websocket.send_json(log)
            except:
                break
        
        # 发送当前状态
        status = logger.get_current_status()
        await websocket.send_json({
            "type": "status",
            **status
        })
    
    async def disconnect(self, websocket: WebSocket, task_id: str):
        """断开WebSocket连接"""
        # 移除回调函数
        if websocket in self.websocket_callbacks:
            callback = self.websocket_callbacks[websocket]
            logger = await TaskLoggerFactory.get_logger(task_id)
            logger.remove_push_callback(callback)
            del self.websocket_callbacks[websocket]
        
        # 移除连接
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            
            # 如果没有客户端连接了，清理
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_to_task_clients(self, task_id: str, message: dict):
        """向所有监听该任务的客户端发送消息"""
        if task_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[task_id].discard(conn)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/task/{task_id}/logs")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str
):
    """
    WebSocket端点 - 实时推送任务日志
    
    客户端连接后会：
    1. 接收该任务的历史日志（最近50条）
    2. 接收当前任务状态
    3. 实时接收新的日志更新
    
    日志格式：
    {
        "task_id": "任务ID",
        "timestamp": "时间戳",
        "level": "日志级别",
        "module": "模块名",
        "stage": "任务阶段",
        "message": "日志消息",
        "progress": 进度(0-100),
        "metadata": {}
    }
    
    状态格式：
    {
        "type": "status",
        "task_id": "任务ID",
        "stage": "当前阶段",
        "progress": 当前进度,
        "timestamp": "时间戳"
    }
    """
    await manager.connect(websocket, task_id)
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 保持连接
        while True:
            # 等待客户端消息（心跳或其他）
            data = await websocket.receive_text()
            
            # 处理心跳
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, task_id)
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        await manager.disconnect(websocket, task_id)


@router.get("/api/tasks/{task_id}/logs/history")
async def get_task_logs_history(
    task_id: str,
    limit: int = 100
):
    """
    获取任务的历史日志
    
    Parameters:
    - task_id: 任务ID
    - limit: 返回的日志条数限制（默认100）
    
    Returns:
    - 日志列表
    """
    try:
        logger = await TaskLoggerFactory.get_logger(task_id)
        logs = logger.get_history(limit)
        status = logger.get_current_status()
        
        return {
            "task_id": task_id,
            "logs": logs,
            "count": len(logs),
            "current_status": status
        }
    except Exception as e:
        return {
            "error": str(e),
            "task_id": task_id,
            "logs": []
        }