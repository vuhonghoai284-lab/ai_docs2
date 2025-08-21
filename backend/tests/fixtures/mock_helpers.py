"""
Mock工具和测试辅助类
"""
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Optional


class MockAIService:
    """AI服务Mock类"""
    
    def __init__(self, response_data: Optional[Dict[str, Any]] = None):
        self.response_data = response_data or {
            "issues": [
                {
                    "id": 1,
                    "type": "grammar",
                    "description": "语法问题测试",
                    "location": "第1行",
                    "severity": "medium",
                    "confidence": 0.85,
                    "suggestion": "修改建议",
                    "original_text": "原始文本",
                    "user_impact": "用户影响",
                    "reasoning": "检测原因",
                    "context": "上下文"
                }
            ],
            "summary": {
                "total_issues": 1,
                "grammar_count": 1,
                "logic_count": 0,
                "completeness_count": 0
            }
        }
        self.call_count = 0
        self.last_input = None
        self.should_fail = False
        self.fail_count = 0
        
    async def analyze_document(self, content: str, **kwargs) -> Dict[str, Any]:
        """模拟文档分析"""
        self.call_count += 1
        self.last_input = content
        
        # 模拟处理延迟
        await asyncio.sleep(0.01)
        
        # 模拟失败情况
        if self.should_fail:
            if self.fail_count > 0:
                self.fail_count -= 1
                raise Exception("AI服务暂时不可用")
        
        return self.response_data.copy()
    
    def set_response(self, response_data: Dict[str, Any]):
        """设置Mock响应数据"""
        self.response_data = response_data
        
    def set_failure(self, should_fail: bool = True, fail_count: int = 1):
        """设置是否失败"""
        self.should_fail = should_fail
        self.fail_count = fail_count
        
    def reset(self):
        """重置状态"""
        self.call_count = 0
        self.last_input = None
        self.should_fail = False
        self.fail_count = 0


class MockTaskRepository:
    """任务仓储Mock类"""
    
    def __init__(self):
        self.tasks = {}
        self.next_id = 1
        # 创建Mock方法
        self.get = Mock()
        self.get_by_id = Mock()
        self.update = Mock()
        self.create = Mock()
        self.delete = Mock()
        
    def _get_task(self, task_id: int):
        """内部获取任务方法"""
        return self.tasks.get(task_id)
        
    def _update_task(self, task_id: int, **kwargs):
        """内部更新任务方法"""
        if task_id in self.tasks:
            for key, value in kwargs.items():
                setattr(self.tasks[task_id], key, value)
            return self.tasks[task_id]
        return None
        
    def create_mock_task(self, task_id: int = None, **kwargs):
        """创建Mock任务对象"""
        if task_id is None:
            task_id = self.next_id
            self.next_id += 1
            
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.title = kwargs.get('title', '测试任务')
        mock_task.status = kwargs.get('status', 'pending')
        mock_task.progress = kwargs.get('progress', 0)
        mock_task.user_id = kwargs.get('user_id', 1)
        mock_task.model_id = kwargs.get('model_id', 1)
        mock_task.file_name = kwargs.get('file_name', 'test.md')
        mock_task.created_at = kwargs.get('created_at', None)
        
        self.tasks[task_id] = mock_task
        return mock_task


class MockFileRepository:
    """文件仓储Mock类"""
    
    def __init__(self):
        self.files = {}
        # 创建Mock方法
        self.get_by_task_id = Mock()
        self.create = Mock()
        self.update = Mock()
        self.delete = Mock()
        
    def _get_file_by_task_id(self, task_id: int):
        """内部根据任务ID获取文件信息方法"""
        return self.files.get(task_id)
        
    def create_mock_file(self, task_id: int, **kwargs):
        """创建Mock文件对象"""
        mock_file = Mock()
        mock_file.id = kwargs.get('id', 1)
        mock_file.task_id = task_id
        mock_file.original_name = kwargs.get('original_name', 'test.md')
        mock_file.file_path = kwargs.get('file_path', '/uploads/test.md')
        mock_file.file_size = kwargs.get('file_size', 1024)
        mock_file.content_type = kwargs.get('content_type', 'text/markdown')
        
        self.files[task_id] = mock_file
        return mock_file


