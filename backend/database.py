"""数据库模型定义"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 关系
    issues = relationship("Issue", back_populates="task", cascade="all, delete-orphan")

# 检测问题表
class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    issue_type = Column(String(50))  # 语法/逻辑/完整性
    description = Column(Text)
    location = Column(String(200))
    severity = Column(String(20))  # 高/中/低
    suggestion = Column(Text)
    feedback_type = Column(String(20), nullable=True)  # accept/reject/null
    feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    task = relationship("Task", back_populates="issues")

# 创建表
Base.metadata.create_all(bind=engine)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()