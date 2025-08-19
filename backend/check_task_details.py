"""检查任务详细信息"""
import sqlite3

def check_task_details():
    """检查任务详细信息"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 查询最近的任务详情
    cursor.execute("""
        SELECT id, title, model_index, model_label, status, 
               error_message, processing_time, created_at, completed_at
        FROM tasks
        WHERE id >= 7
        ORDER BY id DESC
    """)
    
    results = cursor.fetchall()
    
    print("任务详细信息:")
    print("=" * 80)
    
    for row in results:
        print(f"任务ID: {row[0]}")
        print(f"  标题: {row[1]}")
        print(f"  模型索引: {row[2]}")
        print(f"  模型标签: {row[3]}")
        print(f"  状态: {row[4]}")
        print(f"  错误信息: {row[5] if row[5] else '无'}")
        print(f"  处理时间: {row[6] if row[6] else '无'} 秒")
        print(f"  创建时间: {row[7]}")
        print(f"  完成时间: {row[8] if row[8] else '未完成'}")
        print("-" * 40)
    
    conn.close()

if __name__ == "__main__":
    check_task_details()