#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加 model_index 列
"""
import sqlite3
import os
import sys

def check_column_exists(conn, table_name, column_name):
    """检查表中是否存在指定列"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for column in columns:
        if column[1] == column_name:
            return True
    return False

def add_model_index_column():
    """为 tasks 表添加 model_index 列"""
    db_path = './data/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ 连接到数据库: {db_path}")
        
        # 检查 tasks 表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        if not cursor.fetchone():
            print("❌ tasks 表不存在")
            conn.close()
            return False
        
        # 检查 model_index 列是否已存在
        if check_column_exists(conn, 'tasks', 'model_index'):
            print("ℹ️  model_index 列已经存在，无需迁移")
            conn.close()
            return True
        
        # 添加 model_index 列
        print("🔧 正在添加 model_index 列...")
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN model_index INTEGER DEFAULT 0
        """)
        conn.commit()
        print("✅ model_index 列添加成功")
        
        # 验证添加是否成功
        if check_column_exists(conn, 'tasks', 'model_index'):
            print("✅ 验证成功：model_index 列已正确添加")
            
            # 显示表结构
            cursor.execute("PRAGMA table_info(tasks)")
            columns = cursor.fetchall()
            print("\n📋 tasks 表当前结构：")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        else:
            print("❌ 验证失败：model_index 列添加失败")
            conn.close()
            return False
        
        # 统计并更新现有记录
        cursor.execute("SELECT COUNT(*) FROM tasks")
        task_count = cursor.fetchone()[0]
        print(f"\n📊 共有 {task_count} 个任务记录")
        
        # 为现有记录设置默认值
        cursor.execute("UPDATE tasks SET model_index = 0 WHERE model_index IS NULL")
        updated_count = cursor.rowcount
        if updated_count > 0:
            conn.commit()
            print(f"✅ 已为 {updated_count} 个记录设置默认 model_index = 0")
        
        conn.close()
        print("\n🎉 数据库迁移完成！")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False

def main():
    """主函数"""
    print("="*50)
    print("数据库迁移工具 - 添加 model_index 列")
    print("="*50)
    
    # 切换到正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录: {os.getcwd()}\n")
    
    # 执行迁移
    success = add_model_index_column()
    
    if success:
        print("\n✅ 迁移成功完成！")
        return 0
    else:
        print("\n❌ 迁移失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())