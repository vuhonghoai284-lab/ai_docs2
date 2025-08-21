"""
AI服务工厂 - 根据配置返回真实或模拟的AI服务
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.mock_ai_service import MockAIService
from app.services.document_processor import DocumentProcessor
from app.services.issue_detector import IssueDetector
from app.services.realtime_logger import realtime_logger, TaskLoggerAdapter


class AIServiceFactory:
    """AI服务工厂类 - 提供完整的文档处理和问题检测服务"""
    
    def __init__(self):
        self.logger = logging.getLogger("ai_service_factory")
        self.logger.setLevel(logging.INFO)
        
        # 确保日志能输出到控制台
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def create_service(self, model_config: Dict[str, Any], test_mode: bool = False, db_session: Optional[Session] = None):
        """
        创建AI服务实例
        
        Args:
            model_config: 模型配置
            test_mode: 是否为测试模式
            db_session: 数据库会话
            
        Returns:
            AI服务实例字典，包含文档处理器和问题检测器
        """
        provider = model_config.get('provider', 'openai')
        
        self.logger.info(f"🏭 创建AI服务: provider={provider}, test_mode={test_mode}")
        
        # 如果是测试模式或使用mock provider，返回模拟服务
        if test_mode or provider == 'mock':
            self.logger.info("🔧 使用模拟AI服务")
            return {
                'mock_service': MockAIService(model_config.get('config', {})),
                'document_processor': None,
                'issue_detector': None
            }
        
        # 否则返回真实的AI服务组件
        try:
            document_processor = DocumentProcessor(model_config, db_session)
            issue_detector = IssueDetector(model_config, db_session)
            
            self.logger.info("✅ 真实AI服务创建成功")
            return {
                'mock_service': None,
                'document_processor': document_processor,
                'issue_detector': issue_detector
            }
        except Exception as e:
            self.logger.error(f"❌ 创建真实AI服务失败: {str(e)}")
            self.logger.warning("🔄 降级到模拟服务")
            return {
                'mock_service': MockAIService(model_config.get('config', {})),
                'document_processor': None,
                'issue_detector': None
            }
    
    def get_service_for_model(self, model_index: int, settings, db_session: Optional[Session] = None):
        """
        根据模型索引获取AI服务
        
        Args:
            model_index: 模型索引
            settings: 配置对象
            db_session: 数据库会话
            
        Returns:
            AI服务实例字典
        """
        models = settings.ai_models
        if model_index < 0 or model_index >= len(models):
            self.logger.warning(f"⚠️ 无效的模型索引 {model_index}，使用默认模型 {settings.default_model_index}")
            model_index = settings.default_model_index
            
        model_config = models[model_index]
        self.logger.info(f"🎯 选择模型: {model_config.get('label', 'Unknown')} (索引: {model_index})")
        
        return self.create_service(model_config, settings.is_test_mode, db_session)
    
    def create_task_logger(self, task_id: int, operation: str = "") -> TaskLoggerAdapter:
        """
        创建任务专用日志适配器
        
        Args:
            task_id: 任务ID
            operation: 操作类型
            
        Returns:
            任务日志适配器
        """
        return TaskLoggerAdapter(realtime_logger, task_id, operation)
    
    async def start_realtime_logging(self):
        """启动实时日志服务"""
        await realtime_logger.start()
        self.logger.info("🚀 实时日志服务已启动")
    
    async def stop_realtime_logging(self):
        """停止实时日志服务"""
        await realtime_logger.stop()
        self.logger.info("🛑 实时日志服务已停止")
    
    def subscribe_to_logs(self, callback):
        """订阅实时日志"""
        realtime_logger.subscribe(callback)
    
    def unsubscribe_from_logs(self, callback):
        """取消订阅实时日志"""
        realtime_logger.unsubscribe(callback)


# 创建全局工厂实例
ai_service_factory = AIServiceFactory()