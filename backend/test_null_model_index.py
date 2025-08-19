#!/usr/bin/env python3
"""测试model_index为NULL时的任务处理"""
import sqlite3
import time
import requests

def create_task_with_null_model():
    """直接在数据库中创建model_index为NULL的任务"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 插入一个model_index为NULL的任务
    cursor.execute("""
        INSERT INTO tasks (title, file_name, file_path, file_size, file_type, status, progress, model_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('测试NULL模型索引', 'test.md', './data/uploads/test.md', 100, 'md', 'pending', 0, None))
    
    task_id = cursor.lastrowid
    conn.commit()
    
    print(f"创建了任务 ID={task_id}，model_index=NULL")
    
    # 验证插入
    cursor.execute("SELECT id, title, model_index FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    print(f"验证: ID={task[0]}, Title={task[1]}, Model={task[2]}")
    
    conn.close()
    return task_id

def check_task_status(task_id):
    """检查任务状态"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status, progress, model_index, error_message FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    if task:
        print(f"任务状态: ID={task[0]}, Status={task[2]}, Progress={task[3]}, Model={task[4]}")
        if task[5]:
            print(f"错误信息: {task[5]}")
    conn.close()
    return task[2] if task else None

def main():
    print("="*50)
    print("测试 model_index 为 NULL 的情况")
    print("="*50)
    
    # 创建测试任务
    task_id = create_task_with_null_model()
    
    # 等待任务处理
    print("\n等待任务处理...")
    for i in range(10):
        time.sleep(2)
        status = check_task_status(task_id)
        if status in ['completed', 'failed']:
            break
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()