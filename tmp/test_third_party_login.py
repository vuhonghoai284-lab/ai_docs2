#!/usr/bin/env python3
"""
第三方登录测试脚本
测试完整的第三方登录流程，包括Mock模式下的API调用
"""

import sys
import os
import asyncio
import httpx
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import init_settings
from app.services.auth import AuthService
from app.core.database import SessionLocal

async def test_third_party_auth_flow():
    """测试第三方认证完整流程"""
    print("🚀 开始测试第三方登录流程...\n")
    
    # 1. 初始化测试配置
    print("1️⃣ 初始化测试配置...")
    
    # 创建临时测试配置
    test_env = {
        'FRONTEND_DOMAIN': 'http://localhost:5173',
        'THIRD_PARTY_CLIENT_ID': 'test_client_id',
        'THIRD_PARTY_CLIENT_SECRET': 'test_client_secret',
        'THIRD_PARTY_AUTH_URL': 'https://mock-auth-provider.com/oauth2/authorize',
        'THIRD_PARTY_TOKEN_URL': 'https://mock-auth-provider.com/oauth2/accesstoken',
        'THIRD_PARTY_USERINFO_URL': 'https://mock-auth-provider.com/oauth2/userinfo',
        'JWT_SECRET_KEY': 'test_jwt_secret_key'
    }
    
    # 设置测试环境变量
    for key, value in test_env.items():
        os.environ[key] = value
    
    # 初始化配置（测试模式）
    settings = init_settings()
    settings.config['test_mode'] = True
    settings._test_mode = True
    
    print(f"✅ 配置加载成功")
    print(f"   - 前端域名: {test_env['FRONTEND_DOMAIN']}")
    print(f"   - 客户端ID: {test_env['THIRD_PARTY_CLIENT_ID']}")
    print(f"   - 测试模式: {settings.is_test_mode}")
    print()
    
    # 2. 测试获取授权URL
    print("2️⃣ 测试获取第三方授权URL...")
    
    # 创建数据库会话
    db_session = SessionLocal()
    try:
        auth_service = AuthService(db_session)
        
        try:
            auth_url = auth_service.get_authorization_url("test_state_123")
            print(f"✅ 授权URL生成成功:")
            print(f"   {auth_url}")
            
            # 验证URL组成
            expected_redirect_url = "http://localhost:5173/callback"
            if expected_redirect_url in auth_url:
                print(f"✅ 重定向URL配置正确: {expected_redirect_url}")
            else:
                print(f"❌ 重定向URL配置错误，期望包含: {expected_redirect_url}")
                return False
                
        except Exception as e:
            print(f"❌ 授权URL生成失败: {e}")
            return False
            
        print()
        
        # 3. 测试Token交换（Mock模式）
        print("3️⃣ 测试使用授权码交换Token...")
        
        mock_auth_code = "mock_auth_code_12345"
        
        try:
            token_response = await auth_service.exchange_code_for_token(mock_auth_code)
            print(f"✅ Token交换成功:")
            print(f"   - Access Token: {token_response.access_token[:20]}...")
            print(f"   - Refresh Token: {token_response.refresh_token[:20]}...")
            print(f"   - Scope: {token_response.scope}")
            print(f"   - Expires In: {token_response.expires_in}")
            
        except Exception as e:
            print(f"❌ Token交换失败: {e}")
            return False
            
        print()
        
        # 4. 测试获取用户信息（Mock模式）
        print("4️⃣ 测试获取第三方用户信息...")
        
        try:
            user_info = await auth_service.get_third_party_user_info(token_response.access_token)
            print(f"✅ 用户信息获取成功:")
            print(f"   - UID: {user_info.uid}")
            print(f"   - 显示名: {user_info.display_name}")
            print(f"   - 邮箱: {user_info.email}")
            print(f"   - 头像: {user_info.avatar_url}")
            
        except Exception as e:
            print(f"❌ 用户信息获取失败: {e}")
            return False
            
        print()
        
        # 5. 测试完整登录流程
        print("5️⃣ 测试完整登录流程...")
        
        try:
            login_result = auth_service.login_user(
                uid=user_info.uid,
                display_name=user_info.display_name,
                email=user_info.email,
                avatar_url=user_info.avatar_url
            )
            
            print(f"✅ 用户登录成功:")
            print(f"   - 用户ID: {login_result['user'].id}")
            print(f"   - 用户UID: {login_result['user'].uid}")
            print(f"   - 显示名: {login_result['user'].display_name}")
            print(f"   - 邮箱: {login_result['user'].email}")
            print(f"   - Token类型: {login_result['token_type']}")
            print(f"   - Access Token: {login_result['access_token'][:20]}...")
            
        except Exception as e:
            print(f"❌ 用户登录失败: {e}")
            return False
            
        print()
        
    finally:
        db_session.close()
        
    print("🎉 第三方登录流程测试完成！所有步骤均成功。")
    return True

async def test_api_endpoints():
    """测试API端点响应"""
    print("6️⃣ 测试API端点...")
    
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        try:
            # 测试获取授权URL端点
            response = await client.get(f"{base_url}/auth/thirdparty/url")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取授权URL端点正常: {data.get('auth_url', '')[:50]}...")
            else:
                print(f"❌ 获取授权URL端点异常: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  API端点测试跳过（服务未启动）: {e}")
            
        try:
            # 测试第三方登录端点
            test_code = "test_mock_code_123"
            response = await client.post(f"{base_url}/auth/thirdparty/login", 
                                       json={"code": test_code})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 第三方登录端点正常: 用户 {data.get('user', {}).get('display_name', 'Unknown')}")
            else:
                print(f"❌ 第三方登录端点异常: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  API端点测试跳过（服务未启动）: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 AI文档测试系统 - 第三方登录测试")
    print("=" * 60)
    print()
    
    try:
        # 运行异步测试
        success = asyncio.run(test_third_party_auth_flow())
        
        if success:
            print()
            print("✅ 核心功能测试通过！")
            
            # 尝试测试API端点
            asyncio.run(test_api_endpoints())
            
            print()
            print("📋 测试总结:")
            print("  ✅ 配置加载正确")
            print("  ✅ 授权URL生成正常")
            print("  ✅ Mock Token交换成功")
            print("  ✅ Mock用户信息获取成功") 
            print("  ✅ 完整登录流程正常")
            print()
            print("🎯 建议下一步:")
            print("  1. 启动后端服务: cd backend && PYTHONPATH=. CONFIG_FILE=config.yaml python app/main.py")
            print("  2. 启动前端服务: cd frontend && npm run dev")
            print("  3. 访问 http://localhost:5173 测试完整UI流程")
            print("  4. 点击第三方登录按钮进行端到端测试")
            
        else:
            print("❌ 测试失败，请检查配置和代码实现")
            
    except Exception as e:
        print(f"💥 测试过程中发生意外错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()