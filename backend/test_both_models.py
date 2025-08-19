"""测试两个模型的选择和处理"""
import requests
import time
import os

API_BASE = "http://localhost:8080/api"

def test_both_models():
    """测试两个模型"""
    
    # 创建测试文件
    test_content = """# 测试文档
这是测试内容。
有个错别字：这理
语法问题：我昨天是去了
"""
    
    with open("test_both.md", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    print("=== 测试双模型选择 ===\n")
    
    # 获取模型列表
    models_resp = requests.get(f"{API_BASE}/models")
    if models_resp.status_code == 200:
        models = models_resp.json()['models']
        print(f"可用模型: {len(models)}")
        for m in models:
            print(f"  [{m['index']}] {m['label']}")
        print()
    
    # 测试每个模型
    for model_idx in [0, 1]:
        print(f"--- 测试模型 {model_idx} ---")
        
        with open("test_both.md", "rb") as f:
            files = {"file": ("test_both.md", f, "text/markdown")}
            data = {"model_index": str(model_idx)}
            
            print(f"发送: model_index={model_idx}")
            resp = requests.post(f"{API_BASE}/tasks", files=files, data=data)
            
            if resp.status_code == 200:
                task = resp.json()
                print(f"✅ 任务创建成功")
                print(f"   任务ID: {task['id']}")
                print(f"   模型标签: {task.get('model_label', 'N/A')}")
                
                # 等待处理完成
                for i in range(10):
                    time.sleep(2)
                    detail_resp = requests.get(f"{API_BASE}/tasks/{task['id']}")
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json()
                        status = detail['task']['status']
                        print(f"   [{i+1}] 状态: {status}")
                        
                        if status == 'completed':
                            print(f"   ✅ 任务完成")
                            break
                        elif status == 'failed':
                            print(f"   ❌ 任务失败: {detail['task'].get('error_message', 'Unknown')}")
                            break
            else:
                print(f"❌ 创建失败: {resp.status_code}")
                print(resp.text)
        
        print()
    
    # 清理
    os.remove("test_both.md")
    print("测试完成！")

if __name__ == "__main__":
    test_both_models()