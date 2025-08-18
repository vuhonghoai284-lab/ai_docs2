"""报告生成模块"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from sqlalchemy.orm import Session
from database import Task, Issue
import os

def generate_report(task_id: int, db: Session) -> str:
    """生成Excel报告"""
    # 获取任务和问题
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"任务不存在: {task_id}")
    
    issues = db.query(Issue).filter(Issue.task_id == task_id).all()
    
    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "问题汇总"
    
    # 设置表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    
    # 写入表头
    headers = ['序号', '问题类型', '问题描述', '所在位置', '严重程度', '改进建议', '用户反馈', '用户评价']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    
    # 写入数据
    for i, issue in enumerate(issues, 2):
        ws.cell(row=i, column=1, value=i-1)
        ws.cell(row=i, column=2, value=issue.issue_type)
        ws.cell(row=i, column=3, value=issue.description)
        ws.cell(row=i, column=4, value=issue.location)
        ws.cell(row=i, column=5, value=issue.severity)
        ws.cell(row=i, column=6, value=issue.suggestion)
        ws.cell(row=i, column=7, value=issue.feedback_type or '未反馈')
        ws.cell(row=i, column=8, value=issue.feedback_comment or '')
    
    # 调整列宽
    column_widths = [8, 12, 40, 20, 12, 30, 12, 30]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + i)].width = width
    
    # 添加统计信息
    stats_row = len(issues) + 3
    ws.cell(row=stats_row, column=1, value='统计信息').font = Font(bold=True)
    ws.cell(row=stats_row + 1, column=1, value='总问题数')
    ws.cell(row=stats_row + 1, column=2, value=len(issues))
    
    accepted = len([i for i in issues if i.feedback_type == 'accept'])
    rejected = len([i for i in issues if i.feedback_type == 'reject'])
    
    ws.cell(row=stats_row + 2, column=1, value='已接受')
    ws.cell(row=stats_row + 2, column=2, value=accepted)
    ws.cell(row=stats_row + 3, column=1, value='已拒绝')
    ws.cell(row=stats_row + 3, column=2, value=rejected)
    ws.cell(row=stats_row + 4, column=1, value='未反馈')
    ws.cell(row=stats_row + 4, column=2, value=len(issues) - accepted - rejected)
    
    # 保存文件
    os.makedirs("./data/reports", exist_ok=True)
    file_name = f"{task_id}_{task.file_name.replace('.', '_')}_report.xlsx"
    file_path = f"./data/reports/{file_name}"
    wb.save(file_path)
    
    return file_path