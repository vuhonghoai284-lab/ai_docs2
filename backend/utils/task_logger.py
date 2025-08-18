"""
任务日志管理器 - 无Redis版本
使用内存队列和数据库实现日志记录和实时推送
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import asyncio
from collections import deque
import os

from sqlalchemy.orm import Session


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"  # 特殊类型，用于进度更新


class TaskStage(str, Enum):
    """任务阶段枚举"""
    INIT = "初始化"
    PARSING = "文档解析"
    ANALYZING = "内容分析"
    GENERATING = "报告生成"
    COMPLETE = "完成"
    ERROR = "错误"


class TaskLogger:
    """任务日志管理器"""
    
    def __init__(self, task_id: str, module: str = "system"):
        self.task_id = task_id
        self.module = module
        self.current_stage = TaskStage.INIT
        self.current_progress = 0
        
        # 内存中的日志队列（保留最近100条）
        self.log_queue = deque(maxlen=100)
        
        # WebSocket推送回调函数列表
        self.push_callbacks: List[Callable] = []
        
        # 配置Python标准日志
        self.logger = logging.getLogger(f"task.{task_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = "logs/tasks"
        os.makedirs(log_dir, exist_ok=True)
        
        # 添加文件处理器
        file_handler = logging.FileHandler(
            f"{log_dir}/{task_id}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        self.logger.addHandler(file_handler)
    
    def add_push_callback(self, callback: Callable):
        """添加推送回调函数"""
        if callback not in self.push_callbacks:
            self.push_callbacks.append(callback)
    
    def remove_push_callback(self, callback: Callable):
        """移除推送回调函数"""
        if callback in self.push_callbacks:
            self.push_callbacks.remove(callback)
    
    async def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        stage: Optional[TaskStage] = None,
        progress: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录日志并推送到WebSocket
        
        Args:
            message: 日志消息
            level: 日志级别
            stage: 任务阶段
            progress: 任务进度(0-100)
            metadata: 额外的元数据
        """
        # 更新当前阶段和进度
        if stage:
            self.current_stage = stage
        if progress is not None:
            self.current_progress = progress
        
        # 构建日志数据
        log_data = {
            "task_id": self.task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "module": self.module,
            "stage": self.current_stage.value,
            "message": message,
            "progress": self.current_progress,
            "metadata": metadata or {}
        }
        
        # 写入Python日志
        log_level = getattr(logging, level.value, logging.INFO)
        self.logger.log(log_level, json.dumps(log_data, ensure_ascii=False))
        
        # 添加到内存队列
        self.log_queue.append(log_data)
        
        # 推送到所有WebSocket连接
        for callback in self.push_callbacks:
            try:
                await callback(log_data)
            except Exception as e:
                self.logger.error(f"推送日志失败: {str(e)}")
        
        return log_data
    
    async def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        await self.log(message, LogLevel.DEBUG, **kwargs)
    
    async def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        await self.log(message, LogLevel.INFO, **kwargs)
    
    async def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        await self.log(message, LogLevel.WARNING, **kwargs)
    
    async def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        await self.log(message, LogLevel.ERROR, **kwargs)
    
    async def progress(self, progress: int, message: str = "", **kwargs):
        """更新任务进度"""
        await self.log(
            message or f"任务进度: {progress}%",
            LogLevel.PROGRESS,
            progress=progress,
            **kwargs
        )
    
    async def set_stage(self, stage: TaskStage, message: str = "", progress: Optional[int] = None):
        """设置任务阶段"""
        stage_progress_map = {
            TaskStage.INIT: 5,
            TaskStage.PARSING: 20,
            TaskStage.ANALYZING: 50,
            TaskStage.GENERATING: 80,
            TaskStage.COMPLETE: 100,
            TaskStage.ERROR: self.current_progress  # 错误时保持当前进度
        }
        
        if progress is None:
            progress = stage_progress_map.get(stage, self.current_progress)
        
        await self.log(
            message or f"进入阶段: {stage.value}",
            LogLevel.INFO,
            stage=stage,
            progress=progress
        )
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取历史日志"""
        # 从内存队列中获取
        logs = list(self.log_queue)
        # 返回最近的limit条
        return logs[-limit:] if len(logs) > limit else logs
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        return {
            "task_id": self.task_id,
            "stage": self.current_stage.value,
            "progress": self.current_progress,
            "timestamp": datetime.utcnow().isoformat()
        }


class TaskLoggerFactory:
    """任务日志管理器工厂"""
    
    _loggers: Dict[str, TaskLogger] = {}
    
    @classmethod
    async def get_logger(cls, task_id: str, module: str = "system") -> TaskLogger:
        """获取或创建任务日志管理器"""
        if task_id not in cls._loggers:
            logger = TaskLogger(task_id, module)
            cls._loggers[task_id] = logger
        
        return cls._loggers[task_id]
    
    @classmethod
    async def close_logger(cls, task_id: str):
        """关闭并移除任务日志管理器"""
        if task_id in cls._loggers:
            # 清理回调函数
            cls._loggers[task_id].push_callbacks.clear()
            del cls._loggers[task_id]
    
    @classmethod
    async def close_all(cls):
        """关闭所有日志管理器"""
        for task_id in list(cls._loggers.keys()):
            await cls.close_logger(task_id)
    
    @classmethod
    def get_active_loggers(cls) -> List[str]:
        """获取所有活动的日志管理器ID"""
        return list(cls._loggers.keys())


# 全局日志管理器实例
task_logger_factory = TaskLoggerFactory()