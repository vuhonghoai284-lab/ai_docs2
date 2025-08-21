"""
应用配置管理
"""
import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class Settings:
    """应用配置类"""
    
    def __init__(self, config_file: Optional[str] = None):
        # 支持通过环境变量或参数指定配置文件
        if config_file:
            self.config_file = config_file
        else:
            # 检查环境变量
            env_mode = os.getenv('APP_MODE', 'production')
            if env_mode == 'test':
                self.config_file = "config.test.yaml"
            else:
                self.config_file = os.getenv('CONFIG_FILE', 'config.yaml')
        
        self.config = self._load_config()
        self._test_mode = self.config.get('test_mode', False)
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            # 如果测试配置不存在，回退到默认配置
            if self.config_file == "config.test.yaml":
                print(f"测试配置文件不存在，使用默认配置")
                self.config_file = "config.yaml"
                config_path = Path(self.config_file)
            
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
            
        print(f"加载配置文件: {self.config_file}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 处理环境变量替换
        self._replace_env_vars(config)
        return config
    
    def _replace_env_vars(self, config: Any) -> None:
        """递归替换配置中的环境变量"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._replace_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                if isinstance(item, (dict, list)):
                    self._replace_env_vars(item)
    
    @property
    def is_test_mode(self) -> bool:
        """是否为测试模式"""
        return self._test_mode
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        db_path = self.config.get('database', './data/app.db')
        if not db_path.startswith('sqlite://'):
            db_path = f'sqlite:///{db_path}'
        return db_path
    
    @property
    def upload_dir(self) -> str:
        """文件上传目录"""
        dirs = self.config.get('directories', {})
        return dirs.get('upload_dir', './data/uploads')
    
    @property
    def data_dir(self) -> str:
        """数据目录"""
        dirs = self.config.get('directories', {})
        return dirs.get('data_dir', './data')
    
    @property
    def ai_models(self) -> List[Dict[str, Any]]:
        """AI模型配置"""
        return self.config.get('ai_models', {}).get('models', [])
    
    @property
    def default_model_index(self) -> int:
        """默认模型索引"""
        return self.config.get('ai_models', {}).get('default_index', 0)
    
    @property
    def file_settings(self) -> Dict[str, Any]:
        """文件设置"""
        return self.config.get('file_settings', {})
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS允许的源"""
        cors_config = self.config.get('cors', {})
        if cors_config.get('enabled', True):
            return cors_config.get('origins', [
                "http://localhost:3000", 
                "http://localhost:5173", 
                "http://127.0.0.1:3000", 
                "http://127.0.0.1:5173"
            ])
        return []
    
    @property
    def test_data_config(self) -> Dict[str, Any]:
        """测试数据配置（仅测试模式下使用）"""
        return self.config.get('test_data', {})
    
    @property
    def external_api_mock_config(self) -> Dict[str, Any]:
        """外部API Mock配置"""
        return self.config.get('external_api_mock', {})
    
    def get_mock_config(self, service_name: str) -> Dict[str, Any]:
        """获取指定服务的Mock配置"""
        return self.external_api_mock_config.get(service_name, {})
    
    def is_service_mocked(self, service_name: str) -> bool:
        """检查指定服务是否需要mock（仅在测试模式下有效）"""
        if not self.is_test_mode:
            return False
        mock_config = self.get_mock_config(service_name)
        return mock_config.get('enabled', False)
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """服务器配置"""
        return self.config.get('server', {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False,
            'reload': False
        })
    
    def reload(self, config_file: Optional[str] = None):
        """重新加载配置"""
        if config_file:
            self.config_file = config_file
        self.config = self._load_config()
        self._test_mode = self.config.get('test_mode', False)


# 全局配置实例（延迟初始化）
settings: Optional[Settings] = None

def get_settings() -> Settings:
    """获取配置实例"""
    global settings
    if settings is None:
        settings = Settings()
    return settings

def init_settings(config_file: Optional[str] = None) -> Settings:
    """初始化配置"""
    global settings
    settings = Settings(config_file)
    return settings