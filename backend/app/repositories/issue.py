"""
问题数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Issue


class IssueRepository:
    """问题仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> Issue:
        """创建问题"""
        issue = Issue(**kwargs)
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        return issue
    
    def bulk_create(self, issues_data: List[dict]) -> List[Issue]:
        """批量创建问题"""
        issues = [Issue(**data) for data in issues_data]
        self.db.add_all(issues)
        self.db.commit()
        return issues
    
    def get_by_id(self, issue_id: int) -> Optional[Issue]:
        """根据ID获取问题"""
        return self.db.query(Issue).filter(Issue.id == issue_id).first()
    
    def get_by_task_id(self, task_id: int) -> List[Issue]:
        """获取任务的所有问题"""
        return self.db.query(Issue).filter(Issue.task_id == task_id).all()
    
    def update_feedback(self, issue_id: int, feedback_type: str, comment: Optional[str] = None) -> Optional[Issue]:
        """更新问题反馈"""
        issue = self.get_by_id(issue_id)
        if issue:
            issue.feedback_type = feedback_type
            issue.feedback_comment = comment
            self.db.commit()
            self.db.refresh(issue)
        return issue
    
    def delete_by_task_id(self, task_id: int):
        """删除任务的所有问题"""
        self.db.query(Issue).filter(Issue.task_id == task_id).delete()
        self.db.commit()