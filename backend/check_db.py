"""检查数据库中的任务记录"""
import sqlite3

def check_tasks():
    """检查任务表中的模型信息"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 查询最近的任务
    cursor.execute("""
        SELECT id, title, model_index, model_label, status, created_at 
        FROM tasks 
        ORDER BY id DESC 
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    
    print("最近的任务记录:")
    print("ID | 标题 | 模型索引 | 模型标签 | 状态 | 创建时间")
    print("-" * 80)
    
    for row in results:
        print(f"{row[0]} | {row[1][:15]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    
    conn.close()

if __name__ == "__main__":
    check_tasks()