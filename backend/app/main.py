"""
重构后的主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine, get_db, Base
from app.views import system_view, auth_view, task_view, user_view, ai_output_view, issue_view, task_log_view, analytics_view

# 导入所有模型以确保它们被注册到Base.metadata
from app.models import *

# 获取配置
settings = get_settings()

# 创建数据库表（非测试模式下）
if not settings.is_test_mode:
    Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    app = FastAPI(
        title="AI文档测试系统API",
        description="基于AI的文档质量检测系统后端API",
        version="2.0.0",
        debug=settings.server_config.get('debug', False)
    )
    
    # 配置CORS
    cors_origins = settings.cors_origins
    
    # 开发模式或端口不是8080时，允许更宽松的CORS
    server_port = settings.server_config.get('port', 8080)
    if server_port != 8080 or settings.server_config.get('debug', False):
        print(f"💡 检测到非标准端口({server_port})或调试模式，启用宽松CORS策略")
        # 添加当前服务器端口的前端地址
        additional_origins = [
            f"http://localhost:3000",
            f"http://localhost:5173", 
            f"http://127.0.0.1:3000",
            f"http://127.0.0.1:5173"
        ]
        for origin in additional_origins:
            if origin not in cors_origins:
                cors_origins.append(origin)
    
    print(f"🌐 CORS允许的源: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

# 创建应用实例
app = create_app()

def setup_startup_event(app: FastAPI):
    """设置应用启动事件"""
    @app.on_event("startup")
    async def startup_event():
        """应用启动时的初始化操作"""        
        from app.services.model_initializer import model_initializer
        
        # 初始化AI模型配置到数据库（测试模式下也需要）
        db = next(get_db())
        try:
            models = model_initializer.initialize_models(db)
            mode_text = "测试模式" if settings.is_test_mode else "生产模式"
            print(f"✓ {mode_text} - 已初始化 {len(models)} 个AI模型")
        except Exception as e:
            mode_text = "测试模式" if settings.is_test_mode else "生产模式"
            print(f"✗ {mode_text} - AI模型初始化失败: {e}")
        finally:
            db.close()

# 设置启动事件
setup_startup_event(app)

def setup_routes(app: FastAPI):
    """设置所有路由"""
    # 注册系统相关路由
    app.include_router(system_view.router, tags=["系统"])
    
    # 注册认证相关路由
    app.include_router(auth_view.router, prefix="/api/auth", tags=["认证"])
    
    # 注册任务相关路由
    app.include_router(task_view.router, prefix="/api/tasks", tags=["任务"])
    
    # 注册用户相关路由
    app.include_router(user_view.router, prefix="/api/users", tags=["用户"])
    
    # 注册AI输出相关路由（任务相关的AI输出）
    # 单独的AI输出查询路由注册在ai-outputs前缀下
    from fastapi import APIRouter
    from app.views.ai_output_view import ai_output_view
    
    # 为任务相关的AI输出创建单独的路由
    task_ai_output_router = APIRouter(tags=["AI输出"])
    task_ai_output_router.add_api_route("/{task_id}/ai-outputs", ai_output_view.get_task_ai_outputs, methods=["GET"])
    app.include_router(task_ai_output_router, prefix="/api/tasks")
    
    # 为单独的AI输出查询创建路由
    single_ai_output_router = APIRouter(tags=["AI输出"])
    single_ai_output_router.add_api_route("/{output_id}", ai_output_view.get_ai_output_detail, methods=["GET"])
    app.include_router(single_ai_output_router, prefix="/api/ai-outputs")
    
    # 注册问题反馈相关路由
    app.include_router(issue_view.router, prefix="/api/issues", tags=["问题反馈"])
    
    # 注册任务日志相关路由
    app.include_router(task_log_view.router, prefix="/api/tasks", tags=["任务日志"])
    
    # 注册运营数据统计相关路由
    app.include_router(analytics_view.router, tags=["运营数据统计"])

# 设置路由
setup_routes(app)


if __name__ == "__main__":
    import uvicorn
    print("启动服务器...")
    # 从配置获取服务器端口
    server_config = settings.server_config
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8080)
    uvicorn.run(app, host=host, port=port)