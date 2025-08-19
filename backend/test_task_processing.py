#!/usr/bin/env python3
"""测试任务处理功能"""
import time
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8080"

def create_task(file_path, title="测试任务"):
    """创建任务"""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'text/markdown')}
        data = {'title': title, 'model_index': '0'}
        response = requests.post(f"{BASE_URL}/api/tasks", files=files, data=data)
        return response.json()

def get_task_status(task_id):
    """获取任务状态"""
    response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
    return response.json()

def main():
    print("="*50)
    print("任务处理测试")
    print("="*50)
    
    # 创建测试文件
    test_file = "test_processing.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("# 测试文档\n\n这是一个用于测试任务处理的文档。\n")
    
    # 创建任务
    print("\n1. 创建任务...")
    task = create_task(test_file, "处理测试任务")
    task_id = task['id']
    print(f"   任务创建成功: ID={task_id}, Status={task['status']}")
    
    # 监控任务状态
    print("\n2. 监控任务状态...")
    max_wait = 30  # 最多等待30秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        task_detail = get_task_status(task_id)
        task_info = task_detail['task']
        
        print(f"   [{int(time.time() - start_time)}s] Status: {task_info['status']}, Progress: {task_info['progress']}%")
        
        if task_info['status'] in ['completed', 'failed']:
            print(f"\n3. 任务结束: {task_info['status']}")
            if task_info['error_message']:
                print(f"   错误信息: {task_info['error_message']}")
            if 'issues' in task_detail:
                print(f"   发现问题数: {len(task_detail['issues'])}")
            break
        
        time.sleep(2)
    else:
        print("\n3. 超时: 任务处理时间超过30秒")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()