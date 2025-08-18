"""FastAPI主应用"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import shutil
from datetime import datetime
import asyncio
import yaml

from database import get_db, Task, Issue, AIOutput
from task_processor import task_processor
from report_generator import generate_report

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建应用
app = FastAPI(title="AI文档测试系统")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
os.makedirs(config['upload_dir'], exist_ok=True)
os.makedirs(config['report_dir'], exist_ok=True)

# Pydantic模型
class FeedbackRequest(BaseModel):
    feedback_type: str  # accept/reject
    comment: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_size: int
    file_type: str
    status: str
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

class IssueResponse(BaseModel):
    id: int
    issue_type: str
    description: str
    location: str
    severity: str
    suggestion: str
    feedback_type: Optional[str]
    feedback_comment: Optional[str]

class AIOutputResponse(BaseModel):
    id: int
    task_id: int
    operation_type: str
    section_title: Optional[str]
    section_index: Optional[int]
    input_text: str
    raw_output: str
    parsed_output: Optional[dict]
    status: str
    error_message: Optional[str]
    tokens_used: Optional[int]
    processing_time: Optional[float]
    created_at: datetime

# API端点
@app.get("/")
def read_root():
    return {"message": "AI文档测试系统后端API"}

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建任务"""
    # 验证文件类型
    allowed_types = ['.pdf', '.docx', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(400, f"不支持的文件类型: {file_ext}")
    
    # 验证文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > config['max_file_size']:
        raise HTTPException(400, f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB")
    
    # 保存文件
    file_name = file.filename
    file_path = os.path.join(config['upload_dir'], f"{datetime.now().timestamp()}_{file_name}")
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # 创建任务记录
    task = Task(
        title=title or os.path.splitext(file_name)[0],
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_ext[1:],
        status='pending',
        progress=0
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 后台处理任务
    background_tasks.add_task(process_task_async, task.id)
    
    return task

async def process_task_async(task_id: int):
    """异步处理任务"""
    db = next(get_db())
    try:
        await task_processor.process_task(task_id, db)
    finally:
        db.close()

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    """获取任务列表"""
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return tasks

@app.get("/api/tasks/{task_id}")
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    
    issues = db.query(Issue).filter(Issue.task_id == task_id).all()
    
    return {
        "task": {
            "id": task.id,
            "title": task.title,
            "file_name": task.file_name,
            "file_size": task.file_size,
            "file_type": task.file_type,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message
        },
        "issues": [
            {
                "id": issue.id,
                "issue_type": issue.issue_type,
                "description": issue.description,
                "location": issue.location,
                "severity": issue.severity,
                "suggestion": issue.suggestion,
                "feedback_type": issue.feedback_type,
                "feedback_comment": issue.feedback_comment
            }
            for issue in issues
        ]
    }

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    
    # 删除文件
    if os.path.exists(task.file_path):
        os.remove(task.file_path)
    
    # 删除数据库记录
    db.delete(task)
    db.commit()
    
    return {"success": True, "message": "任务已删除"}

@app.put("/api/issues/{issue_id}/feedback")
def update_issue_feedback(
    issue_id: int,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """更新问题反馈"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "问题不存在")
    
    issue.feedback_type = feedback.feedback_type
    issue.feedback_comment = feedback.comment
    issue.updated_at = datetime.now()
    db.commit()
    
    return {"success": True}

@app.get("/api/tasks/{task_id}/report")
def download_report(task_id: int, db: Session = Depends(get_db)):
    """生成并下载报告"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    
    if task.status != 'completed':
        raise HTTPException(400, "任务未完成，无法生成报告")
    
    try:
        file_path = generate_report(task_id, db)
        return FileResponse(
            file_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(file_path)
        )
    except Exception as e:
        raise HTTPException(500, f"报告生成失败: {str(e)}")

@app.get("/api/tasks/{task_id}/ai-outputs", response_model=List[AIOutputResponse])
def get_task_ai_outputs(
    task_id: int,
    operation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取任务的AI输出记录"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    
    query = db.query(AIOutput).filter(AIOutput.task_id == task_id)
    
    # 按操作类型过滤
    if operation_type:
        query = query.filter(AIOutput.operation_type == operation_type)
    
    # 按创建时间排序
    ai_outputs = query.order_by(AIOutput.created_at).all()
    
    return ai_outputs

@app.get("/api/ai-outputs/{output_id}", response_model=AIOutputResponse)
def get_ai_output_detail(output_id: int, db: Session = Depends(get_db)):
    """获取单个AI输出详情"""
    ai_output = db.query(AIOutput).filter(AIOutput.id == output_id).first()
    if not ai_output:
        raise HTTPException(404, "AI输出记录不存在")
    
    return ai_output

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)