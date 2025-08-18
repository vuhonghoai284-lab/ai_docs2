"""任务处理模块"""
import asyncio
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from database import Task, Issue
from file_parser import FileParser
from ai_service import AIService

class TaskProcessor:
    """任务处理器"""
    
    def __init__(self):
        self.file_parser = FileParser()
        self.ai_service = AIService()
    
    def split_text(self, text: str, chunk_size: int = 8000) -> List[str]:
        """文本分块"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])
        return chunks
    
    async def process_task(self, task_id: int, db: Session):
        """处理单个任务"""
        # 获取任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"任务不存在: {task_id}")
            return
        
        # 更新状态为处理中
        task.status = 'processing'
        task.progress = 0
        db.commit()
        
        try:
            # 1. 解析文件
            print(f"开始解析文件: {task.file_path}")
            text = self.file_parser.parse(task.file_path)
            
            # 更新进度
            task.progress = 20
            db.commit()
            
            # 2. 文本分块
            chunks = self.split_text(text, 8000)
            print(f"文本分块完成，共{len(chunks)}块")
            
            # 3. AI检测每个文本块（支持进度回调）
            all_issues = []
            
            # 定义进度回调函数
            async def update_progress(message: str, progress: int):
                """更新任务进度和消息"""
                task.progress = min(progress, 95)  # 留5%给最后的保存步骤
                task.message = message
                db.commit()
                print(f"[进度 {progress}%] {message}")
            
            for i, chunk in enumerate(chunks):
                print(f"处理第{i+1}/{len(chunks)}块")
                
                # 计算当前块的进度范围
                base_progress = 20 + (70 * i / len(chunks))
                chunk_progress_range = 70 / len(chunks)
                
                # 创建当前块的进度回调
                async def chunk_progress_callback(msg: str, pct: int):
                    """将块内的进度转换为总体进度"""
                    actual_progress = base_progress + (chunk_progress_range * pct / 100)
                    await update_progress(f"[块{i+1}/{len(chunks)}] {msg}", int(actual_progress))
                
                # 使用进度回调检测问题
                issues = await self.ai_service.detect_issues(chunk, chunk_progress_callback)
                
                # 添加块索引到位置信息
                for issue in issues:
                    if len(chunks) > 1:
                        issue['location'] = f"第{i+1}部分 - {issue.get('location', '')}"
                all_issues.extend(issues)
            
            # 4. 保存问题到数据库
            await update_progress("正在保存检测结果...", 95)
            print(f"检测到{len(all_issues)}个问题")
            for issue_data in all_issues:
                issue = Issue(
                    task_id=task_id,
                    issue_type=issue_data.get('type', '未知'),
                    description=issue_data.get('description', ''),
                    location=issue_data.get('location', ''),
                    severity=issue_data.get('severity', '中'),
                    suggestion=issue_data.get('suggestion', '')
                )
                db.add(issue)
            
            # 5. 完成任务
            task.status = 'completed'
            task.progress = 100
            task.message = f"文档检测完成，发现 {len(all_issues)} 个问题"
            task.completed_at = datetime.now()
            db.commit()
            
            print(f"任务{task_id}处理完成")
            
        except Exception as e:
            # 处理失败
            print(f"任务{task_id}处理失败: {str(e)}")
            task.status = 'failed'
            task.error_message = str(e)
            db.commit()

# 全局任务处理器实例
task_processor = TaskProcessor()