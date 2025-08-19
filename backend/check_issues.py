"""检查问题记录"""
import sqlite3

def check_issues():
    """检查问题表"""
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 查询每个任务的问题数量
    cursor.execute("""
        SELECT task_id, COUNT(*) as issue_count
        FROM issues
        GROUP BY task_id
        ORDER BY task_id DESC
    """)
    
    results = cursor.fetchall()
    
    print("任务问题统计:")
    print("任务ID | 问题数量")
    print("-" * 30)
    
    for row in results:
        print(f"{row[0]} | {row[1]}")
    
    # 检查任务7-10的问题数
    cursor.execute("""
        SELECT t.id, t.model_index, t.status, COUNT(i.id) as issue_count
        FROM tasks t
        LEFT JOIN issues i ON t.id = i.task_id
        WHERE t.id >= 7
        GROUP BY t.id
        ORDER BY t.id DESC
    """)
    
    results = cursor.fetchall()
    
    print("\n任务7-10的问题统计:")
    print("任务ID | 模型索引 | 状态 | 问题数")
    print("-" * 40)
    
    for row in results:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_issues()