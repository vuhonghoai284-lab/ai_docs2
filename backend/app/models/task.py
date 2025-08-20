"""
任务数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime

from app.core.database import Base


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    model_index = Column(Integer, default=0)
    model_label = Column(String(100))
    document_chars = Column(Integer)
    processing_time = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)