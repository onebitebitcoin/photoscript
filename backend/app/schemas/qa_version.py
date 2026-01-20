from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QAVersionResponse(BaseModel):
    """전체 버전 정보 (스크립트 포함)"""
    id: str
    version_number: int
    version_name: Optional[str]
    memo: Optional[str]
    corrected_script: str
    model: str
    created_at: datetime

    class Config:
        from_attributes = True


class QAVersionListItem(BaseModel):
    """목록용 (스크립트 제외)"""
    id: str
    version_number: int
    version_name: Optional[str]
    memo: Optional[str]
    model: str
    created_at: datetime

    class Config:
        from_attributes = True


class QAVersionUpdate(BaseModel):
    """수정 요청"""
    version_name: Optional[str] = Field(None, max_length=255)
    memo: Optional[str] = Field(None, max_length=5000)


class QAVersionCreate(BaseModel):
    """버전 생성 요청 (내부용)"""
    project_id: str
    corrected_script: str
    model: str
    version_name: Optional[str] = None
    memo: Optional[str] = None
