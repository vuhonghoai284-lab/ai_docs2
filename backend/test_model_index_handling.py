#!/usr/bin/env python3
"""测试model_index各种情况的处理"""
import sqlite3
import os
import time

def create_test_file():
    """创建测试文件"""
    test_file = './data/uploads/test_null_model.md'
    os.makedirs('./data/uploads', exist_ok=True)
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("# 测试文档\n\n这是用于测试NULL model_index的文档。")
    return test_file

def test_model_index_cases():
    """测试不同model_index值的情况"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 创建测试文件
    test_file = create_test_file()
    print(f"创建测试文件: {test_file}")
    
    test_cases = [
        ("NULL model_index", None),
        ("model_index = 0", 0),
        ("model_index = 1", 1),
        ("model_index = -1", -1),  # 无效索引
        ("model_index = 999", 999),  # 超出范围的索引
    ]
    
    task_ids = []
    
    for desc, model_index in test_cases:
        # 插入测试任务
        cursor.execute("""
            INSERT INTO tasks (title, file_name, file_path, file_size, file_type, status, progress, model_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (desc, 'test.md', test_file, 100, 'md', 'pending', 0, model_index))
        
        task_id = cursor.lastrowid
        task_ids.append((task_id, desc, model_index))
        print(f"\n创建任务: ID={task_id}, {desc}")
    
    conn.commit()
    conn.close()
    
    return task_ids

def check_tasks_status(task_ids):
    """检查任务状态"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("任务状态检查:")
    print("="*60)
    
    for task_id, desc, expected_model in task_ids:
        cursor.execute("""
            SELECT id, title, status, progress, model_index, error_message 
            FROM tasks WHERE id = ?
        """, (task_id,))
        task = cursor.fetchone()
        
        if task:
            print(f"\nID={task[0]}: {task[1]}")
            print(f"  状态: {task[2]}")
            print(f"  进度: {task[3]}%")
            print(f"  模型索引: {task[4]} (预期: {expected_model})")
            if task[5]:
                print(f"  错误: {task[5][:100]}...")
    
    conn.close()

def cleanup_test_tasks(task_ids):
    """清理测试任务"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    for task_id, _, _ in task_ids:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    conn.commit()
    print(f"\n清理了 {len(task_ids)} 个测试任务")
    conn.close()

def main():
    print("="*60)
    print("测试 model_index 处理")
    print("="*60)
    
    # 创建测试任务
    task_ids = test_model_index_cases()
    
    print("\n注意: 需要重启后端服务器以触发启动事件处理器")
    print("或者等待任务通过API创建后自动处理")
    print("\n等待5秒后检查状态...")
    time.sleep(5)
    
    # 检查任务状态
    check_tasks_status(task_ids)
    
    # 询问是否清理
    response = input("\n是否清理测试任务? (y/n): ")
    if response.lower() == 'y':
        cleanup_test_tasks(task_ids)
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()