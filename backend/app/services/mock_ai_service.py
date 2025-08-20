"""
模拟AI服务 - 用于测试模式（增强版）
"""
import json
import random
import asyncio
from typing import Dict, Any
from datetime import datetime
import hashlib


class MockAIService:
    """模拟AI服务，返回测试数据"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.response_delay = config.get('response_delay', 0.5)
        self.total_time = config.get('total_time', None)
        self.enable_detailed_logs = config.get('enable_detailed_logs', False)
        self.model_name = config.get('model', 'mock-model')
        self.task_id = None  # 将由处理器设置
        self.manager = None  # WebSocket管理器，将由处理器设置
        
    async def set_context(self, task_id: int, manager=None):
        """设置上下文信息"""
        self.task_id = task_id
        self.manager = manager
        
    async def _send_log(self, message: str, stage: str = None, progress: int = None):
        """发送实时日志"""
        if self.manager and self.task_id:
            await self.manager.send_log(
                self.task_id, 
                "INFO", 
                f"[{self.model_name}] {message}",
                stage,
                progress
            )
    
    async def analyze_document(self, text: str, prompt_type: str = "detect_issues") -> Dict[str, Any]:
        """模拟文档分析（带详细日志）"""
        
        # 调试信息
        print(f"[DEBUG] MockAI analyze_document: model={self.model_name}, "
              f"total_time={self.total_time}, enable_detailed_logs={self.enable_detailed_logs}, "
              f"prompt_type={prompt_type}")
        
        # 根据文本生成确定性的seed
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        random.seed(seed)
        
        if prompt_type == "preprocess":
            return await self._generate_preprocessing_result_with_logs(text)
        else:
            return await self._generate_issues_result_with_logs(text)
    
    async def _generate_preprocessing_result_with_logs(self, text: str) -> Dict[str, Any]:
        """生成预处理结果（带日志）"""
        
        print(f"[DEBUG] _generate_preprocessing_result_with_logs: total_time={self.total_time}, "
              f"enable_detailed_logs={self.enable_detailed_logs}, manager={self.manager}")
        
        # 慢速模式下的分阶段处理
        if self.total_time and self.total_time > 10 and self.enable_detailed_logs:
            # 预处理占总时间的40%
            preprocess_time = self.total_time * 0.4
            steps = [
                ("分析文档结构...", 0.25),
                ("提取章节信息...", 0.25),
                ("识别关键内容...", 0.25),
                ("生成元数据...", 0.25)
            ]
            
            for i, (step_msg, step_ratio) in enumerate(steps):
                progress = 30 + int(20 * (i / len(steps)))
                print(f"[DEBUG] Sending log: {step_msg}, progress={progress}")
                await self._send_log(step_msg, "文档预处理", progress)
                await asyncio.sleep(preprocess_time * step_ratio)
        else:
            # 快速模式
            print(f"[DEBUG] Fast mode, sleeping {self.response_delay}s")
            await asyncio.sleep(self.response_delay)
        
        # 生成预处理结果
        lines = text.split('\n')
        sections = []
        current_section = []
        section_count = 0
        
        for line in lines:
            if line.strip() and (line.strip().startswith('#') or 
                                line.strip().startswith('第') or
                                '章' in line or '节' in line):
                if current_section:
                    section_count += 1
                    sections.append({
                        "title": f"第{section_count}节",
                        "content": '\n'.join(current_section[:100])
                    })
                    current_section = []
                current_section.append(line)
            elif line.strip():
                current_section.append(line)
        
        if current_section:
            section_count += 1
            sections.append({
                "title": f"第{section_count}节",
                "content": '\n'.join(current_section[:100])
            })
        
        if not sections:
            sections = [{
                "title": "文档内容",
                "content": text[:500]
            }]
        
        await self._send_log(f"识别到{len(sections)}个章节", "文档预处理")
        
        result = {
            "document_type": "技术文档",
            "structure": {
                "total_sections": len(sections),
                "sections": sections[:5]
            },
            "metadata": {
                "total_chars": len(text),
                "estimated_reading_time": max(1, len(text) // 500),
                "language": "中文",
                "technical_level": random.choice(["初级", "中级", "高级"])
            }
        }
        
        return {
            "status": "success",
            "data": result,
            "raw_output": json.dumps(result, ensure_ascii=False, indent=2),
            "tokens_used": random.randint(100, 500),
            "processing_time": self.response_delay
        }
    
    async def _generate_issues_result_with_logs(self, text: str) -> Dict[str, Any]:
        """生成问题检测结果（带详细日志）"""
        
        # 慢速模式下的分阶段处理
        if self.total_time and self.total_time > 10 and self.enable_detailed_logs:
            # 问题检测占总时间的60%
            detect_time = self.total_time * 0.6
            steps = [
                ("开始语法检查...", 0.15, "语法分析"),
                ("检查标点符号使用...", 0.1, "语法分析"),
                ("检查句子结构...", 0.1, "语法分析"),
                ("开始逻辑分析...", 0.15, "逻辑分析"),
                ("验证因果关系...", 0.1, "逻辑分析"),
                ("检查论述连贯性...", 0.1, "逻辑分析"),
                ("开始完整性检查...", 0.15, "完整性分析"),
                ("检查必要元素...", 0.1, "完整性分析"),
                ("生成改进建议...", 0.05, "生成建议")
            ]
            
            for i, (step_msg, step_ratio, stage) in enumerate(steps):
                progress = 60 + int(20 * (i / len(steps)))
                await self._send_log(step_msg, stage, progress)
                await asyncio.sleep(detect_time * step_ratio)
                
                # 模拟发现问题
                if random.random() < 0.3:
                    issue_type = random.choice(["语法错误", "逻辑问题", "完整性问题"])
                    await self._send_log(f"发现{issue_type}", stage)
        else:
            # 快速模式
            await asyncio.sleep(self.response_delay)
            await self._send_log("快速分析中...", "问题检测")
        
        issues = []
        num_issues = random.randint(3, 8)
        
        issue_templates = [
            {
                "type": "语法错误",
                "descriptions": [
                    "句子结构不完整，缺少主语",
                    "标点符号使用不当",
                    "中英文混用格式不统一",
                    "括号未正确闭合",
                    "引号使用不规范"
                ],
                "severities": ["一般", "提示"],
                "suggestions": [
                    "建议补充完整的句子结构",
                    "请检查并修正标点符号",
                    "统一使用中文或英文标点",
                    "请确保括号正确配对",
                    "使用规范的引号格式"
                ]
            },
            {
                "type": "逻辑问题",
                "descriptions": [
                    "前后描述存在矛盾",
                    "因果关系不明确",
                    "论述缺乏支撑依据",
                    "概念定义不清晰",
                    "步骤顺序有误"
                ],
                "severities": ["严重", "致命"],
                "suggestions": [
                    "请核实并统一前后描述",
                    "明确说明因果关系",
                    "补充必要的论据或引用",
                    "给出清晰的概念定义",
                    "调整为正确的操作顺序"
                ]
            },
            {
                "type": "完整性",
                "descriptions": [
                    "缺少必要的背景介绍",
                    "示例代码不完整",
                    "缺少结论或总结",
                    "参考资料未列出",
                    "图表说明缺失"
                ],
                "severities": ["一般", "严重"],
                "suggestions": [
                    "补充相关背景信息",
                    "提供完整的示例代码",
                    "添加适当的总结内容",
                    "列出参考文献或资料来源",
                    "为图表添加说明文字"
                ]
            }
        ]
        
        text_lines = text.split('\n')
        for i in range(num_issues):
            template = random.choice(issue_templates)
            issue_idx = random.randint(0, len(template["descriptions"]) - 1)
            
            if text_lines:
                line_num = random.randint(1, min(len(text_lines), 100))
                location = f"第{line_num}行"
                if line_num <= len(text_lines):
                    original_text = text_lines[line_num - 1][:100]
                else:
                    original_text = "（文本内容）"
            else:
                location = "文档开头"
                original_text = text[:100] if text else "（空文档）"
            
            issue = {
                "issue_type": template["type"],
                "description": template["descriptions"][issue_idx],
                "location": location,
                "severity": random.choice(template["severities"]),
                "confidence": round(random.uniform(0.7, 0.95), 2),
                "suggestion": template["suggestions"][issue_idx],
                "original_text": original_text,
                "user_impact": f"可能影响读者理解，建议优先级：{'高' if template['severities'][0] in ['致命', '严重'] else '中'}",
                "reasoning": f"基于文档分析，发现此处{template['type']}，需要修正以提高文档质量",
                "context": f"上下文：{original_text[:50]}..."
            }
            issues.append(issue)
        
        # 统计问题
        severity_count = {
            "致命": sum(1 for i in issues if i["severity"] == "致命"),
            "严重": sum(1 for i in issues if i["severity"] == "严重"),
            "一般": sum(1 for i in issues if i["severity"] == "一般"),
            "提示": sum(1 for i in issues if i["severity"] == "提示")
        }
        
        await self._send_log(
            f"检测完成：发现{len(issues)}个问题（致命:{severity_count['致命']}, 严重:{severity_count['严重']}, 一般:{severity_count['一般']}, 提示:{severity_count['提示']}）",
            "问题检测"
        )
        
        result = {
            "status": "success",
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "critical": severity_count["致命"],
                "major": severity_count["严重"],
                "normal": severity_count["一般"],
                "minor": severity_count["提示"]
            }
        }
        
        return {
            "status": "success",
            "data": result,
            "raw_output": json.dumps(result, ensure_ascii=False, indent=2),
            "tokens_used": random.randint(500, 1500),
            "processing_time": self.response_delay
        }
    
    async def process_with_thinking(self, text: str, prompt_type: str = "detect_issues") -> Dict[str, Any]:
        """带有思考过程的处理（模拟）"""
        thinking_steps = [
            "正在分析文档结构...",
            "识别关键章节和内容...",
            "检查语法和格式问题...",
            "验证逻辑一致性...",
            "评估内容完整性...",
            "生成改进建议..."
        ]
        
        # 慢速模式下逐步输出思考过程
        if self.enable_detailed_logs:
            for step in thinking_steps:
                await self._send_log(f"思考: {step}", "AI思考")
                await asyncio.sleep(0.5)
        
        result = {
            "thinking": "\n".join(thinking_steps),
            "response": await self.analyze_document(text, prompt_type)
        }
        
        return result