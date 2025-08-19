"""测试模型选择API"""
import requests
import os

# 创建测试文件
test_content = """# 测试文档
这是一个简单的测试文档。
"""

with open("test_api.md", "w", encoding="utf-8") as f:
    f.write(test_content)

# 测试API调用
print("=== 测试模型选择API ===")
print("\n1. 测试选择索引1的模型:")

with open("test_api.md", "rb") as f:
    files = {"file": ("test_api.md", f, "text/markdown")}
    data = {"model_index": "1"}
    
    print(f"   发送数据: model_index = {data['model_index']}")
    
    response = requests.post("http://localhost:8080/api/tasks", files=files, data=data)
    
    print(f"   响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   任务ID: {result['id']}")
        print(f"   模型标签: {result.get('model_label', 'N/A')}")
        print(f"   文件名: {result['file_name']}")
    else:
        print(f"   错误: {response.text}")

# 清理
os.remove("test_api.md")