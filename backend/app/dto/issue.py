"""
问题相关的DTO
"""
from pydantic import BaseModel
from typing import Optional


class IssueResponse(BaseModel):
    """问题响应"""
    id: int
    issue_type: str
    description: str
    location: Optional[str] = None
    severity: str
    confidence: Optional[float] = None
    suggestion: Optional[str] = None
    original_text: Optional[str] = None
    user_impact: Optional[str] = None
    reasoning: Optional[str] = None
    context: Optional[str] = None
    feedback_type: Optional[str] = None
    feedback_comment: Optional[str] = None
    
    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """反馈请求"""
    feedback_type: str  # accept, reject
    comment: Optional[str] = None