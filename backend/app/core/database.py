"""
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import get_settings

# 获取配置
settings = get_settings()

# 创建数据库引擎
sqlite_connect_args = {
    "check_same_thread": False,
    "timeout": 30,  # 30秒超时
    "isolation_level": None  # 启用自动提交模式
} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=sqlite_connect_args,
    pool_pre_ping=True,  # 预先检查连接有效性
    pool_recycle=3600,   # 1小时后回收连接
    max_overflow=20 if "sqlite" not in settings.database_url else 0  # SQLite不支持连接池
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用作FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()