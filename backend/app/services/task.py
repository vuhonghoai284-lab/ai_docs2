"""
任务业务逻辑层
"""
import os
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import asyncio

from app.repositories.task import TaskRepository
from app.repositories.issue import IssueRepository
from app.repositories.ai_output import AIOutputRepository
from app.dto.task import TaskResponse, TaskDetail
from app.dto.issue import IssueResponse
from app.core.config import settings
from datetime import datetime


class TaskService:
    """任务服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.issue_repo = IssueRepository(db)
        self.ai_output_repo = AIOutputRepository(db)
    
    async def create_task(self, file: UploadFile, title: Optional[str] = None, model_index: Optional[int] = None) -> TaskResponse:
        """创建任务"""
        # 验证文件
        file_settings = settings.file_settings
        allowed_exts = ['.' + ext for ext in file_settings.get('allowed_extensions', ['pdf', 'docx', 'md'])]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_exts:
            raise HTTPException(400, f"不支持的文件类型: {file_ext}")
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        max_size = file_settings.get('max_file_size', 10485760)
        if file_size > max_size:
            raise HTTPException(400, f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB")
        
        # 保存文件
        file_name = file.filename
        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{file_name}")
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 获取模型信息
        if model_index is None:
            model_index = settings.default_model_index
        
        models = settings.ai_models
        model_label = models[model_index].get('label', f'Model {model_index}') if model_index < len(models) else 'Unknown'
        
        # 创建任务记录
        task = self.task_repo.create(
            title=title or os.path.splitext(file_name)[0],
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            file_type=file_ext[1:],
            status='pending',
            progress=0,
            model_index=model_index,
            model_label=model_label
        )
        
        # 异步处理任务
        from app.services.task_processor import TaskProcessor
        processor = TaskProcessor(self.db)
        asyncio.create_task(processor.process_task(task.id))
        
        return TaskResponse.from_orm(task)
    
    def get_all_tasks(self) -> List[TaskResponse]:
        """获取所有任务"""
        tasks = self.task_repo.get_all()
        result = []
        for task in tasks:
            task_resp = TaskResponse.from_orm(task)
            task_resp.issue_count = self.task_repo.count_issues(task.id)
            result.append(task_resp)
        return result
    
    def get_task_detail(self, task_id: int) -> TaskDetail:
        """获取任务详情"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(404, "任务不存在")
        
        issues = self.issue_repo.get_by_task_id(task_id)
        
        task_resp = TaskResponse.from_orm(task)
        task_resp.issue_count = len(issues)
        
        return TaskDetail(
            task=task_resp,
            issues=[IssueResponse.from_orm(issue) for issue in issues]
        )
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(404, "任务不存在")
        
        # 删除文件
        if os.path.exists(task.file_path):
            os.remove(task.file_path)
        
        return self.task_repo.delete(task_id)