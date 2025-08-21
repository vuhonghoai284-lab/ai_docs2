#!/usr/bin/env python3
"""
测试新的AI服务模块
"""
import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.ai_service_factory import ai_service_factory
from app.services.prompt_loader import prompt_loader

async def test_ai_service():
    """测试AI服务功能"""
    print("🧪 开始测试新的AI服务模块")
    
    # 测试prompt_loader
    print("\n📚 测试Prompt加载器...")
    try:
        templates = prompt_loader.list_templates()
        print(f"✅ 找到模板: {templates}")
        
        if 'document_preprocess' in templates:
            system_prompt = prompt_loader.get_system_prompt('document_preprocess')
            print(f"✅ 系统提示词长度: {len(system_prompt)}")
    except Exception as e:
        print(f"❌ Prompt加载器测试失败: {e}")
    
    # 测试AI服务
    print("\n🤖 测试AI服务...")
    try:
        # 创建AI服务实例（不使用真实模型）
        ai_service = AIService()
        
        # 测试文档预处理
        test_text = """
# 标题1
这是第一段内容。这里有一些文字。

## 子标题
这是第二段内容。这里也有一些文字。

这是第三段内容，没有标题。
        """.strip()
        
        print("📝 测试文档预处理...")
        sections = await ai_service.preprocess_document(test_text)
        print(f"✅ 文档预处理完成，获得 {len(sections)} 个章节")
        for i, section in enumerate(sections):
            print(f"  章节 {i+1}: {section.get('section_title', 'Unknown')}")
        
        # 测试问题检测
        print("\n🔍 测试问题检测...")
        issues = await ai_service.detect_issues(test_text)
        print(f"✅ 问题检测完成，发现 {len(issues)} 个问题")
        for i, issue in enumerate(issues):
            print(f"  问题 {i+1}: {issue.get('type', 'Unknown')} - {issue.get('description', 'No description')}")
        
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试实时日志
    print("\n📡 测试实时日志服务...")
    try:
        await ai_service_factory.start_realtime_logging()
        
        # 创建任务日志适配器
        task_logger = ai_service_factory.create_task_logger(1, "test")
        await task_logger.info("这是一个测试日志消息")
        
        await ai_service_factory.stop_realtime_logging()
        print("✅ 实时日志服务测试完成")
        
    except Exception as e:
        print(f"❌ 实时日志服务测试失败: {e}")
    
    print("\n🎉 AI服务模块测试完成！")

if __name__ == "__main__":
    asyncio.run(test_ai_service())