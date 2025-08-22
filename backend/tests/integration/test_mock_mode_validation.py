"""
Mock模式验证测试
确保业务代码流程与生产环境保持一致，仅在外部API调用时进行mock
"""
import pytest
import time
from app.core.database import Base, engine
# 导入所有模型以确保它们被注册到Base.metadata
from app.models import *


class TestMockModeValidation:
    """Mock模式验证测试类"""
    
    @classmethod
    def setup_class(cls):
        """设置测试类，创建数据库表"""
        # 创建所有表
        Base.metadata.create_all(bind=engine)
    
    @classmethod
    def teardown_class(cls):
        """清理测试类"""
        # 可选：删除测试数据
        pass
    
    @pytest.mark.asyncio
    async def test_auth_service_business_logic_consistency(self):
        """测试认证服务业务逻辑一致性"""
        from app.core.database import SessionLocal
        from app.services.auth import AuthService
        from app.core.config import get_settings
        
        # 使用当前配置（应该是测试配置）
        get_settings()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            auth_service = AuthService(db)
            
            # 步骤1: 构建请求参数（与生产环境完全一致）
            test_code = f"test_code_{int(time.time())}"
            
            # 步骤2: 令牌交换（业务逻辑与生产环境完全一致）
            token_response = await auth_service.exchange_code_for_token(test_code)
            
            # 验证响应结构
            assert hasattr(token_response, 'access_token')
            assert hasattr(token_response, 'refresh_token')
            assert hasattr(token_response, 'scope')
            assert hasattr(token_response, 'expires_in')
            assert token_response.scope == "base.profile"
            
            # 步骤3: 用户信息获取（业务逻辑与生产环境完全一致）
            user_info = await auth_service.get_third_party_user_info(token_response.access_token)
            
            # 验证响应结构
            assert hasattr(user_info, 'uid')
            assert hasattr(user_info, 'display_name')
            assert hasattr(user_info, 'email')
            assert hasattr(user_info, 'avatar_url')
            
            # 步骤4: 用户登录（业务逻辑与生产环境完全一致）
            login_result = auth_service.login_user(
                uid=user_info.uid,
                display_name=user_info.display_name,
                email=user_info.email,
                avatar_url=user_info.avatar_url
            )
            
            # 验证登录结果
            assert login_result is not None
            assert "user" in login_result
            assert "access_token" in login_result
            assert "token_type" in login_result
            
            # 步骤5: 令牌验证（业务逻辑与生产环境完全一致）
            jwt_token = login_result["access_token"]
            verified_user = auth_service.verify_token(jwt_token)
            
            assert verified_user is not None
            assert verified_user.uid == user_info.uid
            
        finally:
            db.close()
    
    @pytest.mark.asyncio
    async def test_ai_service_business_logic_consistency(self):
        """测试AI服务业务逻辑一致性"""
        pytest.skip("AI服务测试已移至专门的测试文件")
    
    @pytest.mark.asyncio
    async def test_mock_mode_performance(self):
        """测试Mock模式性能"""
        from app.core.database import SessionLocal
        from app.services.auth import AuthService
        from app.core.config import get_settings
        
        get_settings()
        db = SessionLocal()
        
        try:
            auth_service = AuthService(db)
            
            # 测试多次调用的性能
            start_time = time.time()
            for i in range(3):  # 减少测试次数以适配测试环境
                test_code = f"perf_test_{i}"
                token_response = await auth_service.exchange_code_for_token(test_code)
                await auth_service.get_third_party_user_info(token_response.access_token)
            
            total_time = time.time() - start_time
            avg_time = total_time / 3
            
            # Mock模式应该很快
            assert avg_time < 2.0, f"Mock模式性能过慢: {avg_time}s"
            
        finally:
            db.close()
    
    def test_config_loading_validation(self):
        """测试配置加载和Mock控制验证"""
        from app.core.config import get_settings
        
        # 测试当前配置
        settings = get_settings()
        
        # 在测试环境中，应该启用Mock
        if settings.is_test_mode:
            assert settings.is_service_mocked('third_party_auth') == True
            assert settings.is_service_mocked('ai_models') == True
        
        # 验证配置方法可用
        assert hasattr(settings, 'is_test_mode')
        assert hasattr(settings, 'is_service_mocked')
        assert callable(settings.is_service_mocked)