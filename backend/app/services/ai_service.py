"""AI服务统一接口 - 整合文档处理和问题检测功能"""
import time
import logging
from typing import List, Dict, Optional, Callable
from sqlalchemy.orm import Session

from app.services.ai_service_factory import ai_service_factory
from app.services.realtime_logger import TaskLoggerAdapter


class AIService:
    """AI服务统一接口 - 提供与原有ai_service.py兼容的接口"""
    
    def __init__(self, db_session: Optional[Session] = None, model_index: Optional[int] = None, settings=None):
        """
        初始化AI服务
        
        Args:
            db_session: 数据库会话
            model_index: 模型索引
            settings: 设置对象
        """
        self.db = db_session
        self.settings = settings
        self.model_index = model_index or (settings.default_model_index if settings else 0)
        
        # 初始化日志
        self.logger = logging.getLogger(f"ai_service.{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # 确保日志能输出到控制台
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 获取AI服务组件
        if settings:
            self.services = ai_service_factory.get_service_for_model(
                self.model_index, 
                settings, 
                db_session
            )
        else:
            # 如果没有设置，使用模拟服务
            self.services = {
                'mock_service': None,
                'document_processor': None,
                'issue_detector': None
            }
        
        self.logger.info(f"🤖 AI服务初始化完成，模型索引: {self.model_index}")
        
        # 检查服务状态
        if self.services.get('document_processor') and self.services.get('issue_detector'):
            self.logger.info("✅ 使用真实AI服务")
            self.is_real_service = True
        else:
            self.logger.info("🔧 使用模拟AI服务")
            self.is_real_service = False
    
    async def preprocess_document(self, text: str, task_id: Optional[int] = None, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        预处理文档：章节分割和内容整理
        
        Args:
            text: 文档文本内容
            task_id: 任务ID
            progress_callback: 进度回调函数
            
        Returns:
            章节列表
        """
        self.logger.info("📝 开始文档预处理...")
        
        # 创建任务日志适配器
        if task_id:
            task_logger = ai_service_factory.create_task_logger(task_id, "preprocess")
            await task_logger.info("开始文档预处理", {"text_length": len(text)})
        
        try:
            if self.is_real_service and self.services.get('document_processor'):
                # 使用真实的文档处理器
                sections = await self.services['document_processor'].preprocess_document(
                    text, task_id, progress_callback
                )
            else:
                # 使用模拟服务或简单处理
                if progress_callback:
                    await progress_callback("使用简单文档分割...", 10)
                
                sections = self._simple_document_split(text)
                
                if progress_callback:
                    await progress_callback(f"文档分割完成，共 {len(sections)} 个章节", 20)
            
            if task_id:
                await task_logger.info(f"文档预处理完成，获得 {len(sections)} 个章节")
            
            return sections
            
        except Exception as e:
            self.logger.error(f"❌ 文档预处理失败: {str(e)}")
            if task_id:
                await task_logger.error(f"文档预处理失败: {str(e)}")
            
            # 降级到简单分割
            return self._simple_document_split(text)
    
    async def detect_issues(self, text: str, progress_callback: Optional[Callable] = None, task_id: Optional[int] = None) -> List[Dict]:
        """
        检测文档问题
        
        Args:
            text: 文档文本内容
            progress_callback: 进度回调函数
            task_id: 任务ID
            
        Returns:
            问题列表
        """
        self.logger.info("🔍 开始问题检测...")
        
        # 创建任务日志适配器
        if task_id:
            task_logger = ai_service_factory.create_task_logger(task_id, "detect_issues")
            await task_logger.info("开始问题检测", {"text_length": len(text)})
        
        try:
            # 先进行文档预处理
            sections = await self.preprocess_document(text, task_id, progress_callback)
            
            if self.is_real_service and self.services.get('issue_detector'):
                # 使用真实的问题检测器
                issues = await self.services['issue_detector'].detect_issues(
                    sections, task_id, progress_callback
                )
            else:
                # 使用模拟服务
                if progress_callback:
                    await progress_callback("使用模拟问题检测...", 50)
                
                issues = self._mock_issue_detection(sections)
                
                if progress_callback:
                    await progress_callback(f"问题检测完成，发现 {len(issues)} 个问题", 100)
            
            if task_id:
                await task_logger.info(f"问题检测完成，发现 {len(issues)} 个问题")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"❌ 问题检测失败: {str(e)}")
            if task_id:
                await task_logger.error(f"问题检测失败: {str(e)}")
            
            return []
    
    def _simple_document_split(self, text: str) -> List[Dict]:
        """
        简单的文档分割方法（降级方案）
        
        Args:
            text: 文档文本
            
        Returns:
            章节列表
        """
        # 按段落分割，每个段落作为一个章节
        paragraphs = text.split('\n\n')
        sections = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip() and len(paragraph.strip()) > 20:
                sections.append({
                    'section_title': f'第{i+1}段',
                    'content': paragraph.strip(),
                    'level': 1
                })
        
        if not sections:
            # 如果没有段落，整个文档作为一个章节
            sections = [{
                'section_title': '文档内容',
                'content': text,
                'level': 1
            }]
        
        self.logger.info(f"简单文档分割完成，共 {len(sections)} 个章节")
        return sections
    
    def _mock_issue_detection(self, sections: List[Dict]) -> List[Dict]:
        """
        模拟问题检测（降级方案）
        
        Args:
            sections: 章节列表
            
        Returns:
            模拟问题列表
        """
        issues = []
        
        # 简单的规则检测
        for section in sections:
            content = section.get('content', '')
            section_title = section.get('section_title', '未知章节')
            
            # 检查错别字（简单示例）
            common_typos = ['的的', '了了', '是是', '在在']
            for typo in common_typos:
                if typo in content:
                    issues.append({
                        'type': '错别字',
                        'description': f'发现重复字词：{typo}',
                        'location': section_title,
                        'severity': '一般',
                        'confidence': 0.9,
                        'suggestion': f'将"{typo}"修改为"{typo[0]}"',
                        'original_text': typo,
                        'user_impact': '影响阅读流畅性',
                        'reasoning': '重复字词影响文档质量',
                        'context': f'在章节"{section_title}"中发现'
                    })
            
            # 检查句子长度
            sentences = content.split('。')
            for sentence in sentences:
                if len(sentence) > 200:
                    issues.append({
                        'type': '句子过长',
                        'description': '句子过长，建议拆分为多个短句以提高可读性',
                        'location': section_title,
                        'severity': '提示',
                        'confidence': 0.7,
                        'suggestion': '建议将长句拆分为多个短句',
                        'original_text': sentence[:50] + '...',
                        'user_impact': '可能影响理解',
                        'reasoning': '过长的句子影响阅读理解',
                        'context': f'在章节"{section_title}"中'
                    })
        
        self.logger.info(f"模拟问题检测完成，发现 {len(issues)} 个问题")
        return issues
    
    async def call_api(self, prompt: str) -> Dict:
        """
        通用API调用方法（保持兼容性）
        
        Args:
            prompt: 提示词
            
        Returns:
            API响应
        """
        try:
            if self.services.get('mock_service'):
                # 使用模拟服务
                return await self.services['mock_service'].call_api(prompt)
            else:
                # 简单响应
                return {
                    "status": "success",
                    "content": f"这是对提示词的模拟响应: {prompt[:100]}..."
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}