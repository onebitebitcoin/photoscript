from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BlockResponse(BaseModel):
    """블록 응답"""
    id: str
    project_id: str
    index: int
    text: str
    keywords: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetInBlock(BaseModel):
    """블록 내 에셋 정보"""
    id: str
    asset_type: str
    source_url: str
    thumbnail_url: str
    title: Optional[str]
    provider: str

    class Config:
        from_attributes = True


class BlockWithAssetResponse(BaseModel):
    """블록 응답 (대표 에셋 포함)"""
    id: str
    project_id: str
    index: int
    text: str
    keywords: Optional[List[str]]
    status: str
    primary_asset: Optional[AssetInBlock] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SetPrimaryRequest(BaseModel):
    """대표 에셋 선택 요청"""
    asset_id: str = Field(..., min_length=1)
