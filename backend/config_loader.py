"""配置加载辅助模块"""
import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def resolve_env_var(value: str) -> str:
        """
        解析环境变量引用
        支持格式: ${ENV_VAR_NAME}
        """
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            return os.getenv(env_var, '')
        return value
    
    @staticmethod
    def get_ai_config(config: Dict[str, Any], model_index: Optional[int] = None) -> Dict[str, Any]:
        """
        获取AI服务配置
        
        Args:
            config: 主配置字典
            model_index: 模型索引（用于新的多模型配置）
        
        Returns:
            包含所有必要配置的字典
        """
        # 检查是否使用新的多模型配置格式
        if 'ai_models' in config:
            models_config = config.get('ai_models', {})
            models = models_config.get('models', [])
            
            # 使用指定的模型索引或默认索引
            if model_index is None:
                model_index = models_config.get('default_index', 0)
            
            # 确保索引有效
            if 0 <= model_index < len(models):
                model_config = models[model_index]
                provider = model_config.get('provider', 'openai')
                inner_config = model_config.get('config', {})
                
                # 解析环境变量
                resolved_config = {}
                for key, value in inner_config.items():
                    resolved_config[key] = ConfigLoader.resolve_env_var(value)
                
                result = {
                    'provider': provider,
                    'api_key': resolved_config.get('api_key', 'dummy-key'),
                    'base_url': resolved_config.get('base_url', 'https://api.openai.com/v1'),
                    'model': resolved_config.get('model', 'gpt-4o-mini'),
                    'temperature': float(resolved_config.get('temperature', 0.3)),
                    'max_tokens': int(resolved_config.get('max_tokens', 4096)),
                    'timeout': int(resolved_config.get('timeout', 30)),
                    'max_retries': int(resolved_config.get('max_retries', 3)),
                    'model_label': model_config.get('label', f'Model {model_index}'),
                    'model_index': model_index
                }
                
                # 添加降级策略配置
                fallback_config = config.get('fallback', {})
                result['fallback_enabled'] = fallback_config.get('enabled', False)
                result['fallback_strategy'] = fallback_config.get('strategy', 'next')
                result['fallback_specific_index'] = fallback_config.get('specific_index', 0)
                
                return result
        
        # 兼容旧的配置格式
        ai_config = config.get('ai_service', {})
        provider = ai_config.get('provider', 'openai')
        
        # 获取提供商特定配置和默认配置
        provider_config = ai_config.get(provider, {})
        default_config = ai_config.get('default', {})
        
        # 合并配置（提供商配置优先）
        merged_config = {**default_config, **provider_config}
        
        # 解析环境变量
        for key, value in merged_config.items():
            merged_config[key] = ConfigLoader.resolve_env_var(value)
        
        # 确保必要的配置存在
        result = {
            'provider': provider,
            'api_key': merged_config.get('api_key') or os.getenv('OPENAI_API_KEY', os.getenv('ANTHROPIC_API_KEY', 'dummy-key')),
            'base_url': merged_config.get('base_url') or os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
            'model': merged_config.get('model', 'gpt-4o-mini'),
            'temperature': float(merged_config.get('temperature', 0.3)),
            'max_tokens': int(merged_config.get('max_tokens', 4096)),
            'timeout': int(merged_config.get('timeout', 30)),
            'max_retries': int(merged_config.get('max_retries', 3))
        }
        
        # 添加降级策略配置
        fallback_config = ai_config.get('fallback', {})
        result['fallback_enabled'] = fallback_config.get('enabled', False)
        result['fallback_provider'] = fallback_config.get('provider')
        
        return result


# 全局配置实例
def get_config() -> Dict[str, Any]:
    """获取全局配置"""
    return ConfigLoader.load_config()


def get_ai_service_config(model_index: Optional[int] = None) -> Dict[str, Any]:
    """获取AI服务配置"""
    config = get_config()
    return ConfigLoader.get_ai_config(config, model_index)