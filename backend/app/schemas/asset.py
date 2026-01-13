from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AssetResponse(BaseModel):
    """에셋 응답"""
    id: str
    provider: str
    asset_type: str
    source_url: str
    thumbnail_url: str
    title: Optional[str]
    license: Optional[str]
    meta: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class BlockAssetResponse(BaseModel):
    """블록-에셋 연결 응답 (점수, 대표 여부 포함)"""
    id: str
    block_id: str
    asset_id: str
    score: float
    is_primary: bool
    chosen_by: str
    asset: AssetResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
