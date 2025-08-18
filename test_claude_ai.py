"""测试Claude AI服务"""
import asyncio
import os
import sys

# 设置工作目录
os.chdir('/mnt/d/projects/ai_docs/ai_doc_test/backend')
sys.path.append('/mnt/d/projects/ai_docs/ai_doc_test/backend')

from ai_service import AIService

async def test_ai_service():
    """测试AI服务"""
    print("=== AI文档检测服务测试 ===\n")
    
    # 初始化服务
    ai_service = AIService()
    
    if ai_service.use_mock:
        print("⚠️  使用模拟模式（未检测到ANTHROPIC_API_KEY）")
        print("💡 要使用真实Claude API，请设置环境变量：")
        print("   export ANTHROPIC_API_KEY=your_api_key")
    else:
        print("✅ 使用真实Claude API")
    
    print("\n" + "="*50)
    
    # 测试文档
    test_doc = """
    # AI文档测试系统使用指南
    
    这是一个测试文档，用于验证AI文档质量检测功能。
    
    ## 功能介绍
    
    本系统可以检测文档中的语法错误、逻辑问题和内容质量问题，这段话很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长。
    
    主要特性包括
    - 语法检查
    - 逻辑分析  
    - 内容评估
    
    使用方法
    1. 上传文档
    2. 等待分析
    3. 查看结果
    
    注意：这是测试版本
    """
    
    print("\n📄 测试文档内容:")
    print("-" * 30)
    print(test_doc)
    print("-" * 30)
    
    print("\n🔍 开始AI检测...")
    try:
        issues = await ai_service.detect_issues(test_doc)
        
        print(f"\n✅ 检测完成！发现 {len(issues)} 个问题：")
        print("="*50)
        
        for i, issue in enumerate(issues, 1):
            print(f"\n问题 #{i}:")
            print(f"  类型: {issue.get('type', 'N/A')}")
            print(f"  描述: {issue.get('description', 'N/A')}")
            print(f"  位置: {issue.get('location', 'N/A')}")
            print(f"  严重程度: {issue.get('severity', 'N/A')}")
            print(f"  建议: {issue.get('suggestion', 'N/A')}")
        
        if not issues:
            print("🎉 未发现任何问题，文档质量良好！")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "="*50)
    print("测试完成！")

if __name__ == "__main__":
    asyncio.run(test_ai_service())