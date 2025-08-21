"""
DocumentProcessor单元测试
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_processor import DocumentProcessor
from tests.fixtures.mock_helpers import create_mock_dependencies


class TestDocumentProcessor:
    """文档处理器单元测试"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        return db
    
    @pytest.fixture
    def mock_model_config(self):
        """Mock模型配置"""
        return {
            'provider': 'openai',
            'config': {
                'api_key': 'test-api-key',
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-4o-mini',
                'temperature': 0.3,
                'max_tokens': 4000,
                'timeout': 60,
                'max_retries': 3
            }
        }
    
    @pytest.fixture
    def document_processor(self, mock_model_config, mock_db):
        """创建DocumentProcessor实例"""
        with patch('app.services.document_processor.ChatOpenAI'):
            with patch('app.services.document_processor.PydanticOutputParser'):
                processor = DocumentProcessor(mock_model_config, mock_db)
                return processor
    
    @pytest.mark.asyncio
    async def test_preprocess_document_normal_flow(self, document_processor, mock_db):
        """测试正常文档预处理流程"""
        # 准备测试数据
        test_text = "# 测试标题\n\n这是测试内容。\n\n## 子标题\n\n更多内容。"
        task_id = 1
        
        # Mock AI响应
        mock_response = {
            "sections": [
                {
                    "section_title": "测试标题",
                    "content": "这是测试内容。",
                    "level": 1
                },
                {
                    "section_title": "子标题", 
                    "content": "更多内容。",
                    "level": 2
                }
            ]
        }
        
        # Mock _call_ai_model 方法
        with patch.object(document_processor, '_call_ai_model') as mock_call:
            mock_call.return_value = Mock(content=json.dumps(mock_response, ensure_ascii=False))
            
            # 执行测试
            result = await document_processor.preprocess_document(test_text, task_id)
            
            # 验证结果
            assert len(result) == 2
            assert result[0]['section_title'] == '测试标题'
            assert result[1]['section_title'] == '子标题'
            
            # 验证AI模型被调用
            mock_call.assert_called_once()
            
            # 验证数据库操作
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_preprocess_document_with_progress_callback(self, document_processor):
        """测试带进度回调的文档预处理"""
        # 准备测试数据
        test_text = "简短测试内容"
        progress_calls = []
        
        async def mock_progress_callback(message, progress):
            progress_calls.append((message, progress))
        
        # Mock AI响应
        mock_response = {
            "sections": [
                {"section_title": "文档内容", "content": test_text, "level": 1}
            ]
        }
        
        with patch.object(document_processor, '_call_ai_model') as mock_call:
            mock_call.return_value = Mock(content=json.dumps(mock_response))
            
            # 执行测试
            result = await document_processor.preprocess_document(
                test_text, 
                progress_callback=mock_progress_callback
            )
            
            # 验证结果
            assert len(result) == 1
            
            # 验证进度回调被调用
            assert len(progress_calls) >= 3
            assert any("开始分析文档结构" in call[0] for call in progress_calls)
            assert any("正在调用AI模型" in call[0] for call in progress_calls)
    
    @pytest.mark.asyncio
    async def test_preprocess_document_ai_failure(self, document_processor, mock_db):
        """测试AI服务调用失败"""
        test_text = "测试内容"
        task_id = 1
        
        # Mock AI调用失败
        with patch.object(document_processor, '_call_ai_model') as mock_call:
            mock_call.side_effect = Exception("AI服务不可用")
            
            # 执行测试
            result = await document_processor.preprocess_document(test_text, task_id)
            
            # 验证返回默认章节
            assert len(result) == 1
            assert result[0]['section_title'] == '文档内容'
            assert result[0]['content'] == test_text
            
            # 验证错误记录到数据库
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_preprocess_document_invalid_json_response(self, document_processor, mock_db):
        """测试AI返回无效JSON格式"""
        test_text = "测试内容"
        task_id = 1
        
        # Mock AI返回无效JSON
        with patch.object(document_processor, '_call_ai_model') as mock_call:
            mock_call.return_value = Mock(content="这是无效的JSON响应")
            
            # 执行测试
            result = await document_processor.preprocess_document(test_text, task_id)
            
            # 验证返回默认章节
            assert len(result) == 1
            assert result[0]['section_title'] == '文档内容'
            assert result[0]['content'] == test_text
    
    @pytest.mark.asyncio
    async def test_preprocess_document_partial_json_response(self, document_processor):
        """测试AI返回部分有效的JSON响应"""
        test_text = "测试内容"
        
        # Mock AI返回包含JSON的文本响应
        response_content = '''
        这是一些前置文本
        {"sections": [{"section_title": "提取的标题", "content": "提取的内容", "level": 1}]}
        这是一些后置文本
        '''
        
        with patch.object(document_processor, '_call_ai_model') as mock_call:
            mock_call.return_value = Mock(content=response_content)
            
            # 执行测试
            result = await document_processor.preprocess_document(test_text)
            
            # 验证能正确提取JSON部分
            assert len(result) == 1
            assert result[0]['section_title'] == '提取的标题'
            assert result[0]['content'] == '提取的内容'
    
    def test_validate_sections_normal(self, document_processor):
        """测试章节验证 - 正常情况"""
        sections = [
            {
                "section_title": "标题1",
                "content": "这是足够长的内容，超过20个字符的测试内容",
                "level": 1
            },
            {
                "section_title": "标题2", 
                "content": "另一个足够长的章节内容，用于测试验证功能",
                "level": 2
            }
        ]
        
        result = document_processor.validate_sections(sections)
        
        # 验证所有有效章节都保留
        assert len(result) == 2
        assert result[0]['section_title'] == '标题1'
        assert result[1]['section_title'] == '标题2'
    
    def test_validate_sections_filter_invalid(self, document_processor):
        """测试章节验证 - 过滤无效章节"""
        sections = [
            {
                "section_title": "有效章节",
                "content": "这是足够长的有效内容，超过20个字符的测试内容",
                "level": 1
            },
            {
                "section_title": "太短章节",
                "content": "短",  # 内容太短
                "level": 1
            },
            "无效类型",  # 非字典类型
            {
                "section_title": "无内容章节",
                # 缺少content字段
                "level": 1
            },
            {
                # 缺少section_title，但有有效内容
                "content": "这个章节没有标题但内容足够长，应该被保留并设置默认标题",
                "level": 1
            }
        ]
        
        result = document_processor.validate_sections(sections)
        
        # 验证只保留有效章节
        assert len(result) == 2
        assert result[0]['section_title'] == '有效章节'
        assert result[1]['section_title'] == '未命名章节'  # 默认标题
    
    @pytest.mark.asyncio
    async def test_call_ai_model_mock_mode(self, document_processor):
        """测试Mock模式下的AI调用"""
        messages = [Mock(content="测试消息")]
        
        # Mock settings返回Mock模式
        with patch('app.services.document_processor.get_settings') as mock_settings:
            mock_settings_instance = Mock()
            mock_settings_instance.is_service_mocked.return_value = True
            mock_settings_instance.get_mock_config.return_value = {'mock_delay': 0.1}
            mock_settings.return_value = mock_settings_instance
            
            # Mock _create_mock_response
            with patch.object(document_processor, '_create_mock_response') as mock_create:
                mock_response = Mock(content='{"sections": []}')
                mock_create.return_value = mock_response
                
                # 执行测试
                result = await document_processor._call_ai_model(messages)
                
                # 验证返回Mock响应
                assert result == mock_response
                mock_create.assert_called_once_with(messages)
    
    @pytest.mark.asyncio
    async def test_call_ai_model_production_mode(self, document_processor):
        """测试生产模式下的AI调用"""
        messages = [Mock(content="测试消息")]
        
        # Mock settings返回非Mock模式
        with patch('app.services.document_processor.get_settings') as mock_settings:
            mock_settings_instance = Mock()
            mock_settings_instance.is_service_mocked.return_value = False
            mock_settings.return_value = mock_settings_instance
            
            # Mock asyncio.to_thread
            mock_response = Mock(content='{"sections": []}')
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_to_thread.return_value = mock_response
                
                # 执行测试
                result = await document_processor._call_ai_model(messages)
                
                # 验证调用真实AI模型
                assert result == mock_response
                mock_to_thread.assert_called_once()
    
    def test_create_mock_response_with_content(self, document_processor):
        """测试创建Mock响应 - 包含文档内容"""
        messages = [
            Mock(content="其他内容"),
            Mock(content="文档内容: 第一段内容\n\n第二段内容\n\n第三段内容")
        ]
        
        result = document_processor._create_mock_response(messages)
        
        # 验证响应格式
        assert hasattr(result, 'content')
        
        # 解析响应内容
        response_data = json.loads(result.content)
        assert 'sections' in response_data
        
        sections = response_data['sections']
        assert len(sections) > 0
        
        # 验证章节结构
        for section in sections:
            assert 'section_title' in section
            assert 'content' in section
            assert 'level' in section
    
    def test_create_mock_response_without_content(self, document_processor):
        """测试创建Mock响应 - 无文档内容"""
        messages = [Mock(content="没有文档内容的消息")]
        
        result = document_processor._create_mock_response(messages)
        
        # 验证响应格式
        assert hasattr(result, 'content')
        
        # 解析响应内容
        response_data = json.loads(result.content)
        assert 'sections' in response_data
        
        sections = response_data['sections']
        assert len(sections) == 1
        assert sections[0]['section_title'] == '文档内容'
        assert sections[0]['content'] == '模拟文档内容'