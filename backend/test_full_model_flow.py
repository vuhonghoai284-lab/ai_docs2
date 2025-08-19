"""完整测试模型选择流程"""
import requests
import time
import json

API_BASE = "http://localhost:8080/api"

def test_full_flow():
    """测试完整的模型选择流程"""
    
    print("=" * 60)
    print("完整模型选择流程测试")
    print("=" * 60)
    
    # 1. 获取模型列表
    models_resp = requests.get(f"{API_BASE}/models")
    models = models_resp.json()['models']
    
    print(f"\n可用模型: {len(models)}")
    for m in models:
        print(f"  [{m['index']}] {m['label']}")
    
    # 2. 创建测试文档
    test_doc = """# 测试文档
这是测试内容，用于验证模型选择。
错别字：这理有问题
语法：我昨天是去了商店
"""
    
    # 3. 测试第二个模型（索引1）
    print(f"\n测试选择第二个模型（索引=1）:")
    print("-" * 40)
    
    with open("test.md", "w", encoding="utf-8") as f:
        f.write(test_doc)
    
    with open("test.md", "rb") as f:
        files = {"file": ("test.md", f, "text/markdown")}
        data = {"model_index": "1"}  # 选择第二个模型
        
        print(f"发送: model_index=1")
        resp = requests.post(f"{API_BASE}/tasks", files=files, data=data)
        
        if resp.status_code == 200:
            task = resp.json()
            print(f"✅ 任务创建成功")
            print(f"   任务ID: {task['id']}")
            print(f"   模型标签: {task.get('model_label', 'N/A')}")
            
            # 等待处理
            print("\n等待任务处理...")
            for i in range(10):
                time.sleep(2)
                status_resp = requests.get(f"{API_BASE}/tasks")
                tasks = status_resp.json()
                
                for t in tasks:
                    if t['id'] == task['id']:
                        print(f"   [{i+1}] 状态: {t['status']}, 进度: {t.get('progress', 0)}%")
                        if t['status'] in ['completed', 'failed']:
                            print(f"\n最终结果:")
                            print(f"  状态: {t['status']}")
                            print(f"  模型: {t.get('model_label', 'N/A')}")
                            print(f"  文档长度: {t.get('document_chars', 'N/A')} 字符")
                            print(f"  处理时间: {t.get('processing_time', 'N/A')} 秒")
                            print(f"  问题数: {t.get('issue_count', 'N/A')}")
                            return
                        break
        else:
            print(f"❌ 创建失败: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    test_full_flow()