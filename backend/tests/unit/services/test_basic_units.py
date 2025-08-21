"""
基础单元测试 - 专注于核心逻辑验证
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_processor import DocumentProcessor
from app.services.issue_detector import IssueDetector


class TestBasicUnits:
    """基础单元测试类"""
    
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
    def mock_db(self):
        """Mock数据库会话"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        return db


class TestDocumentProcessorBasic(TestBasicUnits):
    """DocumentProcessor基础测试"""
    
    def test_validate_sections_normal_case(self, mock_model_config, mock_db):
        """测试章节验证 - 正常情况"""
        with patch('app.services.document_processor.ChatOpenAI'):
            with patch('app.services.document_processor.PydanticOutputParser'):
                processor = DocumentProcessor(mock_model_config, mock_db)
                
                sections = [
                    {
                        "section_title": "有效标题",
                        "content": "这是足够长的有效内容，超过20个字符的测试内容，确保通过验证",
                        "level": 1
                    },
                    {
                        "section_title": "另一标题",
                        "content": "另一个足够长的章节内容用于测试验证功能，这里添加更多字符确保通过验证", 
                        "level": 2
                    }
                ]
                
                result = processor.validate_sections(sections)
                
                assert len(result) == 2
                assert result[0]['section_title'] == '有效标题'
                assert result[1]['section_title'] == '另一标题'
    
    def test_validate_sections_filter_invalid(self, mock_model_config, mock_db):
        """测试章节验证 - 过滤无效章节"""
        with patch('app.services.document_processor.ChatOpenAI'):
            with patch('app.services.document_processor.PydanticOutputParser'):
                processor = DocumentProcessor(mock_model_config, mock_db)
                
                sections = [
                    {
                        "section_title": "有效章节",
                        "content": "这是足够长的有效内容，超过20个字符的测试文本，确保能通过验证",
                        "level": 1
                    },
                    {
                        "section_title": "太短",
                        "content": "短",  # 内容太短
                        "level": 1
                    },
                    "无效类型",  # 非字典
                    {
                        "section_title": "无内容"
                        # 缺少content
                    }
                ]
                
                result = processor.validate_sections(sections)
                
                # 只保留有效章节
                assert len(result) == 1
                assert result[0]['section_title'] == '有效章节'
    
    def test_create_mock_response_structure(self, mock_model_config, mock_db):
        """测试创建Mock响应的结构"""
        with patch('app.services.document_processor.ChatOpenAI'):
            with patch('app.services.document_processor.PydanticOutputParser'):
                processor = DocumentProcessor(mock_model_config, mock_db)
                
                messages = [
                    Mock(content="文档内容: 第一段\n\n第二段\n\n第三段")
                ]
                
                result = processor._create_mock_response(messages)
                
                # 验证响应结构
                assert hasattr(result, 'content')
                response_data = json.loads(result.content)
                assert 'sections' in response_data
                assert len(response_data['sections']) > 0
                
                # 验证每个章节的结构
                for section in response_data['sections']:
                    assert 'section_title' in section
                    assert 'content' in section
                    assert 'level' in section


