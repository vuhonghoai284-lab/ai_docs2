"""
AI服务工厂 - 根据配置返回真实或模拟的AI服务
"""
from typing import Dict, Any, Optional
from app.services.mock_ai_service import MockAIService


class AIServiceFactory:
    """AI服务工厂类"""
    
    @staticmethod
    def create_service(model_config: Dict[str, Any], test_mode: bool = False):
        """
        创建AI服务实例
        
        Args:
            model_config: 模型配置
            test_mode: 是否为测试模式
            
        Returns:
            AI服务实例
        """
        provider = model_config.get('provider', 'openai')
        
        # 如果是测试模式或使用mock provider，返回模拟服务
        if test_mode or provider == 'mock':
            return MockAIService(model_config.get('config', {}))
        
        # 否则返回真实的AI服务
        # 这里暂时也返回模拟服务，因为真实的AI服务需要API密钥
        # 在生产环境中，这里应该返回真实的OpenAI/Anthropic服务
        return MockAIService(model_config.get('config', {}))
    
    @staticmethod
    def get_service_for_model(model_index: int, settings):
        """
        根据模型索引获取AI服务
        
        Args:
            model_index: 模型索引
            settings: 配置对象
            
        Returns:
            AI服务实例
        """
        models = settings.ai_models
        if model_index < 0 or model_index >= len(models):
            model_index = settings.default_model_index
            
        model_config = models[model_index]
        return AIServiceFactory.create_service(model_config, settings.is_test_mode)