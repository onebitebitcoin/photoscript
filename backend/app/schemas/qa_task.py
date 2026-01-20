"""
QA Task 스키마 (비동기 처리)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .project import QAScriptResponse


class QATaskCreate(BaseModel):
    """QA 작업 생성 요청"""
    additional_prompt: Optional[str] = Field(None, description="추가 프롬프트")


class QATaskResponse(BaseModel):
    """QA 작업 응답"""
    id: str
    project_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    result: Optional[QAScriptResponse] = None  # 완료 시만
    error_message: Optional[str] = None  # 실패 시만
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
