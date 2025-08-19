#!/usr/bin/env python3
"""测试自定义配置文件和prompts目录的示例"""

import asyncio
from ai_service import AIService

async def test_custom_config():
    """测试使用自定义配置文件和prompts目录"""
    
    # 示例1: 使用默认配置
    print("1. 使用默认配置初始化AI服务:")
    ai_service_default = AIService()
    print(f"   Provider: {ai_service_default.provider}")
    print(f"   Model: {ai_service_default.model_name}")
    print()
    
    # 示例2: 使用自定义配置文件
    print("2. 使用自定义配置文件:")
    ai_service_custom = AIService(config_path='test_config.yaml')
    print(f"   Provider: {ai_service_custom.provider}")
    print(f"   Model: {ai_service_custom.model_name}")
    print()
    
    # 示例3: 使用自定义prompts目录
    print("3. 使用自定义prompts目录:")
    ai_service_prompts = AIService(prompts_dir='./custom_prompts')
    print(f"   Prompts目录已设置为: ./custom_prompts")
    print()
    
    # 示例4: 同时使用自定义配置文件和prompts目录
    print("4. 同时使用自定义配置文件和prompts目录:")
    ai_service_both = AIService(
        config_path='test_config.yaml',
        prompts_dir='./prompts',
        model_index=0
    )
    print(f"   Provider: {ai_service_both.provider}")
    print(f"   Model: {ai_service_both.model_name}")
    print(f"   使用prompts目录: ./prompts")
    print()
    
    # 测试文档预处理
    test_text = """
    这是一个测试文档。
    
    第一章：介绍
    这是第一章的内容。
    
    第二章：详细说明
    这是第二章的内容。
    """
    
    print("5. 测试文档预处理功能:")
    sections = await ai_service_both.preprocess_document(test_text)
    print(f"   识别到 {len(sections)} 个章节")
    for section in sections:
        print(f"   - {section.get('section_title', '未知章节')}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI服务配置加载测试")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(test_custom_config())
    except Exception as e:
        print(f"错误: {e}")
        print("\n提示: 确保配置文件和prompts目录存在")