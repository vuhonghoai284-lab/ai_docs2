"""
认证相关视图
"""
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.dto.user import UserResponse, UserLoginResponse, ThirdPartyAuthRequest
from app.views.base import BaseView


class AuthView(BaseView):
    """认证视图类"""
    
    def __init__(self):
        super().__init__()
        self.router = APIRouter(tags=["auth"])
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        self.router.add_api_route("/thirdparty/url", self.get_third_party_auth_url, methods=["GET"])
        self.router.add_api_route("/thirdparty/login", self.third_party_login, methods=["POST"], response_model=UserLoginResponse)
        self.router.add_api_route("/system/login", self.system_admin_login, methods=["POST"], response_model=UserLoginResponse)
    
    def get_third_party_auth_url(self, db: Session = Depends(get_db)):
        """获取第三方认证URL"""
        auth_service = AuthService(db)
        auth_url = auth_service.get_authorization_url()
        return {"auth_url": auth_url}
    
    async def third_party_login(
        self,
        auth_request: ThirdPartyAuthRequest,
        db: Session = Depends(get_db)
    ) -> UserLoginResponse:
        """第三方登录"""
        auth_service = AuthService(db)
        
        try:
            # 使用authorization code交换access token
            token_response = await auth_service.exchange_code_for_token(auth_request.code)
            # 使用access token获取用户信息
            user_info = await auth_service.get_third_party_user_info(token_response.access_token)
            
            # 登录用户
            login_result = auth_service.login_user(
                uid=user_info.uid,
                display_name=user_info.display_name,
                email=user_info.email,
                avatar_url=user_info.avatar_url
            )
            
            if not login_result:
                raise HTTPException(status_code=401, detail="登录失败")
            
            return UserLoginResponse(
                user=UserResponse.from_orm(login_result["user"]),
                access_token=login_result["access_token"],
                token_type=login_result["token_type"]
            )
        except Exception as e:
            print(f"第三方登录失败: {e}")
            raise HTTPException(status_code=401, detail="第三方登录失败")
    
    def system_admin_login(
        self,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
    ) -> UserLoginResponse:
        """系统管理员登录"""
        auth_service = AuthService(db)
        
        # 验证管理员凭据（在实际应用中应该使用加密密码验证）
        if username == "admin" and password == "admin123":
            # 创建或获取系统管理员用户
            login_result = auth_service.login_user(
                uid="sys_admin",
                display_name="系统管理员",
                email="admin@example.com",
                is_system_admin=True,
                is_admin=True
            )
            
            if not login_result:
                raise HTTPException(status_code=401, detail="登录失败")
            
            return UserLoginResponse(
                user=UserResponse.from_orm(login_result["user"]),
                access_token=login_result["access_token"],
                token_type=login_result["token_type"]
            )
        else:
            raise HTTPException(status_code=401, detail="用户名或密码错误")


# 创建视图实例并导出router
auth_view = AuthView()
router = auth_view.router