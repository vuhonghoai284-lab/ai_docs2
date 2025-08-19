"""测试模型选择功能"""
import requests
import os
import time

# API基础URL
API_BASE = "http://localhost:8080/api"

def test_model_selection():
    """测试不同模型的选择"""
    
    # 1. 获取可用模型列表
    print("=" * 60)
    print("1. 获取可用模型列表")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE}/models")
    models_data = response.json()
    print(f"可用模型数量: {len(models_data['models'])}")
    
    for model in models_data['models']:
        print(f"  模型 {model['index']}: {model['label']}")
        print(f"    描述: {model['description']}")
        print(f"    提供商: {model['provider']}")
        print(f"    默认: {model['is_default']}")
    
    # 2. 创建测试文件
    test_content = """# 测试文档
    
这是一个测试文档，用于验证模型选择功能。

## 测试内容
1. 错别字：这理有一个错别字
2. 语法错误：我是去了商店昨天
"""
    
    test_file = "test_model_selection.md"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    print("\n" + "=" * 60)
    print("2. 测试创建任务时的模型选择")
    print("=" * 60)
    
    # 3. 测试每个模型
    for i, model in enumerate(models_data['models']):
        print(f"\n测试模型 {i}: {model['label']}")
        print("-" * 40)
        
        # 创建任务
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f, "text/markdown")}
            data = {"model_index": str(i)}  # 发送模型索引
            
            print(f"发送请求: model_index={i}")
            response = requests.post(f"{API_BASE}/tasks", files=files, data=data)
            
            if response.status_code == 200:
                task = response.json()
                print(f"✅ 任务创建成功:")
                print(f"   任务ID: {task['id']}")
                print(f"   模型标签: {task.get('model_label', 'N/A')}")
                print(f"   状态: {task['status']}")
                
                # 等待一下再获取任务详情
                time.sleep(2)
                
                # 获取任务详情验证
                detail_response = requests.get(f"{API_BASE}/tasks/{task['id']}")
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    print(f"   任务详情确认:")
                    print(f"     状态: {detail['task']['status']}")
                
                # 查询任务列表确认模型标签
                tasks_response = requests.get(f"{API_BASE}/tasks")
                if tasks_response.status_code == 200:
                    tasks = tasks_response.json()
                    for t in tasks:
                        if t['id'] == task['id']:
                            print(f"   任务列表中的模型标签: {t.get('model_label', 'N/A')}")
                            break
            else:
                print(f"❌ 创建任务失败: {response.status_code}")
                print(f"   错误: {response.text}")
    
    # 清理测试文件
    os.remove(test_file)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_model_selection()