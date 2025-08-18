#!/usr/bin/env python3
"""后端测试脚本 - 验证代码结构"""

import os
import sys

def test_backend_structure():
    """测试后端代码结构"""
    print("检查后端代码结构...")
    
    required_files = [
        'backend/main.py',
        'backend/database.py',
        'backend/file_parser.py',
        'backend/ai_service.py',
        'backend/task_processor.py',
        'backend/report_generator.py',
        'backend/config.yaml',
        'backend/requirements.txt'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 缺失")
            return False
    
    print("\n后端代码结构检查通过！")
    return True

def test_frontend_structure():
    """测试前端代码结构"""
    print("\n检查前端代码结构...")
    
    required_files = [
        'frontend/package.json',
        'frontend/tsconfig.json',
        'frontend/public/index.html',
        'frontend/src/index.tsx',
        'frontend/src/App.tsx',
        'frontend/src/api.ts',
        'frontend/src/types.ts',
        'frontend/src/pages/TaskCreate.tsx',
        'frontend/src/pages/TaskList.tsx',
        'frontend/src/pages/TaskDetail.tsx'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 缺失")
            return False
    
    print("\n前端代码结构检查通过！")
    return True

def test_data_directories():
    """测试数据目录"""
    print("\n检查数据目录...")
    
    directories = [
        'data/uploads',
        'data/reports'
    ]
    
    for dir in directories:
        if os.path.exists(dir):
            print(f"✓ {dir} 存在")
        else:
            print(f"✗ {dir} 缺失")
            os.makedirs(dir, exist_ok=True)
            print(f"  → 已创建 {dir}")
    
    return True

def main():
    print("=" * 50)
    print("AI文档测试系统 - 代码结构验证")
    print("=" * 50)
    
    # 测试各个部分
    backend_ok = test_backend_structure()
    frontend_ok = test_frontend_structure()
    data_ok = test_data_directories()
    
    print("\n" + "=" * 50)
    if backend_ok and frontend_ok and data_ok:
        print("✅ 所有检查通过！项目结构完整。")
        print("\n下一步操作：")
        print("1. 安装Python依赖：")
        print("   cd backend && pip install -r requirements.txt")
        print("\n2. 安装前端依赖：")
        print("   cd frontend && npm install")
        print("\n3. 启动后端服务：")
        print("   cd backend && python main.py")
        print("\n4. 启动前端服务：")
        print("   cd frontend && npm start")
    else:
        print("❌ 部分检查失败，请检查缺失的文件。")
    print("=" * 50)

if __name__ == "__main__":
    main()