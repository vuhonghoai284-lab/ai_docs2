"""
用户认证服务
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
import time
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user import UserRepository
from app.dto.user import UserCreate, ThirdPartyTokenResponse, ThirdPartyUserInfoResponse
from app.core.config import get_settings
from app.services.interfaces.auth_service import IAuthService


class AuthService(IAuthService):
    """用户认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings = get_settings()
        # JWT密钥和过期时间配置
        jwt_config = self.settings.jwt_config
        self.SECRET_KEY = jwt_config.get("secret_key", "ai_doc_test_secret_key")
        self.ALGORITHM = jwt_config.get("algorithm", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = jwt_config.get("access_token_expire_minutes", 30)
        
        # 第三方认证配置
        self.third_party_config = self.settings.third_party_auth_config
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def authenticate_user(self, uid: str) -> Optional[User]:
        """验证用户是否存在"""
        user = self.user_repo.get_by_uid(uid)
        return user
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建新用户"""
        return self.user_repo.create(user_data)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.user_repo.get_by_id(user_id)
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        """更新用户最后登录时间"""
        return self.user_repo.update_last_login(user_id)
    
    def login_user(self, uid: str, display_name: str = None, email: str = None, 
                   avatar_url: str = None, is_admin: bool = False, 
                   is_system_admin: bool = False) -> Optional[Dict[str, Any]]:
        """用户登录"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 查找用户
                user = self.user_repo.get_by_uid(uid)
                
                # 如果用户不存在，创建新用户
                if not user:
                    user_create = UserCreate(
                        uid=uid,
                        display_name=display_name,
                        email=email,
                        avatar_url=avatar_url,
                        is_admin=is_admin,
                        is_system_admin=is_system_admin
                    )
                    user = self.user_repo.create(user_create)
                else:
                    # 更新用户最后登录时间
                    self.user_repo.update_last_login(user.id)
                
                # 如果成功，跳出重试循环
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                # 处理各种并发问题
                if ("UNIQUE constraint failed" in error_msg or 
                    "IntegrityError" in error_msg or 
                    "NULL identity key" in error_msg or
                    "FlushError" in error_msg or
                    "database is locked" in error_msg):
                    
                    # 回滚当前事务
                    try:
                        self.db.rollback()
                    except:
                        pass
                    
                    # 重新查找用户（可能被其他线程创建了）
                    user = self.user_repo.get_by_uid(uid)
                    if user:
                        break  # 找到用户，成功
                    
                    # 如果还有重试次数，稍等片刻再重试
                    if retry_count < max_retries:
                        import time
                        time.sleep(0.1 * retry_count)  # 递增延迟
                        continue
                    else:
                        raise e  # 重试次数用完，抛出异常
                else:
                    raise e  # 非并发问题，直接抛出
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def verify_token(self, token: str) -> Optional[User]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            user = self.user_repo.get_by_id(int(user_id))
            return user
        except jwt.PyJWTError:
            return None
    
    async def exchange_code_for_token(self, code: str) -> ThirdPartyTokenResponse:
        """使用authorization code交换access token"""
        import httpx
        
        # 从配置获取参数
        payload = {
            "client_id": self.third_party_config.get("client_id"),
            "client_secret": self.third_party_config.get("client_secret"),
            "redirect_url": self.third_party_config.get("redirect_url"),
            "grant_type": "authorization_code",
            "code": code
        }
        
        # 验证必需的配置
        if not payload["client_id"] or not payload["client_secret"] or not payload["redirect_url"]:
            raise ValueError("第三方登录配置不完整，请检查client_id、client_secret和redirect_url配置")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 执行HTTP调用（仅在此处进行mock判断）
        try:
            response_data = await self._call_third_party_token_api(payload, headers)
            return ThirdPartyTokenResponse(
                access_token=response_data["access_token"],
                refresh_token=response_data.get("refresh_token"),
                scope=response_data["scope"],
                expires_in=response_data["expires_in"]
            )
        except Exception as e:
            print(f"第三方API调用失败: {e}")
            # 只有在真实API调用失败时才fallback到mock数据
            if not self.settings.is_test_mode:
                raise
            return self._mock_token_response(code)
    
    async def _call_third_party_token_api(self, payload: dict, headers: dict) -> dict:
        """调用第三方令牌API（仅在此方法内进行mock判断）"""
        # 检查是否需要mock第三方认证API
        if self.settings.is_service_mocked('third_party_auth'):
            # 获取mock配置
            mock_config = self.settings.get_mock_config('third_party_auth')
            delay = mock_config.get('mock_delay', 0.1)
            
            # 模拟API调用延迟
            import asyncio
            await asyncio.sleep(delay)
            
            # 返回模拟的API响应数据
            return {
                "access_token": f"mock_access_token_{payload['code']}_{int(time.time())}",
                "refresh_token": f"mock_refresh_token_{payload['code']}_{int(time.time())}",
                "scope": "base.profile",
                "expires_in": 3600
            }
        
        # 生产环境或非mock模式：真实的API调用
        import httpx
        # 从配置获取API端点和超时设置
        api_endpoints = self.third_party_config.get("api_endpoints", {})
        token_url = api_endpoints.get("token_url")
        timeout = self.third_party_config.get("request_timeout", 30)
        
        if not token_url:
            raise ValueError("第三方登录token_url配置缺失")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                json=payload,
                headers=headers,
                timeout=float(timeout)
            )
            response.raise_for_status()
            return response.json()
    
    async def get_third_party_user_info(self, access_token: str) -> ThirdPartyUserInfoResponse:
        """使用access token获取用户信息"""
        # 从配置构建请求参数
        payload = {
            "client_id": self.third_party_config.get("client_id"),
            "access_token": access_token,
            "scope": self.third_party_config.get("scope", "base.profile")
        }
        
        if not payload["client_id"]:
            raise ValueError("第三方登录client_id配置缺失")
        
        # 执行HTTP调用（仅在此处进行mock判断）
        try:
            user_data = await self._call_third_party_userinfo_api(payload)
            return ThirdPartyUserInfoResponse(
                uid=user_data["uid"],
                display_name=user_data.get("displayNameCn"),
                email=user_data.get("email", f"{user_data['uid']}@example.com"),
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_data['uid']}"
            )
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            # 只有在真实API调用失败时才fallback到mock数据
            if not self.settings.is_test_mode:
                raise
            return self._mock_user_info(access_token)
    
    async def _call_third_party_userinfo_api(self, payload: dict) -> dict:
        """调用第三方用户信息API（仅在此方法内进行mock判断）"""
        # 检查是否需要mock第三方认证API
        if self.settings.is_service_mocked('third_party_auth'):
            # 获取mock配置
            mock_config = self.settings.get_mock_config('third_party_auth')
            delay = mock_config.get('mock_delay', 0.1)
            
            # 模拟API调用延迟
            import asyncio
            await asyncio.sleep(delay)
            
            # 基于access_token生成一致的模拟用户信息
            import hashlib
            hash_obj = hashlib.md5(payload["access_token"].encode())
            user_hash = hash_obj.hexdigest()[:8]
            return {
                "uid": f"test_user_{user_hash}",
                "displayNameCn": f"测试用户_{user_hash[:4]}",
                "email": f"user_{user_hash[:4]}@example.com"
            }
        
        # 生产环境或非mock模式：真实的API调用
        import httpx
        # 从配置获取API端点和超时设置
        api_endpoints = self.third_party_config.get("api_endpoints", {})
        userinfo_url = api_endpoints.get("userinfo_url")
        timeout = self.third_party_config.get("request_timeout", 30)
        
        if not userinfo_url:
            raise ValueError("第三方登录userinfo_url配置缺失")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                userinfo_url,
                json=payload,
                timeout=float(timeout)
            )
            response.raise_for_status()
            return response.json()
    
    def get_authorization_url(self, state: str = "12345678") -> str:
        """获取第三方认证授权URL"""
        # 从配置获取参数
        api_endpoints = self.third_party_config.get("api_endpoints", {})
        auth_url = api_endpoints.get("authorization_url")
        client_id = self.third_party_config.get("client_id")
        redirect_url = self.third_party_config.get("redirect_url")
        scope = self.third_party_config.get("scope", "base.profile")
        
        # 验证必需的配置
        if not auth_url or not client_id or not redirect_url:
            raise ValueError("第三方登录配置不完整，请检查authorization_url、client_id和redirect_url配置")
        
        return (
            f"{auth_url}?"
            f"client_id={client_id}&response_type=code&"
            f"redirect_url={redirect_url}&"
            f"scope={scope}&display=page&"
            f"state={state}"
        )
    
    def _mock_token_response(self, code: str) -> ThirdPartyTokenResponse:
        """模拟第三方令牌交换（用于测试）"""
        import time
        return ThirdPartyTokenResponse(
            access_token=f"mock_access_token_{code}_{int(time.time())}",
            refresh_token=f"mock_refresh_token_{code}_{int(time.time())}",
            scope="base.profile",
            expires_in=3600
        )
    
    def _mock_user_info(self, access_token: str) -> ThirdPartyUserInfoResponse:
        """模拟获取第三方用户信息（用于测试）"""
        import hashlib
        # 基于access_token生成一致的模拟用户信息
        hash_obj = hashlib.md5(access_token.encode())
        user_hash = hash_obj.hexdigest()[:8]
        
        return ThirdPartyUserInfoResponse(
            uid=f"test_user_{user_hash}",
            display_name=f"测试用户_{user_hash[:4]}",
            email=f"user_{user_hash[:4]}@example.com",
            avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_hash}"
        )
    
    def create(self, **kwargs) -> User:
        """创建用户实体"""
        user_data = UserCreate(**kwargs)
        return self.user_repo.create(user_data)
    
    def get_by_id(self, entity_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.user_repo.get_by_id(entity_id)
    
    def get_all(self) -> List[User]:
        """获取所有用户"""
        return self.user_repo.get_all()
    
    def update(self, entity_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        return self.user_repo.update(entity_id, **kwargs)
    
    def delete(self, entity_id: int) -> bool:
        """删除用户"""
        return self.user_repo.delete(entity_id)
    
    def generate_token(self, user: User) -> str:
        """生成访问令牌"""
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        return self.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )