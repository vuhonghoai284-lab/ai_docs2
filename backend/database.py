"""数据库模型定义"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import os

# 创建数据库目录
os.makedirs("./data", exist_ok=True)

# 数据库配置
DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 任务表
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    file_name = Column(String(200))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(20))
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    progress = Column(Float, default=0)
    model_index = Column(Integer, default=0)  # 使用的模型索引
    model_label = Column(String(100), nullable=True)  # 模型显示名称
    document_chars = Column(Integer, nullable=True)  # 文档总字符数
    processing_time = Column(Float, nullable=True)  # 处理总耗时（秒）
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 关系
    issues = relationship("Issue", back_populates="task", cascade="all, delete-orphan")
    ai_outputs = relationship("AIOutput", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")

# 检测问题表
class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    issue_type = Column(String(50))  # 语法/逻辑/完整性
    description = Column(Text)
    location = Column(String(200))
    severity = Column(String(20))  # 致命/严重/一般/提示
    confidence = Column(Float, nullable=True)  # 模型置信度 (0.0-1.0)
    suggestion = Column(Text)
    
    # 新增字段：更详细的问题信息
    original_text = Column(Text, nullable=True)  # 原文内容
    user_impact = Column(Text, nullable=True)  # 对用户的影响
    reasoning = Column(Text, nullable=True)  # 判定问题的思考原因
    context = Column(Text, nullable=True)  # 上下文信息
    
    feedback_type = Column(String(20), nullable=True)  # accept/reject/null
    feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    task = relationship("Task", back_populates="issues")

# 任务日志表
class TaskLog(Base):
    """任务日志表"""
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    level = Column(String, nullable=False)  # DEBUG, INFO, WARNING, ERROR, PROGRESS
    module = Column(String, default="system")
    stage = Column(String)  # 初始化, 文档解析, 内容分析, 报告生成, 完成, 错误
    message = Column(Text)
    progress = Column(Integer, default=0)
    extra_data = Column(JSON, default={})
    
    # 关系
    task = relationship("Task", back_populates="logs")

# AI模型输出记录表
class AIOutput(Base):
    __tablename__ = "ai_outputs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    operation_type = Column(String(50))  # preprocess/detect_issues
    section_title = Column(String(500), nullable=True)  # 章节标题（如果是按章节处理）
    section_index = Column(Integer, nullable=True)  # 章节索引
    input_text = Column(Text)  # 输入给AI的文本
    raw_output = Column(Text)  # AI的原始输出
    parsed_output = Column(JSON, nullable=True)  # 解析后的结构化输出
    status = Column(String(20))  # success/failed/parsing_error
    error_message = Column(Text, nullable=True)  # 错误信息
    tokens_used = Column(Integer, nullable=True)  # 使用的token数量
    processing_time = Column(Float, nullable=True)  # 处理时间（秒）
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    task = relationship("Task", back_populates="ai_outputs")

# 创建表
Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()