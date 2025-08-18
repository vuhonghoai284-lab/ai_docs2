"""AI服务模块 - 使用LangChain调用OpenAI兼容API"""
import json
import os
import re
from typing import List, Dict, Optional, Callable
import yaml
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from prompt_loader import prompt_loader

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

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
    type: str = Field(description="问题类型：语法/逻辑/内容")
    description: str = Field(description="具体问题描述")
    location: str = Field(description="问题所在位置")
    severity: str = Field(description="严重程度：高/中/低")
    suggestion: str = Field(description="改进建议")

class DocumentIssues(BaseModel):
    """文档问题列表"""
    issues: List[DocumentIssue] = Field(description="发现的所有问题", default=[])

class AIService:
    """AI服务封装 - 使用LangChain和OpenAI兼容API"""
    
    def __init__(self):
        # 从环境变量获取API配置
        self.api_key = os.getenv('OPENAI_API_KEY', os.getenv('ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_AUTH_TOKEN', 'dummy-key')))
        self.api_base = os.getenv('OPENAI_API_BASE', os.getenv('ANTHROPIC_BASE_URL', 'https://api.openai.com/v1'))
        self.model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # 如果使用Anthropic兼容接口，设置相应的模型名称
        if 'anthropic' in self.api_base.lower() or 'claude' in self.api_base.lower():
            self.model_name = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        
        print(f"🤖 AI服务配置:")
        print(f"   API Base: {self.api_base}")
        print(f"   Model: {self.model_name}")
        
        try:
            # 初始化ChatOpenAI模型（兼容OpenAI和Anthropic）                
            self.model = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                model=self.model_name,
                temperature=0.3,
                max_tokens=4096
            )
            
            # 初始化解析器
            self.structure_parser = PydanticOutputParser(pydantic_object=DocumentStructure)
            self.issues_parser = PydanticOutputParser(pydantic_object=DocumentIssues)
            print("✅ AI服务初始化成功")
            
        except Exception as e:
            print(f"❌ AI服务初始化失败: {str(e)}")
            raise
    
    async def preprocess_document(self, text: str) -> List[Dict]:
        """预处理文档：章节分割和内容整理 - 通过AI一次性完成"""
        print("📝 开始文档预处理...")
        
        try:
            # 从模板加载提示词
            system_prompt = prompt_loader.get_system_prompt('document_preprocess')
            
            # 构建用户提示
            user_prompt = prompt_loader.get_user_prompt(
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
            
            # 解析响应
            try:
                content = response.content
                # 尝试解析JSON
                if isinstance(content, str):
                    # 查找JSON内容
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                    else:
                        # 如果没有找到JSON，返回原文作为单一章节
                        result = {
                            "sections": [{
                                "section_title": "文档内容",
                                "content": text,
                                "level": 1
                            }]
                        }
                else:
                    result = {"sections": [{"section_title": "文档内容", "content": text, "level": 1}]}
                
                print(f"✅ 文档预处理完成，识别到 {len(result.get('sections', []))} 个章节")
                return result.get('sections', [])
                
            except Exception as e:
                print(f"⚠️ 文档结构解析失败，使用原始文本: {str(e)}")
                return [{"section_title": "文档内容", "content": text, "level": 1}]
                
        except Exception as e:
            print(f"❌ 文档预处理失败: {str(e)}")
            # 返回原始文本作为单一章节
            return [{"section_title": "文档内容", "content": text, "level": 1}]
    
    
    async def detect_issues(self, text: str, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """调用AI检测文档问题 - 使用异步批量处理"""
        
        # 如果文本太短，直接返回空列表
        if len(text) < 50:
            return []
        
        # 更新进度：开始文档预处理
        if progress_callback:
            await progress_callback("正在分析文档结构...", 10)
        
        # 先进行文档预处理
        sections = await self.preprocess_document(text)
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
        
        print(f"📊 准备检测 {len(valid_sections)} 个有效章节")
        
        # 创建异步检测任务
        async def detect_section_issues(section: Dict, index: int) -> List[Dict]:
            """异步检测单个章节的问题"""
            section_title = section.get('section_title', '未知章节')
            section_content = section.get('content', '')
            
            # 更新进度
            progress = 20 + int((index / len(valid_sections)) * 70)
            if progress_callback:
                await progress_callback(f"正在检测章节 {index + 1}/{len(valid_sections)}: {section_title}", progress)
            
            print(f"🔍 [{index + 1}/{len(valid_sections)}] 检测章节: {section_title}")
            
            try:
                # 从模板加载提示词
                system_prompt = prompt_loader.get_system_prompt('document_detect_issues')
                
                # 构建用户提示
                user_prompt = prompt_loader.get_user_prompt(
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
                
                # 调用模型
                response = await asyncio.to_thread(self.model.invoke, messages)
                
                # 解析响应
                try:
                    content = response.content
                    if isinstance(content, str):
                        # 查找JSON内容
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            result = json.loads(json_str)
                        else:
                            result = {"issues": []}
                    else:
                        result = {"issues": []}
                    
                    # 为每个问题添加章节信息
                    issues = result.get('issues', [])
                    for issue in issues:
                        if 'location' in issue and not section_title in issue['location']:
                            issue['location'] = f"{section_title} - {issue['location']}"
                    
                    print(f"✓ 章节 '{section_title}' 检测完成，发现 {len(issues)} 个问题")
                    return issues
                    
                except Exception as e:
                    print(f"⚠️ 解析章节 '{section_title}' 的响应失败: {str(e)}")
                    return []
                    
            except Exception as e:
                print(f"❌ 检测章节 '{section_title}' 失败: {str(e)}")
                return []
        
        # 批量并发执行所有章节的检测
        print(f"🚀 开始并发检测 {len(valid_sections)} 个章节...")
        
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
                print(f"⚠️ 某个章节检测出现异常: {str(result)}")
        
        # 更新进度：完成
        if progress_callback:
            await progress_callback(f"文档检测完成，共发现 {len(all_issues)} 个问题", 100)
        
        print(f"✅ 文档检测完成，共发现 {len(all_issues)} 个问题")
        return all_issues
    
    async def call_api(self, prompt: str) -> Dict:
        """通用API调用方法"""
        try:
            messages = [HumanMessage(content=prompt)]
            response = await asyncio.to_thread(self.model.invoke, messages)
            return {"status": "success", "content": response.content}
        except Exception as e:
            return {"status": "error", "message": str(e)}