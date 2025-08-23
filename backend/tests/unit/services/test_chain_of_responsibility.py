"""
测试责任链重构实现
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.services.interfaces.task_processor import TaskProcessingStep, ProcessingResult
from app.services.interfaces.ai_service import IAIServiceProvider
from app.services.ai_service_providers.mock_ai_service_provider import MockAIServiceProvider
from app.services.ai_service_providers.service_provider_factory import ai_service_provider_factory
from app.services.processing_chain import TaskProcessingChain
from app.services.file_parsers.parser_factory import FileParserFactory


class TestChainOfResponsibility:
    """责任链模式测试"""

    @pytest.mark.asyncio
    async def test_mock_service_provider_creation(self):
        """测试Mock服务提供者创建"""
        config = {
            'model': 'test-model',
            'provider': 'mock',
            'response_delay': 0.1
        }
        
        provider = MockAIServiceProvider(config)
        
        assert provider is not None
        assert provider.is_available() is True
        assert provider.get_provider_name() == "MockAI (test-model)"
        
        # 测试获取处理器
        doc_processor = provider.get_document_processor()
        issue_detector = provider.get_issue_detector()
        
        assert doc_processor is not None
        assert issue_detector is not None

    @pytest.mark.asyncio
    async def test_file_parser_factory(self):
        """测试文件解析器工厂"""
        factory = FileParserFactory()
        
        # 测试支持的扩展名
        extensions = factory.get_supported_extensions()
        assert isinstance(extensions, list)
        assert len(extensions) > 0
        
        # 测试获取不同类型的解析器
        pdf_parser = await factory.get_parser("test.pdf")
        docx_parser = await factory.get_parser("test.docx")
        md_parser = await factory.get_parser("test.md")
        txt_parser = await factory.get_parser("test.txt")
        unknown_parser = await factory.get_parser("test.unknown")
        
        assert pdf_parser is not None
        assert docx_parser is not None
        assert md_parser is not None
        assert txt_parser is not None
        assert unknown_parser is None  # 不支持的格式

    @pytest.mark.asyncio
    async def test_processing_chain_execution(self):
        """测试处理链执行"""
        # 创建Mock服务提供者
        config = {'model': 'test-chain', 'response_delay': 0.01}
        provider = MockAIServiceProvider(config)
        
        # 创建处理链
        chain = TaskProcessingChain(provider)
        
        # 准备测试上下文
        context = {
            'task_id': 9999,
            'test_mode': True,
            'file_name': '测试文档.md'
        }
        
        # 进度回调
        progress_calls = []
        async def progress_callback(message: str, progress: int):
            progress_calls.append((message, progress))
        
        # 执行处理链
        result = await chain.execute(context, progress_callback)
        
        # 验证结果
        if not result.success:
            print(f"Chain execution failed: {result.error}")
        assert result.success is True
        assert 'file_parsing_result' in context
        assert 'document_processing_result' in context
        assert 'issue_detection_result' in context
        
        # 验证进度回调被调用
        assert len(progress_calls) > 0
        
        # 验证各阶段结果
        assert isinstance(context['file_parsing_result'], str)
        assert len(context['file_parsing_result']) > 0
        
        assert isinstance(context['document_processing_result'], list)
        assert len(context['document_processing_result']) > 0
        
        assert isinstance(context['issue_detection_result'], list)
        # Mock服务应该能检测到一些问题

    @pytest.mark.asyncio
    async def test_processing_chain_with_real_file(self):
        """测试处理链处理真实文件"""
        # 创建测试文件内容
        import tempfile
        import os
        
        test_content = """# 测试文档
        
## 第一章 简介
这是一个测试文档，用于验证文档处理功能。

### 1.1 背景
在系统开发过程中，文档质量很重要。

### 1.2 目标
本文档的的目标是测试AI分析功能。  # 故意加入错别字"的的"

