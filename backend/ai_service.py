"""AI服务模块 - 使用LangChain调用OpenAI兼容API（修复版）"""
import json
import re
import time
import logging
from typing import List, Dict, Optional, Callable
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from prompt_loader import prompt_loader, PromptLoader
from config_loader import get_ai_service_config
from sqlalchemy.orm import Session
from database import AIOutput

# 定义文档章节模型
class DocumentSection(BaseModel):
    """文档章节"""
    section_title: str = Field(description="章节标题")
    content: str = Field(description="章节内容")
    level: int = Field(description="章节层级，1为一级标题，2为二级标题等")

class DocumentStructure(BaseModel):
    """文档结构"""
    sections: List[DocumentSection] = Field(description="文档章节列表")

# 定义结构化输出模型
class DocumentIssue(BaseModel):
    """文档问题模型"""
    type: str = Field(description="问题类型：2-6个字的简短描述，如'错别字'、'语法错误'、'逻辑不通'、'内容缺失'、'格式问题'等，由模型根据实际问题自行判断")
    description: str = Field(description="详细的问题描述，清晰说明具体问题点，包括问题的表现、位置和影响，至少30字以上")
    location: str = Field(description="问题所在位置")
    severity: str = Field(description="基于用户影响程度的严重等级：致命（导致无法使用或严重误导）/严重（影响核心功能理解）/一般（影响质量但不影响理解）/提示（优化建议）")
    confidence: float = Field(description="模型对此问题判定的置信度，范围0.0-1.0", default=0.8)
    suggestion: str = Field(description="修改建议：直接给出修改后的完整内容，而不是描述如何修改")
    original_text: str = Field(description="包含问题的原文内容关键片段，10~30字符", default="")
    user_impact: str = Field(description="该问题对用户阅读理解的影响，10~30字符", default="")
    reasoning: str = Field(description="判定为问题的详细分析和推理过程，20~100字符", default="")
    context: str = Field(description="包含问题的原文内容的上下文片段内容，长度20~100字符", default="")

class DocumentIssues(BaseModel):
    """文档问题列表"""
    issues: List[DocumentIssue] = Field(description="发现的所有问题", default=[])

