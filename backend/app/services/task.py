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
from app.repositories.file_info import FileInfoRepository
from app.repositories.ai_model import AIModelRepository
from app.repositories.user import UserRepository
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
        self.file_repo = FileInfoRepository(db)
        self.model_repo = AIModelRepository(db)
        self.user_repo = UserRepository(db)
        self.settings = get_settings()
    
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
        
        # 获取关联数据构建响应
        file_info = self.file_repo.get_by_id(task.file_id) if task.file_id else None
        ai_model = self.model_repo.get_by_id(task.model_id) if task.model_id else None
        user_info = self.user_repo.get_by_id(task.user_id) if task.user_id else None
        issue_count = self.task_repo.count_issues(task.id)
        processed_issues = self.task_repo.count_processed_issues(task.id)
        return TaskResponse.from_task_with_relations(task, file_info, ai_model, user_info, issue_count, processed_issues)
    
    def get_all_tasks(self) -> List[TaskResponse]:
        """获取所有任务"""
        tasks = self.task_repo.get_all()
        result = []
        for task in tasks:
            file_info = self.file_repo.get_by_id(task.file_id) if task.file_id else None
            ai_model = self.model_repo.get_by_id(task.model_id) if task.model_id else None
            user_info = self.user_repo.get_by_id(task.user_id) if task.user_id else None
            issue_count = self.task_repo.count_issues(task.id)
            processed_issues = self.task_repo.count_processed_issues(task.id)
            task_resp = TaskResponse.from_task_with_relations(task, file_info, ai_model, user_info, issue_count, processed_issues)
            result.append(task_resp)
        return result
    
    def get_all(self) -> List[TaskResponse]:
        """获取所有任务（基础接口方法）"""
        return self.get_all_tasks()
    
    def get_user_tasks(self, user_id: int) -> List[TaskResponse]:
        """获取指定用户的任务"""
        tasks = self.task_repo.get_by_user_id(user_id)
        result = []
        for task in tasks:
            file_info = self.file_repo.get_by_id(task.file_id) if task.file_id else None
            ai_model = self.model_repo.get_by_id(task.model_id) if task.model_id else None
            user_info = self.user_repo.get_by_id(task.user_id) if task.user_id else None
            issue_count = self.task_repo.count_issues(task.id)
            processed_issues = self.task_repo.count_processed_issues(task.id)
            task_resp = TaskResponse.from_task_with_relations(task, file_info, ai_model, user_info, issue_count, processed_issues)
            result.append(task_resp)
        return result
    
    def get_task_detail(self, task_id: int) -> TaskDetail:
        """获取任务详情"""
        print(f"🔍 正在查找任务: {task_id}")
        task = self.task_repo.get_by_id(task_id)
        print(f"🔍 找到任务: {task}")
        if not task:
            print(f"❌ 任务 {task_id} 不存在")
            raise HTTPException(404, "任务不存在")
        
        issues = self.issue_repo.get_by_task_id(task_id)
        
        file_info = self.file_repo.get_by_id(task.file_id) if task.file_id else None
        ai_model = self.model_repo.get_by_id(task.model_id) if task.model_id else None
        user_info = self.user_repo.get_by_id(task.user_id) if task.user_id else None
        processed_issues = self.task_repo.count_processed_issues(task_id)
        task_resp = TaskResponse.from_task_with_relations(task, file_info, ai_model, user_info, len(issues), processed_issues)
        
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
        
        # 先删除任务（这会删除相关的问题和AI输出）
        task_deleted = self.task_repo.delete(task_id)
        
        # 如果任务删除成功且有关联文件，检查是否可以删除文件
        if task_deleted and file_info:
            # 检查是否还有其他任务使用这个文件
            from app.models import Task
            other_tasks_count = self.db.query(Task).filter(Task.file_id == file_info.id).count()
            
            # 如果没有其他任务使用这个文件，则删除文件
            if other_tasks_count == 0:
                if os.path.exists(file_info.file_path):
                    os.remove(file_info.file_path)
                self.file_repo.delete(file_info.id)
        
        return task_deleted
    
    def create(self, **kwargs) -> TaskResponse:
        """创建任务实体（同步版本）"""
        # 这里实现同步的创建逻辑，不过不常用
        raise NotImplementedError("请使用 create_task 方法")
    
    def get_by_id(self, entity_id: int) -> Optional[TaskResponse]:
        """根据ID获取任务"""
        task = self.task_repo.get_by_id(entity_id)
        if not task:
            return None
        
        file_info = self.file_repo.get_by_id(task.file_id) if task.file_id else None
        ai_model = self.model_repo.get_by_id(task.model_id) if task.model_id else None
        user_info = self.user_repo.get_by_id(task.user_id) if task.user_id else None
        issue_count = self.task_repo.count_issues(task.id)
        processed_issues = self.task_repo.count_processed_issues(task.id)
        return TaskResponse.from_task_with_relations(task, file_info, ai_model, user_info, issue_count, processed_issues)
    
    def update(self, entity_id: int, **kwargs) -> Optional[TaskResponse]:
        """更新任务"""
        updated_task = self.task_repo.update(entity_id, **kwargs)
        if not updated_task:
            return None
        
        file_info = self.file_repo.get_by_id(updated_task.file_id) if updated_task.file_id else None
        ai_model = self.model_repo.get_by_id(updated_task.model_id) if updated_task.model_id else None
        user_info = self.user_repo.get_by_id(updated_task.user_id) if updated_task.user_id else None
        issue_count = self.task_repo.count_issues(updated_task.id)
        processed_issues = self.task_repo.count_processed_issues(updated_task.id)
        return TaskResponse.from_task_with_relations(updated_task, file_info, ai_model, user_info, issue_count, processed_issues)