## 第二章 功能
系统提供以下功能：
1. 文档上传
2. AI分析
3. 报告生成
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # 创建Mock服务提供者
            config = {'model': 'test-real-file', 'response_delay': 0.01}
            provider = MockAIServiceProvider(config)
            
            # 创建处理链
            chain = TaskProcessingChain(provider)
            
            # 准备上下文，使用真实文件路径
            context = {
                'task_id': 9998,
                'test_mode': False,  # 使用真实文件模式
                'file_path': temp_file_path,
                'file_name': 'test_real.md'
            }
            
            # 执行处理链
            result = await chain.execute(context)
            
            # 验证结果
            assert result.success is True
            assert 'file_parsing_result' in context
            assert context['file_parsing_result'] == test_content
            
            # 验证文档处理结果
            assert 'document_processing_result' in context
            sections = context['document_processing_result']
            assert isinstance(sections, list)
            assert len(sections) > 0
            
            # 验证问题检测结果
            assert 'issue_detection_result' in context
            issues = context['issue_detection_result']
            assert isinstance(issues, list)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_processing_chain_error_handling(self):
        """测试处理链错误处理"""
        config = {'model': 'test-error', 'response_delay': 0.01}
        provider = MockAIServiceProvider(config)
        
        chain = TaskProcessingChain(provider)
        
        # 测试不存在文件的情况
        context = {
            'task_id': 9997,
            'test_mode': False,
            'file_path': '/non/existent/file.txt',
            'file_name': 'non_existent.txt'
        }
        
        result = await chain.execute(context)
        
        # 应该失败，因为文件不存在且非测试模式
        assert result.success is False
        assert "文件不存在" in result.error

    @pytest.mark.asyncio
    async def test_individual_processors(self):
        """测试单个处理器"""
        from app.services.processors.file_parsing_processor import FileParsingProcessor
        from app.services.processors.document_processing_processor import DocumentProcessingProcessor
        from app.services.processors.issue_detection_processor import IssueDetectionProcessor
        
        # 创建Mock服务提供者
        config = {'model': 'test-individual', 'response_delay': 0.01}
        provider = MockAIServiceProvider(config)
        
        # 测试文件解析处理器
        file_processor = FileParsingProcessor()
        context = {
            'task_id': 9996,
            'test_mode': True,
            'file_name': 'test.md'
        }
        
        # 测试模式下，只需要有file_name即可处理
        can_handle_result = await file_processor.can_handle(context)
        assert can_handle_result is True  # 测试模式下有file_name就可以
        
        # 但在非测试模式下，需要file_path
        context['test_mode'] = False
        can_handle_result = await file_processor.can_handle(context)
        assert can_handle_result is False  # 没有file_path
        
        context['file_path'] = '/fake/path.md'
        can_handle_result = await file_processor.can_handle(context)
        assert can_handle_result is True  # 有file_path就可以
        
        # 测试文档处理处理器
        doc_processor = DocumentProcessingProcessor(provider)
        doc_context = {
            'task_id': 9995,
            'file_parsing_result': 'test content'
        }
        
        assert await doc_processor.can_handle(doc_context) is True
        result = await doc_processor.process(doc_context)
        assert result.success is True
        assert 'document_processing_result' in doc_context
        
        # 测试问题检测处理器
        issue_processor = IssueDetectionProcessor(provider)
        issue_context = {
            'task_id': 9994,
            'document_processing_result': [
                {'section_title': '测试章节', 'content': '这是测试内容'}
            ]
        }
        
        assert await issue_processor.can_handle(issue_context) is True
        result = await issue_processor.process(issue_context)
        assert result.success is True
        assert 'issue_detection_result' in issue_context


class TestServiceProviderFactory:
    """服务提供者工厂测试"""

    def test_create_mock_provider(self):
        """测试创建Mock提供者"""
        config = {'model': 'factory-test', 'provider': 'mock'}
        provider = ai_service_provider_factory.create_mock_provider(config)
        
        assert provider is not None
        assert provider.is_available() is True
        assert "MockAI" in provider.get_provider_name()


if __name__ == "__main__":
    pytest.main([__file__])