"""数据库迁移脚本 - 添加新字段"""
import sqlite3
import os

def migrate_database():
    """添加新字段到tasks表"""
    db_path = './data/app.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加model_label字段
        if 'model_label' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN model_label VARCHAR(100)")
            print("✅ 添加字段: model_label")
        else:
            print("字段已存在: model_label")
        
        # 添加document_chars字段
        if 'document_chars' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN document_chars INTEGER")
            print("✅ 添加字段: document_chars")
        else:
            print("字段已存在: document_chars")
        
        # 添加processing_time字段
        if 'processing_time' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN processing_time FLOAT")
            print("✅ 添加字段: processing_time")
        else:
            print("字段已存在: processing_time")
        
        conn.commit()
        print("\n数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()