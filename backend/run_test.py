#!/usr/bin/env python
"""
测试模式启动脚本
"""
import os
import sys
import uvicorn
from pathlib import Path

# 设置环境变量为测试模式
os.environ['APP_MODE'] = 'test'

# 确保配置文件路径正确
script_dir = Path(__file__).parent
os.chdir(script_dir)

# 初始化配置（使用测试配置）
from app.core.config import init_settings
settings = init_settings('config.test.yaml')

# 创建必要的目录
test_dirs = [
    './data/test',
    './data/test/uploads',
    './data/test/reports',
    './data/test/logs',
    './data/test/temp'
]

for dir_path in test_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# 导入应用
from app.main import app

if __name__ == "__main__":
    print("="*60)
    print("🧪 启动测试模式")
    print("="*60)
    print(f"📁 配置文件: config.test.yaml")
    print(f"🤖 AI模式: 模拟数据（不调用真实API）")
    print(f"📊 数据库: {settings.database_url}")
    print(f"🌐 服务地址: http://0.0.0.0:8080")
    print(f"📚 API文档: http://localhost:8080/docs")
    print("="*60)
    print("提示: 使用 Ctrl+C 停止服务")
    print()
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=settings.server_config.get('host', '0.0.0.0'),
        port=settings.server_config.get('port', 8080),
        reload=settings.server_config.get('reload', True),
        log_level="debug" if settings.server_config.get('debug') else "info"
    )