"""
测试配置和fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import Base, get_db

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    
    # 覆盖依赖
    app.dependency_overrides[get_db] = override_get_db
    
    # 创建测试客户端
    with TestClient(app) as c:
        yield c
    
    # 清理
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_file():
    """创建测试文件"""
    content = b"# Test Document\nThis is a test content."
    return ("test.md", content, "text/markdown")