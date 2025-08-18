"""
测试任务日志实时展示功能
"""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Task
from utils.task_logger import TaskLoggerFactory, TaskStage
import time

# 创建数据库连接
DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def simulate_task_processing(task_id: int):
    """模拟任务处理过程，生成日志"""
    
    # 获取日志管理器
    logger = await TaskLoggerFactory.get_logger(str(task_id), "task_processor")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 获取任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            await logger.error(f"任务不存在: {task_id}")
            return
        
        # 更新任务状态
        task.status = 'processing'
        task.progress = 0
        db.commit()
        
        # 开始处理
        await logger.set_stage(TaskStage.INIT, f"开始处理任务: {task.title}", 0)
        await asyncio.sleep(2)
        
        # 文档解析阶段
        await logger.set_stage(TaskStage.PARSING, "开始解析文档", 10)
        await logger.debug("读取文件内容", metadata={"file_name": task.file_name, "file_size": task.file_size})
        await asyncio.sleep(2)
        
        await logger.progress(20, "文档解析进行中...")
        await asyncio.sleep(1)
        
        await logger.info("文档解析完成", progress=30)
        await asyncio.sleep(1)
        
        # 内容分析阶段
        await logger.set_stage(TaskStage.ANALYZING, "开始内容分析", 35)
        
        # 模拟分析多个章节
        for i in range(3):
            await logger.info(f"分析第{i+1}/3个章节", progress=35 + i * 15)
            await asyncio.sleep(2)
            
            await logger.debug(f"章节{i+1}分析详情", metadata={
                "chapter": f"第{i+1}章",
                "word_count": 300 + i * 100,
                "issues_found": i
            })
            
            if i == 1:
                await logger.warning(f"章节{i+1}发现潜在问题", metadata={
                    "type": "语法错误",
                    "location": f"第{i+1}章第2段"
                })
        
        await logger.info("内容分析完成", progress=80)
        await asyncio.sleep(1)
        
        # 报告生成阶段
        await logger.set_stage(TaskStage.GENERATING, "生成测试报告", 85)
        await logger.debug("正在整理检测结果")
        await asyncio.sleep(1)
        
        await logger.progress(90, "正在创建报告文件...")
        await asyncio.sleep(1)
        
        await logger.progress(95, "保存报告...")
        await asyncio.sleep(1)
        
        # 完成任务
        await logger.set_stage(TaskStage.COMPLETE, "任务处理完成", 100)
        await logger.info("任务成功完成", metadata={
            "total_time": "15秒",
            "issues_found": 2,
            "chapters_analyzed": 3
        })
        
        # 更新数据库
        task.status = 'completed'
        task.progress = 100
        db.commit()
        
        print(f"任务{task_id}处理完成")
        
    except Exception as e:
        await logger.error(f"任务处理失败: {str(e)}", stage=TaskStage.ERROR)
        task.status = 'failed'
        task.error_message = str(e)
        db.commit()
    finally:
        db.close()
        await TaskLoggerFactory.close_logger(str(task_id))


async def main():
    """主函数"""
    # 使用最新创建的任务ID
    task_id = 31
    
    print(f"开始模拟任务处理，任务ID: {task_id}")
    print("请在浏览器中访问 http://localhost:3002/task/31 查看实时日志")
    print("-" * 60)
    
    await simulate_task_processing(task_id)
    
    print("-" * 60)
    print("测试完成！")


if __name__ == "__main__":
    asyncio.run(main())