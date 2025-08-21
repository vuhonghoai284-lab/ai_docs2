#!/usr/bin/env python3
"""
快速API测试启动脚本
"""
import sys
import os
import subprocess

# 添加项目目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """执行API测试"""
    print("🧪 启动AI文档测试系统API测试...")
    
    # 检查是否在正确的目录
    if not os.path.exists("tests"):
        print("❌ 请在backend目录下运行此脚本")
        return 1
    
    # 执行测试
    try:
        # 使用python -m方式执行，确保模块路径正确
        cmd = [sys.executable, "-m", "tests.run_tests"]
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        return result.returncode
    
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())