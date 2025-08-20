"""
重构后的主应用入口
"""
from fastapi import FastAPI, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import json

from app.core.config import get_settings
from app.core.database import engine, get_db, Base
from app.dto.task import TaskResponse, TaskDetail, TaskCreate
from app.dto.issue import IssueResponse, FeedbackRequest
from app.dto.ai_output import AIOutputResponse
from app.dto.model import ModelsResponse, ModelInfo
from app.services.task import TaskService
from app.repositories.issue import IssueRepository
from app.repositories.ai_output import AIOutputRepository
from app.services.websocket import manager

# 获取配置
settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="AI文档测试系统API",
    description="基于AI的文档质量检测系统后端API",
    version="2.0.0",
    debug=settings.server_config.get('debug', False)
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """根路径"""
    mode = "测试模式" if settings.is_test_mode else "生产模式"
    return {
        "message": "AI文档测试系统后端API v2.0",
        "mode": mode,
        "test_mode": settings.is_test_mode
    }


@app.get("/api/models", response_model=ModelsResponse)
def get_models():
    """获取可用模型列表"""
    models = []
    for idx, model in enumerate(settings.ai_models):
        models.append(ModelInfo(
            index=idx,
            label=model.get('label', f'Model {idx}'),
            description=model.get('description', ''),
            provider=model.get('provider', 'unknown'),
            is_default=(idx == settings.default_model_index)
        ))
    
    return ModelsResponse(
        models=models,
        default_index=settings.default_model_index
    )


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    model_index: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """创建任务"""
    service = TaskService(db)
    return await service.create_task(file, title, model_index)


@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    """获取任务列表"""
    service = TaskService(db)
    return service.get_all_tasks()


@app.get("/api/tasks/{task_id}", response_model=TaskDetail)
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    service = TaskService(db)
    return service.get_task_detail(task_id)


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    service = TaskService(db)
    success = service.delete_task(task_id)
    return {"success": success}


@app.put("/api/issues/{issue_id}/feedback")
def submit_feedback(
    issue_id: int,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """提交问题反馈"""
    repo = IssueRepository(db)
    issue = repo.update_feedback(issue_id, feedback.feedback_type, feedback.comment)
    if not issue:
        raise HTTPException(404, "问题不存在")
    return {"success": True}


@app.get("/api/tasks/{task_id}/ai-outputs", response_model=List[AIOutputResponse])
def get_task_ai_outputs(
    task_id: int,
    operation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取任务的AI输出记录"""
    repo = AIOutputRepository(db)
    outputs = repo.get_by_task_id(task_id, operation_type)
    return [AIOutputResponse.from_orm(output) for output in outputs]


@app.get("/api/ai-outputs/{output_id}", response_model=AIOutputResponse)
def get_ai_output_detail(output_id: int, db: Session = Depends(get_db)):
    """获取AI输出详情"""
    repo = AIOutputRepository(db)
    output = repo.get_by_id(output_id)
    if not output:
        raise HTTPException(404, "AI输出不存在")
    return AIOutputResponse.from_orm(output)


@app.get("/api/tasks/{task_id}/report")
def download_report(task_id: int, db: Session = Depends(get_db)):
    """下载任务报告"""
    # TODO: 实现报告生成逻辑
    return {"message": "报告生成功能待实现"}


@app.post("/api/tasks/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    """重试任务"""
    # TODO: 实现任务重试逻辑
    return {"message": "任务重试功能待实现"}


@app.websocket("/ws/task/{task_id}/logs")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    """WebSocket端点 - 实时日志推送"""
    await manager.connect(websocket, task_id)
    try:
        # 发送连接成功消息
        await manager.send_personal_message(
            json.dumps({
                "type": "connected",
                "message": f"Connected to task {task_id} logs"
            }),
            websocket
        )
        
        # 保持连接
        while True:
            # 接收消息（主要是保持连接活跃）
            data = await websocket.receive_text()
            # 可以处理客户端发来的消息，比如心跳包
            if data == "ping":
                await manager.send_personal_message("pong", websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, task_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket, task_id)


@app.get("/api/tasks/{task_id}/logs/history")
def get_task_logs(task_id: int, db: Session = Depends(get_db)):
    """获取任务的历史日志"""
    from app.models import TaskLog
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.timestamp).all()
    return [
        {
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "level": log.level,
            "module": log.module,
            "stage": log.stage,
            "message": log.message,
            "progress": log.progress,
            "extra_data": log.extra_data
        }
        for log in logs
    ]


if __name__ == "__main__":
    import uvicorn
    print("启动重构后的服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8080)