class MockIssueRepository:
    """问题仓储Mock类"""
    
    def __init__(self):
        self.issues = []
        self.next_id = 1
        # 创建Mock方法
        self.create_from_analysis = Mock()
        self.get_by_task_id = Mock()
        self.update = Mock()
        self.delete = Mock()
        
    def _create_from_analysis(self, task_id: int, analysis_result: Dict[str, Any]):
        """从分析结果创建问题"""
        created_issues = []
        
        for issue_data in analysis_result.get('issues', []):
            mock_issue = Mock()
            mock_issue.id = self.next_id
            mock_issue.task_id = task_id
            mock_issue.issue_type = issue_data.get('type', 'unknown')
            mock_issue.description = issue_data.get('description', '')
            mock_issue.location = issue_data.get('location', '')
            mock_issue.severity = issue_data.get('severity', 'low')
            mock_issue.confidence = issue_data.get('confidence', 0.5)
            mock_issue.suggestion = issue_data.get('suggestion', '')
            mock_issue.original_text = issue_data.get('original_text', '')
            mock_issue.user_impact = issue_data.get('user_impact', '')
            mock_issue.reasoning = issue_data.get('reasoning', '')
            mock_issue.context = issue_data.get('context', '')
            
            self.issues.append(mock_issue)
            created_issues.append(mock_issue)
            self.next_id += 1
            
        return created_issues


class MockAIOutputRepository:
    """AI输出仓储Mock类"""
    
    def __init__(self):
        self.outputs = []
        self.next_id = 1
        # 创建Mock方法
        self.create_output = Mock()
        self.get_by_task_id = Mock()
        self.update = Mock()
        self.delete = Mock()
        
    def _create_output(self, task_id: int, operation_type: str, input_data: str, output_data: Dict[str, Any]):
        """创建AI输出记录"""
        mock_output = Mock()
        mock_output.id = self.next_id
        mock_output.task_id = task_id
        mock_output.operation_type = operation_type
        mock_output.input_data = input_data
        mock_output.output_data = output_data
        mock_output.created_at = None
        
        self.outputs.append(mock_output)
        self.next_id += 1
        return mock_output


class MockWebSocketManager:
    """WebSocket管理器Mock类"""
    
    def __init__(self):
        self.sent_messages = []
        
    async def send_status(self, task_id: int, status: str, **kwargs):
        """发送状态更新"""
        message = {
            'task_id': task_id,
            'status': status,
            **kwargs
        }
        self.sent_messages.append(message)
        
    async def send_progress(self, task_id: int, progress: int, message: str = ""):
        """发送进度更新"""
        await self.send_status(task_id, "processing", progress=progress, message=message)
        
    def reset(self):
        """重置消息记录"""
        self.sent_messages = []


def create_mock_dependencies():
    """创建所有Mock依赖"""
    mocks = {
        'task_repo': MockTaskRepository(),
        'file_repo': MockFileRepository(),
        'issue_repo': MockIssueRepository(),
        'ai_output_repo': MockAIOutputRepository(),
        'websocket_manager': MockWebSocketManager(),
        'ai_service': MockAIService(),
        'ai_service_factory': Mock(),
        'model_repo': Mock()
    }
    
    # 配置AI服务工厂
    mocks['ai_service_factory'].get_service.return_value = mocks['ai_service']
    
    # 配置模型仓储
    mock_model = Mock()
    mock_model.id = 1
    mock_model.model_key = "gpt-4o-mini"
    mock_model.label = "GPT-4o Mini"
    mocks['model_repo'].get_by_id.return_value = mock_model
    
    return mocks