class AIService:
    """AI服务封装 - 使用LangChain和OpenAI兼容API"""
    
    def __init__(self, db_session: Optional[Session] = None, model_index: Optional[int] = None, config_path: Optional[str] = None, prompts_dir: Optional[str] = None):
        """初始化AI服务
        
        Args:
            db_session: 数据库会话
            model_index: 模型索引
            config_path: 配置文件路径，如果不指定则使用默认的config.yaml
            prompts_dir: 提示词模板目录路径，如果不指定则使用默认的prompts目录
        """
        self.db = db_session
        # 使用配置加载器获取配置，支持自定义配置文件路径
        self.config = get_ai_service_config(model_index, config_path)
        
        # 从配置中提取参数
        self.provider = self.config['provider']
        self.api_key = self.config['api_key']
        self.api_base = self.config['base_url']
        self.model_name = self.config['model']
        self.temperature = self.config['temperature']
        self.max_tokens = self.config['max_tokens']
        self.timeout = self.config['timeout']
        self.max_retries = self.config['max_retries']
        
        # 添加上下文窗口和预留tokens配置
        self.context_window = self.config.get('context_window', 32000)  # 默认32k
        self.reserved_tokens = self.config.get('reserved_tokens', 2000)  # 默认预留2000
        
        # 初始化prompt loader - 支持自定义prompts目录
        if prompts_dir:
            self.prompt_loader = PromptLoader(prompts_dir)
        else:
            self.prompt_loader = prompt_loader  # 使用默认的全局实例
        
        # 初始化日志
        self.logger = logging.getLogger(f"ai_service.{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        
        # 确保日志能输出到控制台
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info(f"🤖 AI服务配置: Provider={self.provider}, Model={self.model_name}")
        
        try:
            # 初始化ChatOpenAI模型（兼容OpenAI和Anthropic）
            self.model = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                request_timeout=self.timeout,
                max_retries=self.max_retries
            )
            
            # 初始化解析器
            self.structure_parser = PydanticOutputParser(pydantic_object=DocumentStructure)
            self.issues_parser = PydanticOutputParser(pydantic_object=DocumentIssues)
            self.logger.info("✅ AI服务初始化成功")
            
        except Exception as e:
            self.logger.error(f"❌ AI服务初始化失败: {str(e)}")
            raise
    
    async def preprocess_document(self, text: str, task_id: Optional[int] = None) -> List[Dict]:
        """预处理文档：章节分割和内容整理 - 通过AI一次性完成"""
        self.logger.info("📝 开始文档预处理...")
        start_time = time.time()
        
        try:
            # 从模板加载提示词
            system_prompt = self.prompt_loader.get_system_prompt('document_preprocess')
            
            # 构建用户提示
            user_prompt = self.prompt_loader.get_user_prompt(
                'document_preprocess',
                format_instructions=self.structure_parser.get_format_instructions(),
                document_content=text[:10000]  # 限制长度以避免超出token限制
            )

            # 创建消息
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 调用模型
            response = await asyncio.to_thread(self.model.invoke, messages)
            processing_time = time.time() - start_time
            
            # 保存AI输出到数据库
            if self.db and task_id:
                ai_output = AIOutput(
                    task_id=task_id,
                    operation_type="preprocess",
                    input_text=text[:10000],  # 保存部分输入文本
                    raw_output=response.content,
                    processing_time=processing_time,
                    status="success"
                )
            
            # 解析响应
            try:
                content = response.content
                self.logger.info(f"📥 收到预处理响应 (耗时: {processing_time:.2f}s)")
                self.logger.debug(f"原始响应 (前500字符): {str(content)[:500]}")
                
                # 尝试解析JSON
                if isinstance(content, str):
                    self.logger.debug(f"响应长度: {len(content)} 字符")
                    
                    # 查找JSON内容
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        self.logger.debug(f"找到JSON (前200字符): {json_str[:200]}...")
                        
                        try:
                            result = json.loads(json_str)
                            self.logger.info(f"✅ 预处理JSON解析成功，包含 {len(result.get('sections', []))} 个章节")
                        except json.JSONDecodeError as je:
                            self.logger.error(f"❌ 预处理JSON解析失败: {str(je)}")
                            self.logger.error(f"JSON内容: {json_str[:500]}...")
                            # 如果没有找到JSON，返回原文作为单一章节
                            result = {
                                "sections": [{
                                    "section_title": "文档内容",
                                    "content": text,
                                    "level": 1
                                }]
                            }
                    else:
                        self.logger.warning("⚠️ 预处理响应中未找到JSON格式")
                        self.logger.debug(f"完整响应: {content[:1000]}...")
                        # 如果没有找到JSON，返回原文作为单一章节
                        result = {
                            "sections": [{
                                "section_title": "文档内容",
                                "content": text,
                                "level": 1
                            }]
                        }
                else:
                    self.logger.warning(f"⚠️ 预处理响应不是字符串: {type(content)}")
                    result = {"sections": [{"section_title": "文档内容", "content": text, "level": 1}]}
                
                # 更新数据库中的解析结果
                if self.db and task_id:
                    ai_output.parsed_output = result
                    self.db.add(ai_output)
                    self.db.commit()
                
                self.logger.info(f"✅ 文档预处理完成，识别到 {len(result.get('sections', []))} 个章节")
                return result.get('sections', [])
                
            except Exception as e:
                import traceback
                self.logger.error(f"⚠️ 文档结构解析失败，使用原始文本: {str(e)}")
                self.logger.error(f"错误类型: {type(e).__name__}")
                self.logger.error(f"完整堆栈:\n{traceback.format_exc()}")
                
                # 保存解析错误信息
                if self.db and task_id:
                    ai_output.status = "parsing_error"
                    ai_output.error_message = str(e)
                    self.db.add(ai_output)
                    self.db.commit()
                
                return [{"section_title": "文档内容", "content": text, "level": 1}]
                
        except Exception as e:
            self.logger.error(f"❌ 文档预处理失败: {str(e)}")
            processing_time = time.time() - start_time
            
            # 保存错误信息到数据库
            if self.db and task_id:
                ai_output = AIOutput(
                    task_id=task_id,
                    operation_type="preprocess",
                    input_text=text[:10000],
                    raw_output="",
                    status="failed",
                    error_message=str(e),
                    processing_time=processing_time
                )
                self.db.add(ai_output)
                self.db.commit()
            
            # 返回原始文本作为单一章节
            return [{"section_title": "文档内容", "content": text, "level": 1}]
    
    async def detect_issues(self, text: str, progress_callback: Optional[Callable] = None, task_id: Optional[int] = None) -> List[Dict]:
        """调用AI检测文档问题 - 使用异步批量处理"""
        
        # 如果文本太短，直接返回空列表
        if len(text) < 50:
            return []
        
        # 更新进度：开始文档预处理
        if progress_callback:
            await progress_callback("正在分析文档结构...", 10)
        
        # 先进行文档预处理
        sections = await self.preprocess_document(text, task_id)
        total_sections = len(sections)
        
        if progress_callback:
            await progress_callback(f"文档已拆分为 {total_sections} 个章节", 20)
        
        # 过滤掉太短的章节
        valid_sections = [
            section for section in sections 
            if len(section.get('content', '')) >= 20
        ]
        
        if not valid_sections:
            if progress_callback:
                await progress_callback("没有有效的章节需要检测", 100)
            return []
        
        self.logger.info(f"📊 准备检测 {len(valid_sections)} 个有效章节")
        
        # 创建异步检测任务
        async def detect_section_issues(section: Dict, index: int) -> List[Dict]:
            """异步检测单个章节的问题"""
            section_title = section.get('section_title', '未知章节')
            section_content = section.get('content', '')
            section_start_time = time.time()
            
            # 更新进度
            progress = 20 + int((index / len(valid_sections)) * 70)
            if progress_callback:
                await progress_callback(f"正在检测章节 {index + 1}/{len(valid_sections)}: {section_title}", progress)
            
            self.logger.debug(f"🔍 [{index + 1}/{len(valid_sections)}] 检测章节: {section_title}")
            
            try:
                # 从模板加载提示词
                system_prompt = self.prompt_loader.get_system_prompt('document_detect_issues')
                
                # 构建用户提示
                user_prompt = self.prompt_loader.get_user_prompt(
                    'document_detect_issues',
                    section_title=section_title,
                    format_instructions=self.issues_parser.get_format_instructions(),
                    section_content=section_content[:4000]  # 限制每个章节的长度
                )

                # 创建消息
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                # 打印调用信息
                self.logger.info(f"📤 调用模型检测章节 '{section_title}'")
                self.logger.debug(f"System Prompt: {system_prompt[:200]}...")
                self.logger.debug(f"User Prompt: {user_prompt[:200]}...")
                
                # 调用模型
                response = await asyncio.to_thread(self.model.invoke, messages)
                processing_time = time.time() - section_start_time
                
                # 打印原始响应
                self.logger.info(f"📥 收到模型响应 (耗时: {processing_time:.2f}s)")
                self.logger.debug(f"原始响应内容 (前500字符): {str(response.content)[:500]}")
                self.logger.debug(f"响应类型: {type(response.content)}")
                
                # 保存AI输出到数据库
                if self.db and task_id:
                    ai_output = AIOutput(
                        task_id=task_id,
                        operation_type="detect_issues",
                        section_title=section_title,
                        section_index=index,
                        input_text=section_content[:4000],
                        raw_output=response.content,
                        processing_time=processing_time,
                        status="success"
                    )
                
                # 解析响应
                try:
                    content = response.content
                    self.logger.info(f"🔍 开始解析章节 '{section_title}' 的响应")
                    
                    if isinstance(content, str):
                        self.logger.debug(f"响应内容长度: {len(content)} 字符")
                        
                        # 查找JSON内容
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            self.logger.debug(f"找到JSON内容 (前200字符): {json_str[:200]}...")
                            
                            try:
                                result = json.loads(json_str)
                                self.logger.info(f"✅ JSON解析成功，包含 {len(result.get('issues', []))} 个问题")
                            except json.JSONDecodeError as je:
                                self.logger.error(f"❌ JSON解析失败: {str(je)}")
                                self.logger.error(f"JSON字符串: {json_str[:500]}...")
                                result = {"issues": []}
                        else:
                            self.logger.warning(f"⚠️ 未找到JSON格式内容")
                            self.logger.debug(f"完整响应: {content[:1000]}...")
                            result = {"issues": []}
                    else:
                        self.logger.warning(f"⚠️ 响应不是字符串类型: {type(content)}")
                        result = {"issues": []}
                    
                    # 更新数据库中的解析结果
                    if self.db and task_id:
                        ai_output.parsed_output = result
                        self.db.add(ai_output)
                        self.db.commit()
                    
                    # 为每个问题添加章节信息
                    issues = result.get('issues', [])
                    for issue in issues:
                        if 'location' in issue and section_title not in issue.get('location', ''):
                            issue['location'] = f"{section_title} - {issue['location']}"
                    
                    self.logger.debug(f"✓ 章节 '{section_title}' 检测完成，发现 {len(issues)} 个问题")
                    return issues
                    
                except Exception as e:
                    import traceback
                    self.logger.error(f"⚠️ 解析章节 '{section_title}' 的响应失败: {str(e)}")
                    self.logger.error(f"错误类型: {type(e).__name__}")
                    self.logger.error(f"完整堆栈:\n{traceback.format_exc()}")
                    
                    # 保存解析错误信息
                    if self.db and task_id:
                        ai_output.status = "parsing_error"
                        ai_output.error_message = str(e)
                        self.db.add(ai_output)
                        self.db.commit()
                    
                    return []
                    
            except Exception as e:
                import traceback
                self.logger.error(f"❌ 检测章节 '{section_title}' 失败: {str(e)}")
                self.logger.error(f"错误类型: {type(e).__name__}")
                self.logger.error(f"完整堆栈:\n{traceback.format_exc()}")
                processing_time = time.time() - section_start_time
                
                # 保存错误信息到数据库
                if self.db and task_id:
                    ai_output = AIOutput(
                        task_id=task_id,
                        operation_type="detect_issues",
                        section_title=section_title,
                        section_index=index,
                        input_text=section_content[:4000],
                        raw_output="",
                        status="failed",
                        error_message=str(e),
                        processing_time=processing_time
                    )
                    self.db.add(ai_output)
                    self.db.commit()
                
                return []
        
        # 批量并发执行所有章节的检测
        self.logger.info(f"🚀 开始并发检测 {len(valid_sections)} 个章节...")
        
        # 创建所有检测任务
        tasks = [
            detect_section_issues(section, index) 
            for index, section in enumerate(valid_sections)
        ]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有检测结果
        all_issues = []
        for result in results:
            if isinstance(result, list):
                all_issues.extend(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"⚠️ 某个章节检测出现异常: {str(result)}")
        
        # 更新进度：完成
        if progress_callback:
            await progress_callback(f"文档检测完成，共发现 {len(all_issues)} 个问题", 100)
        
        self.logger.info(f"✅ 文档检测完成，共发现 {len(all_issues)} 个问题")
        return all_issues
    
    async def call_api(self, prompt: str) -> Dict:
        """通用API调用方法"""
        try:
            messages = [HumanMessage(content=prompt)]
            response = await asyncio.to_thread(self.model.invoke, messages)
            return {"status": "success", "content": response.content}
        except Exception as e:
            # 如果启用了降级策略，可以在这里实现
            if hasattr(self, 'fallback_enabled') and self.fallback_enabled and hasattr(self, 'fallback_provider'):
                self.logger.warning(f"⚠️ 主服务失败，尝试降级到 {self.fallback_provider}")
                # 这里可以实现降级逻辑
            return {"status": "error", "message": str(e)}