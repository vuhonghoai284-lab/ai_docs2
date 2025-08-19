"""
测试增强后的问题检测功能
模拟生成包含详细信息的问题数据
"""
import sqlite3
from datetime import datetime
import json

def create_test_task_with_enhanced_issues():
    """创建测试任务并添加包含详细信息的问题"""
    
    # 连接数据库
    conn = sqlite3.connect('./data/app.db')
    cursor = conn.cursor()
    
    # 创建测试任务
    cursor.execute('''
        INSERT INTO tasks (title, file_name, file_path, file_size, file_type, status, progress, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        '增强评估功能测试',
        'test_document.md', 
        './uploads/test.md', 
        5000, 
        'md', 
        'completed', 
        100,
        datetime.now().isoformat()
    ))
    
    task_id = cursor.lastrowid
    print(f"创建任务成功，任务ID: {task_id}")
    
    # 创建增强的问题数据
    enhanced_issues = [
        {
            'task_id': task_id,
            'issue_type': '语法错误',
            'description': '文档中存在明显的错别字，"以中"应该是"一种"',
            'location': '第一章 第1.1节 背景介绍',
            'severity': '高',
            'suggestion': '将"苹果是以中水果"修改为"苹果是一种水果"',
            'original_text': '苹果是以中水果，富含维生素和矿物质',
            'user_impact': '错别字会影响文档的专业性，降低用户的信任度，可能导致理解困惑',
            'reasoning': '检测到"以中"是常见的输入法错误，正确的表达应该是"一种"。这个错误出现在重要的定义句中，会严重影响文档质量',
            'context': '该句出现在背景介绍的开头部分，是对主题的基本定义'
        },
        {
            'task_id': task_id,
            'issue_type': '逻辑错误',
            'description': '因果关系不成立，天空颜色与草的颜色没有直接因果关系',
            'location': '第二章 第2.1节 架构设计',
            'severity': '中',
            'suggestion': '删除或重新组织这个逻辑关系，使用更合理的论述',
            'original_text': '因为天是蓝色的，所以草是绿色的',
            'user_impact': '逻辑错误会让读者质疑文档的严谨性，影响整体可信度',
            'reasoning': '天空的颜色（大气散射）与植物的颜色（叶绿素）在科学上没有因果关系，这是明显的逻辑谬误',
            'context': '在讨论系统架构时突然出现的不相关论述'
        },
        {
            'task_id': task_id,
            'issue_type': '内容缺失',
            'description': '缺少标点符号，影响句子的可读性',
            'location': '第三章 总结',
            'severity': '低',
            'suggestion': '在列举项之间添加顿号或逗号：苹果、香蕉、橘子',
            'original_text': '我今天去了超市买了很多东西包括苹果香蕉橘子',
            'user_impact': '缺少标点会让句子难以阅读，特别是在列举多个项目时',
            'reasoning': '中文写作规范要求在并列的词语之间使用顿号或逗号分隔，这里明显缺少了必要的标点符号',
            'context': '总结部分的举例说明'
        },
        {
            'task_id': task_id,
            'issue_type': '术语不当',
            'description': '专业术语使用不准确，"前后端分离"的英文应该是"Frontend-Backend Separation"',
            'location': '第二章 第2.2节 核心功能',
            'severity': '中',
            'suggestion': '统一使用准确的专业术语，并在首次出现时提供英文对照',
            'original_text': '系统采用前后分离架构（Front-Back Split）',
            'user_impact': '不准确的术语可能导致专业读者的困惑，影响技术交流',
            'reasoning': '在软件工程领域，标准术语是"Frontend-Backend Separation"或"Decoupled Architecture"，使用非标准术语会造成理解偏差',
            'context': '技术架构说明部分'
        },
        {
            'task_id': task_id,
            'issue_type': '格式问题',
            'description': '代码示例缺少语言标识，影响语法高亮',
            'location': '第二章 示例代码',
            'severity': '低',
            'suggestion': '在代码块开始处添加语言标识，如 ```python',
            'original_text': '```\ndef hello():\n    print("Hello")\n```',
            'user_impact': '缺少语言标识会导致代码高亮失效，降低代码可读性',
            'reasoning': 'Markdown规范建议在代码块中指定编程语言，以便正确的语法高亮',
            'context': 'Python代码示例展示'
        }
    ]
    
    # 插入问题数据
    for issue in enhanced_issues:
        cursor.execute('''
            INSERT INTO issues (
                task_id, issue_type, description, location, severity, suggestion,
                original_text, user_impact, reasoning, context,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue['task_id'],
            issue['issue_type'],
            issue['description'],
            issue['location'],
            issue['severity'],
            issue['suggestion'],
            issue['original_text'],
            issue['user_impact'],
            issue['reasoning'],
            issue['context'],
            datetime.now().isoformat()
        ))
    
    conn.commit()
    print(f"成功创建 {len(enhanced_issues)} 个增强问题")
    
    # 查询验证
    cursor.execute('SELECT COUNT(*) FROM issues WHERE task_id = ?', (task_id,))
    count = cursor.fetchone()[0]
    print(f"任务 {task_id} 共有 {count} 个问题")
    
    conn.close()
    
    return task_id

if __name__ == "__main__":
    task_id = create_test_task_with_enhanced_issues()
    print(f"\n测试任务创建完成！")
    print(f"请访问 http://localhost:3002/task/{task_id} 查看增强后的问题展示")
    print("\n增强功能包括：")
    print("1. 显示原文内容片段")
    print("2. 说明对用户的影响")
    print("3. 展示AI判定的推理过程")
    print("4. 提供上下文信息")
    print("5. 支持分页浏览")
    print("6. 紧凑的展示布局")