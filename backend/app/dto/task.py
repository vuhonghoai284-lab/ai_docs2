"""
任务相关的DTO（数据传输对象）
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    """创建任务请求"""
    title: Optional[str] = None
    model_index: Optional[int] = None
    

class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    title: str
    file_name: str
    file_size: int
    file_type: str
    status: str
    progress: float
    issue_count: Optional[int] = None
    model_label: Optional[str] = None
    document_chars: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
        

class TaskDetail(BaseModel):
    """任务详情"""
    task: TaskResponse
    issues: List['IssueResponse']
    
    class Config:
        from_attributes = True


from app.dto.issue import IssueResponse
TaskDetail.model_rebuild()