class TestIssueDetectorBasic(TestBasicUnits):
    """IssueDetector基础测试"""
    
    def test_filter_issues_by_confidence(self, mock_model_config, mock_db):
        """测试根据置信度过滤问题"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                issues = [
                    {"type": "高置信度", "confidence": 0.9},
                    {"type": "中等置信度", "confidence": 0.7},
                    {"type": "低置信度", "confidence": 0.5},
                    {"type": "默认置信度"},  # 无confidence字段，使用默认0.8
                ]
                
                # 使用0.6的阈值
                filtered = detector.filter_issues_by_severity(issues, min_confidence=0.6)
                
                assert len(filtered) == 3
                assert filtered[0]['type'] == '高置信度'
                assert filtered[1]['type'] == '中等置信度'
                assert filtered[2]['type'] == '默认置信度'
    
    def test_categorize_issues_by_severity(self, mock_model_config, mock_db):
        """测试按严重等级分类问题"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                issues = [
                    {"type": "致命问题", "severity": "致命"},
                    {"type": "严重问题", "severity": "严重"},
                    {"type": "一般问题1", "severity": "一般"},
                    {"type": "一般问题2", "severity": "一般"},
                    {"type": "提示问题", "severity": "提示"},
                    {"type": "未知问题", "severity": "未知"},
                    {"type": "无严重度"}
                ]
                
                categorized = detector.categorize_issues(issues)
                
                assert len(categorized['致命']) == 1
                assert len(categorized['严重']) == 1
                assert len(categorized['一般']) == 4  # 2个一般 + 1个未知 + 1个无字段
                assert len(categorized['提示']) == 1
    
    def test_create_mock_response_detect_duplicates(self, mock_model_config, mock_db):
        """测试Mock响应检测重复字词"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                messages = [
                    Mock(content="章节内容: 这是一个的的测试文档")
                ]
                
                result = detector._create_mock_response(messages)
                response_data = json.loads(result.content)
                
                # 验证检测到重复字词
                issues = response_data['issues']
                assert len(issues) > 0
                
                duplicate_issue = next((issue for issue in issues if issue['type'] == '错别字'), None)
                assert duplicate_issue is not None
                assert '的的' in duplicate_issue['description']
    
    def test_create_mock_response_detect_long_sentence(self, mock_model_config, mock_db):
        """测试Mock响应检测长句"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                long_sentence = "这是一个非常长的句子" + "，内容很多" * 20 + "。"
                messages = [
                    Mock(content=f"章节内容: {long_sentence}")
                ]
                
                result = detector._create_mock_response(messages)
                response_data = json.loads(result.content)
                
                # 验证检测到长句
                issues = response_data['issues']
                long_sentence_issue = next((issue for issue in issues if issue['type'] == '句子过长'), None)
                assert long_sentence_issue is not None
                assert '建议拆分' in long_sentence_issue['description']
    
    def test_create_mock_response_default_issue(self, mock_model_config, mock_db):
        """测试Mock响应生成默认问题"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                messages = [
                    Mock(content="章节内容: 正常的文档内容，没有明显问题")
                ]
                
                result = detector._create_mock_response(messages)
                response_data = json.loads(result.content)
                
                # 验证至少有一个默认问题
                issues = response_data['issues']
                assert len(issues) >= 1
                
                # 验证问题结构
                for issue in issues:
                    assert 'type' in issue
                    assert 'description' in issue
                    assert 'location' in issue
                    assert 'severity' in issue
                    assert 'confidence' in issue


class TestExceptionHandling(TestBasicUnits):
    """异常处理测试"""
    
    def test_document_processor_init_failure(self, mock_model_config, mock_db):
        """测试DocumentProcessor初始化失败"""
        with patch('app.services.document_processor.ChatOpenAI', side_effect=Exception("初始化失败")):
            with pytest.raises(Exception, match="初始化失败"):
                DocumentProcessor(mock_model_config, mock_db)
    
    def test_issue_detector_init_failure(self, mock_model_config, mock_db):
        """测试IssueDetector初始化失败"""
        with patch('app.services.issue_detector.ChatOpenAI', side_effect=Exception("初始化失败")):
            with pytest.raises(Exception, match="初始化失败"):
                IssueDetector(mock_model_config, mock_db)
    
    def test_issue_filter_edge_cases(self, mock_model_config, mock_db):
        """测试问题过滤边界情况"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                edge_cases = [
                    {},  # 空字典
                    {"type": "问题", "confidence": "not_number"},  # 非数字置信度
                    {"type": "问题", "confidence": -0.5},  # 负数
                    {"type": "问题", "confidence": 1.5},  # 超出范围
                ]
                
                # 不应抛出异常
                result = detector.filter_issues_by_severity(edge_cases, min_confidence=0.5)
                assert isinstance(result, list)
    
    def test_issue_categorize_edge_cases(self, mock_model_config, mock_db):
        """测试问题分类边界情况"""
        with patch('app.services.issue_detector.ChatOpenAI'):
            with patch('app.services.issue_detector.PydanticOutputParser'):
                detector = IssueDetector(mock_model_config, mock_db)
                
                edge_cases = [
                    {},  # 空字典
                    {"type": "问题", "severity": None},  # None
                    {"type": "问题", "severity": ""},  # 空字符串
                    {"type": "问题", "severity": 123},  # 非字符串
                    {"type": "问题", "severity": "未知等级"},  # 未定义等级
                ]
                
                # 不应抛出异常
                result = detector.categorize_issues(edge_cases)
                assert isinstance(result, dict)
                assert all(key in result for key in ['致命', '严重', '一般', '提示'])