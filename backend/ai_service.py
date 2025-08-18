"""AI服务模块 - 使用LangChain调用Claude API"""
import json
import os
from typing import List, Dict, Optional
import yaml
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

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
    issues: List[DocumentIssue] = Field(description="发现的所有问题")

class AIService:
    """AI服务封装 - 使用LangChain和Claude"""
    
    def __init__(self):
        # 从环境变量获取API密钥，如果没有则使用配置文件中的默认值
        self.api_key = os.getenv('ANTHROPIC_API_KEY', config.get('anthropic_api_key', ''))
        self.use_mock = not bool(self.api_key)  # 如果没有API密钥，使用模拟模式
        
        if not self.use_mock:
            try:
                # 初始化Claude模型
                self.model = ChatAnthropic(
                    api_key=self.api_key,
                    model_name="claude-3-haiku-20240307",  # 使用更经济的模型
                    temperature=0.3,
                    max_tokens=4096
                )
                # 初始化JSON解析器
                self.parser = JsonOutputParser(pydantic_object=DocumentIssues)
            except Exception as e:
                print(f"初始化Claude API失败，将使用模拟模式: {str(e)}")
                self.use_mock = True
    
    async def detect_issues(self, text: str) -> List[Dict]:
        """调用AI检测文档问题"""
        
        # 如果文本太短，直接返回空列表
        if len(text) < 50:
            return []
        
        # 如果使用模拟模式
        if self.use_mock:
            return await self._mock_detect_issues(text)
        
        try:
            # 构建系统提示
            system_prompt = """你是一个专业的技术文档审查专家。你的任务是分析文档内容，找出其中的质量问题。

请重点关注以下几个方面：
1. 语法规范性：错别字、标点符号错误、专业术语使用不当
2. 逻辑完整性：章节结构是否清晰、内容是否连贯、是否有逻辑矛盾
3. 内容质量：描述是否清晰、示例是否完整、是否缺少必要信息

请严格按照指定的JSON格式输出结果。如果没有发现问题，返回空的issues数组。"""

            # 构建用户提示
            user_prompt = f"""请分析以下技术文档的质量问题，并按照JSON格式输出：

{self.parser.get_format_instructions()}

文档内容（最多分析前8000字符）：
{text[:8000]}

请仔细分析并输出发现的问题。如果文档质量良好，可以返回空的issues数组。"""

            # 创建消息
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 调用模型
            response = await asyncio.to_thread(self.model.invoke, messages)
            
            # 解析响应
            try:
                # 尝试从响应中提取JSON内容
                content = response.content
                if isinstance(content, str):
                    # 查找JSON内容
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                    else:
                        # 如果没有找到JSON，尝试直接解析
                        result = self.parser.parse(content)
                else:
                    result = self.parser.parse(str(content))
                
                # 转换为字典列表
                if isinstance(result, dict) and 'issues' in result:
                    issues = result['issues']
                elif isinstance(result, DocumentIssues):
                    issues = [issue.dict() for issue in result.issues]
                else:
                    issues = []
                
                return issues
                
            except Exception as e:
                print(f"解析AI响应失败: {str(e)}")
                # 如果解析失败，返回一个基础问题
                return [{
                    "type": "内容",
                    "description": "文档可能存在一些需要改进的地方",
                    "location": "文档整体",
                    "severity": "低",
                    "suggestion": "建议进行人工复查"
                }]
            
        except Exception as e:
            print(f"AI服务调用失败: {str(e)}")
            # 返回模拟数据作为降级方案
            return await self._mock_detect_issues(text)
    
    async def _mock_detect_issues(self, text: str) -> List[Dict]:
        """模拟检测（用于测试或API不可用时）"""
        await asyncio.sleep(1)  # 模拟网络延迟
        
        # 基于文本长度和内容生成模拟问题
        mock_issues = []
        
        # 检查常见问题
        if "测试" in text or "test" in text.lower():
            mock_issues.append({
                "type": "内容",
                "description": "文档中包含测试相关内容，可能需要更新为正式版本",
                "location": "文档中包含'测试'关键词的位置",
                "severity": "中",
                "suggestion": "建议检查并替换测试内容为正式内容"
            })
        
        if len(text) > 1000 and "## " not in text and "# " not in text:
            mock_issues.append({
                "type": "逻辑",
                "description": "文档缺少清晰的章节结构",
                "location": "文档整体",
                "severity": "中",
                "suggestion": "建议添加章节标题，使用Markdown格式组织内容"
            })
        
        if len([line for line in text.split('\n') if len(line) > 200]) > 0:
            mock_issues.append({
                "type": "语法",
                "description": "存在过长的段落，影响阅读体验",
                "location": "超长段落位置",
                "severity": "低",
                "suggestion": "建议将长段落拆分为多个短段落"
            })
        
        # 如果没有发现问题，添加一个通用建议
        if not mock_issues and len(text) > 100:
            mock_issues.append({
                "type": "内容",
                "description": "文档基本符合规范，但可以进一步优化",
                "location": "文档整体",
                "severity": "低",
                "suggestion": "建议增加更多示例和详细说明"
            })
        
        return mock_issues
    
    async def call_api(self, prompt: str) -> Dict:
        """通用API调用方法"""
        if self.use_mock:
            return {"status": "mock", "message": "使用模拟模式"}
        
        try:
            messages = [HumanMessage(content=prompt)]
            response = await asyncio.to_thread(self.model.invoke, messages)
            return {"status": "success", "content": response.content}
        except Exception as e:
            return {"status": "error", "message": str(e)}