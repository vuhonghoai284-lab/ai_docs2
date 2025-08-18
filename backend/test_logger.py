"""
测试任务日志系统
"""
import asyncio
import time
from utils.task_logger import TaskLoggerFactory, TaskStage, LogLevel


async def test_task_logger():
    """测试任务日志功能"""
    task_id = "test_task_001"
    
    # 获取日志管理器
    logger = await TaskLoggerFactory.get_logger(task_id, "test_module")
    
    print(f"开始测试任务日志系统，任务ID: {task_id}")
    
    # 模拟任务执行流程
    await logger.info("开始测试任务", stage=TaskStage.INIT, progress=0)
    await asyncio.sleep(1)
    
    # 模拟文档解析阶段
    await logger.set_stage(TaskStage.PARSING, "开始文档解析", 10)
    await logger.debug("正在读取文件内容", metadata={"file_name": "test.pdf", "file_size": 1024000})
    await asyncio.sleep(2)
    
    await logger.progress(25, "文档解析进行中...")
    await asyncio.sleep(1)
    
    await logger.info("文档解析完成", progress=30)
    
    # 模拟内容分析阶段
    await logger.set_stage(TaskStage.ANALYZING, "开始AI内容分析", 35)
    
    # 模拟多个分析步骤
    for i in range(5):
        await logger.info(f"处理第{i+1}/5个章节", progress=35 + i * 10)
        await logger.debug(f"章节{i+1}分析详情", metadata={
            "chapter": f"第{i+1}章",
            "word_count": 500 + i * 100,
            "issues_found": i % 3
        })
        await asyncio.sleep(1)
        
        # 偶尔模拟警告
        if i == 2:
            await logger.warning("检测到可能的语法错误", metadata={"location": f"第{i+1}章第3段"})
    
    await logger.info("内容分析完成", progress=80)
    
    # 模拟报告生成阶段
    await logger.set_stage(TaskStage.GENERATING, "生成测试报告", 85)
    await logger.debug("正在格式化检测结果")
    await asyncio.sleep(1)
    
    await logger.progress(90, "正在创建Excel报告...")
    await asyncio.sleep(1)
    
    await logger.progress(95, "正在保存报告文件...")
    await asyncio.sleep(1)
    
    # 完成任务
    await logger.set_stage(TaskStage.COMPLETE, "任务执行完成", 100)
    await logger.info("测试任务成功完成", metadata={
        "total_time": "10秒",
        "issues_found": 3,
        "report_file": "test_report.xlsx"
    })
    
    # 获取历史日志
    history = logger.get_history()
    print(f"\n历史日志条数: {len(history)}")
    
    # 获取当前状态
    status = logger.get_current_status()
    print(f"当前状态: {status}")
    
    # 清理
    await TaskLoggerFactory.close_logger(task_id)
    print("\n测试完成！")


async def test_error_scenario():
    """测试错误场景"""
    task_id = "test_task_error"
    
    logger = await TaskLoggerFactory.get_logger(task_id, "error_test")
    
    print(f"\n开始测试错误场景，任务ID: {task_id}")
    
    await logger.info("开始任务", stage=TaskStage.INIT, progress=0)
    await logger.set_stage(TaskStage.PARSING, "开始文件处理", 10)
    await logger.progress(20, "正在读取文件...")
    
    # 模拟错误
    await logger.error("文件读取失败：文件不存在", stage=TaskStage.ERROR, metadata={
        "error_code": "FILE_NOT_FOUND",
        "file_path": "/path/to/nonexistent.pdf"
    })
    
    await logger.info("任务因错误终止")
    
    await TaskLoggerFactory.close_logger(task_id)
    print("错误场景测试完成！")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("任务日志系统测试")
    print("=" * 60)
    
    # 测试正常流程
    await test_task_logger()
    
    # 测试错误场景
    await test_error_scenario()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())