"""FastAPI主应用"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import sys
import argparse
import shutil
from datetime import datetime
import asyncio
import yaml

from database import get_db, Task, Issue, AIOutput
from task_processor import task_processor
from report_generator import generate_report
from api.websocket import router as websocket_router

# 解析命令行参数
parser = argparse.ArgumentParser(description='AI文档测试系统后端')
parser.add_argument('--config', '-c', type=str, default='config.yaml', help='配置文件路径')
args, unknown = parser.parse_known_args()

# 加载配置
config_path = args.config
if not os.path.exists(config_path):
    print(f"Error: Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 处理环境变量替换
def resolve_env_vars(obj):
    """Recursively resolve environment variables in config"""
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
        env_var = obj[2:-1]
        return os.environ.get(env_var, obj)
    return obj

config = resolve_env_vars(config)

# 创建应用
app = FastAPI(title="AI文档测试系统")

# CORS配置
cors_config = config.get('cors', {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

# 包含WebSocket路由
app.include_router(websocket_router)

# 启动事件处理
@app.on_event("startup")
async def startup_event():
    """系统启动时处理遗留的pending任务"""
    print("Checking for pending tasks...")
    db = next(get_db())
    try:
        # 查找所有pending状态的任务
        pending_tasks = db.query(Task).filter(Task.status == 'pending').all()
        if pending_tasks:
            print(f"Found {len(pending_tasks)} pending tasks, processing...")
            for task in pending_tasks:
                # 使用asyncio创建后台任务
                asyncio.create_task(process_task_async(task.id))
                print(f"Started processing task {task.id}: {task.title}")
        else:
            print("No pending tasks found")
    finally:
        db.close()

# 创建必要的目录
dirs = config.get('directories', {})
os.makedirs(dirs.get('upload_dir', './data/uploads'), exist_ok=True)
os.makedirs(dirs.get('report_dir', './data/reports'), exist_ok=True)
os.makedirs(dirs.get('log_dir', './data/logs'), exist_ok=True)
os.makedirs(dirs.get('temp_dir', './data/temp'), exist_ok=True)

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
    issue_count: Optional[int] = None  # 新增：问题数量
    model_label: Optional[str] = None  # 新增：模型名称
    document_chars: Optional[int] = None  # 新增：文档字符数
    processing_time: Optional[float] = None  # 新增：处理耗时
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
    model_index: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """创建任务"""
    # 验证文件类型
    file_settings = config.get('file_settings', {})
    allowed_exts = ['.' + ext for ext in file_settings.get('allowed_extensions', ['pdf', 'docx', 'md'])]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(400, f"不支持的文件类型: {file_ext}")
    
    # 验证文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    max_size = file_settings.get('max_file_size', 10485760)
    if file_size > max_size:
        raise HTTPException(400, f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB")
    
    # 保存文件
    file_name = file.filename
    upload_dir = config.get('directories', {}).get('upload_dir', './data/uploads')
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{file_name}")
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # 获取选择的模型索引
    print(f"[DEBUG main.py] 接收到的model_index: {model_index}, 类型: {type(model_index)}")
    if model_index is None:
        model_index = config.get('ai_models', {}).get('default_index', 0)
        print(f"[DEBUG main.py] model_index为None，使用默认值: {model_index}")
    else:
        # 确保model_index是整数
        model_index = int(model_index)
        print(f"[DEBUG main.py] 转换后的model_index: {model_index}")
    
    # 获取模型label
    models = config.get('ai_models', {}).get('models', [])
    model_label = models[model_index].get('label', f'Model {model_index}') if model_index < len(models) else 'Unknown'
    print(f"[DEBUG] 选择的模型: index={model_index}, label={model_label}")
    
    # 创建任务记录
    task = Task(
        title=title or os.path.splitext(file_name)[0],
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        file_type=file_ext[1:],
        status='pending',
        progress=0,
        model_index=model_index,  # 保存使用的模型索引
        model_label=model_label   # 保存模型显示名称
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
    # 为每个任务添加问题数量
    for task in tasks:
        task.issue_count = db.query(Issue).filter(Issue.task_id == task.id).count()
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
                "original_text": issue.original_text,
                "user_impact": issue.user_impact,
                "reasoning": issue.reasoning,
                "context": issue.context,
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

# 新增API: 获取可用模型列表
@app.get("/api/models")
def get_available_models():
    """获取可用的AI模型列表"""
    models = config.get('ai_models', {}).get('models', [])
    default_index = config.get('ai_models', {}).get('default_index', 0)
    
    model_list = []
    for i, model in enumerate(models):
        model_list.append({
            'index': i,
            'label': model.get('label', f'Model {i}'),
            'description': model.get('description', ''),
            'provider': model.get('provider', 'unknown'),
            'is_default': i == default_index
        })
    
    return {'models': model_list, 'default_index': default_index}

if __name__ == "__main__":
    import uvicorn
    
    # 从配置文件读取服务器设置
    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8080)
    debug = server_config.get('debug', False)
    reload = server_config.get('reload', False)
    workers = server_config.get('workers', 1)
    
    print(f"Starting server on {host}:{port}")
    print(f"Config file: {config_path}")
    print(f"Available models: {len(config.get('ai_models', {}).get('models', []))}")
    
    uvicorn.run(
        "main:app" if reload else app,
        host=host,
        port=port,
        reload=reload,
        workers=1 if reload else workers,
        log_level="debug" if debug else "info"
    )