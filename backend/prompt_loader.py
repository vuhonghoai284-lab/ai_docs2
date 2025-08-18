"""提示词模板加载器"""
import os
import yaml
from typing import Dict, Optional, Any
from pathlib import Path


class PromptLoader:
    """提示词模板加载和管理器"""
    
    def __init__(self, prompts_dir: str = None):
        """
        初始化提示词加载器
        
        Args:
            prompts_dir: 提示词模板目录路径，默认为当前目录下的prompts文件夹
        """
        if prompts_dir is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        
        self.prompts_dir = Path(prompts_dir)
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        if not self.prompts_dir.exists():
            raise ValueError(f"提示词目录不存在: {self.prompts_dir}")
    
    def load_template(self, template_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        加载提示词模板
        
        Args:
            template_name: 模板名称（不含扩展名）
            use_cache: 是否使用缓存
            
        Returns:
            模板内容字典
        """
        # 检查缓存
        if use_cache and template_name in self.cache:
            return self.cache[template_name]
        
        # 构建文件路径
        template_file = self.prompts_dir / f"{template_name}.yaml"
        
        if not template_file.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_file}")
        
        # 加载YAML文件
        with open(template_file, 'r', encoding='utf-8') as f:
            template_data = yaml.safe_load(f)
        
        # 缓存模板
        if use_cache:
            self.cache[template_name] = template_data
        
        return template_data
    
    def format_prompt(self, template_name: str, prompt_type: str, **kwargs) -> str:
        """
        格式化提示词
        
        Args:
            template_name: 模板名称
            prompt_type: 提示词类型（system_prompt 或 user_prompt_template）
            **kwargs: 模板参数
            
        Returns:
            格式化后的提示词
        """
        template_data = self.load_template(template_name)
        
        # 获取提示词模板
        if prompt_type not in template_data:
            raise KeyError(f"模板中不存在 {prompt_type}")
        
        prompt_template = template_data[prompt_type]
        
        # 如果是用户提示词模板，需要格式化
        if prompt_type == 'user_prompt_template':
            # 验证必需参数
            if 'parameters' in template_data:
                for param_name, param_info in template_data['parameters'].items():
                    if param_info.get('required', False) and param_name not in kwargs:
                        raise ValueError(f"缺少必需参数: {param_name}")
                    
                    # 处理最大长度限制
                    if param_name in kwargs and 'max_length' in param_info:
                        max_len = param_info['max_length']
                        if isinstance(kwargs[param_name], str) and len(kwargs[param_name]) > max_len:
                            kwargs[param_name] = kwargs[param_name][:max_len]
            
            # 格式化模板
            return prompt_template.format(**kwargs)
        
        return prompt_template
    
    def get_system_prompt(self, template_name: str) -> str:
        """
        获取系统提示词
        
        Args:
            template_name: 模板名称
            
        Returns:
            系统提示词
        """
        return self.format_prompt(template_name, 'system_prompt')
    
    def get_user_prompt(self, template_name: str, **kwargs) -> str:
        """
        获取用户提示词
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            格式化后的用户提示词
        """
        return self.format_prompt(template_name, 'user_prompt_template', **kwargs)
    
    def get_detection_rules(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取检测规则配置
        
        Args:
            template_name: 模板名称
            
        Returns:
            检测规则配置，如果不存在返回None
        """
        template_data = self.load_template(template_name)
        return template_data.get('detection_rules')
    
    def get_severity_mapping(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        获取严重程度映射配置
        
        Args:
            template_name: 模板名称
            
        Returns:
            严重程度映射配置，如果不存在返回None
        """
        template_data = self.load_template(template_name)
        return template_data.get('severity_mapping')
    
    def list_templates(self) -> list:
        """
        列出所有可用的模板
        
        Returns:
            模板名称列表
        """
        templates = []
        for file_path in self.prompts_dir.glob('*.yaml'):
            templates.append(file_path.stem)
        return templates
    
    def reload_template(self, template_name: str) -> Dict[str, Any]:
        """
        重新加载模板（不使用缓存）
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容字典
        """
        # 清除缓存
        if template_name in self.cache:
            del self.cache[template_name]
        
        # 重新加载
        return self.load_template(template_name, use_cache=False)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 创建全局实例
prompt_loader = PromptLoader()