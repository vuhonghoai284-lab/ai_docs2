"""检查AI输出记录"""
import sqlite3

def check_ai_outputs():
    """检查AI输出表"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 查询AI输出记录
    cursor.execute("""
        SELECT task_id, COUNT(*) as output_count
        FROM ai_outputs
        GROUP BY task_id
        ORDER BY task_id DESC
    """)
    
    results = cursor.fetchall()
    
    print("AI输出记录统计:")
    print("任务ID | 输出数量")
    print("-" * 30)
    
    for row in results:
        print(f"{row[0]} | {row[1]}")
    
    # 检查最近完成的任务是否有AI输出
    cursor.execute("""
        SELECT t.id, t.model_index, t.model_label, t.status,
               COUNT(ao.id) as output_count
        FROM tasks t
        LEFT JOIN ai_outputs ao ON t.id = ao.task_id
        WHERE t.status = 'completed' AND t.id >= 7
        GROUP BY t.id
        ORDER BY t.id DESC
    """)
    
    results = cursor.fetchall()
    
    print("\n最近完成任务的AI输出:")
    print("任务ID | 模型索引 | 模型标签 | 状态 | AI输出数")
    print("-" * 60)
    
    for row in results:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
    
    conn.close()

if __name__ == "__main__":
    check_ai_outputs()