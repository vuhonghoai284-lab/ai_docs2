"""测试动态文本分割功能"""
import asyncio
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Task
from task_processor import TaskProcessor

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_dynamic_chunking():
    """测试动态分块功能"""
    
    # 创建内存数据库用于测试
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 创建测试任务
    test_task = Task(
        id=999,
        title="测试动态分块",
        file_name="test.md",
        file_path="test.md",
        file_size=1000,
        file_type="md",
        status='pending',
        progress=0,
        model_index=0  # 使用第一个模型配置
    )
    db.add(test_task)
    db.commit()
    
    # 创建处理器
    processor = TaskProcessor()
    
    # 测试不同模型配置的分块
    test_configs = [
        {
            "name": "大模型配置",
            "context_window": 128000,
            "reserved_tokens": 2000,
            "expected_chunk_size": int((128000 - 2000) * 0.8)  # 100800
        },
        {
            "name": "中等模型配置", 
            "context_window": 32000,
            "reserved_tokens": 2000,
            "expected_chunk_size": int((32000 - 2000) * 0.8)  # 24000
        },
        {
            "name": "小模型配置",
            "context_window": 8000,
            "reserved_tokens": 1000,
            "expected_chunk_size": int((8000 - 1000) * 0.8)  # 5600
        }
    ]
    
    # 生成测试文本（150000字符，用于测试分块）
    test_text = "这是一个测试文档。" * 15000  # 约150000字符
    
    print("=" * 60)
    print("动态文本分割测试")
    print("=" * 60)
    print(f"测试文本长度: {len(test_text)} 字符\n")
    
    for config in test_configs:
        print(f"\n测试配置: {config['name']}")
        print(f"  - 上下文窗口: {config['context_window']} tokens")
        print(f"  - 预留tokens: {config['reserved_tokens']} tokens")
        print(f"  - 可用tokens: {config['context_window'] - config['reserved_tokens']} tokens")
        print(f"  - 计算得出的chunk_size: {config['expected_chunk_size']} 字符")
        
        # 调用分割函数
        chunks = processor.split_text(test_text, config)
        
        print(f"  - 分割结果: {len(chunks)} 块")
        for i, chunk in enumerate(chunks):
            print(f"    块 {i+1}: {len(chunk)} 字符")
        
        # 验证分块结果
        total_chars = sum(len(chunk) for chunk in chunks)
        print(f"  - 总字符数验证: {total_chars} (应该等于 {len(test_text)})")
        assert total_chars == len(test_text), "分块后总字符数不匹配！"
        
        # 验证每块大小不超过限制
        for i, chunk in enumerate(chunks):
            assert len(chunk) <= config['expected_chunk_size'], \
                f"块 {i+1} 大小 ({len(chunk)}) 超过限制 ({config['expected_chunk_size']})"
        
        print(f"  ✅ 配置 '{config['name']}' 测试通过！")
    
    print("\n" + "=" * 60)
    print("✨ 所有测试通过！动态文本分割功能正常工作。")
    print("=" * 60)
    
    # 清理
    db.close()

if __name__ == "__main__":
    asyncio.run(test_dynamic_chunking())