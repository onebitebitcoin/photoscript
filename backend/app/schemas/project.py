from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    """프로젝트 생성 요청"""
    script_raw: str = Field(..., min_length=1, max_length=50000)
    title: Optional[str] = Field(None, max_length=255)


class ProjectResponse(BaseModel):
    """프로젝트 기본 응답"""
    id: str
    title: Optional[str]
    script_raw: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlockSummary(BaseModel):
    """블록 요약 (프로젝트 상세 조회용)"""
    id: str
    order: float
    text: str
    keywords: Optional[List[str]]
    status: str
    primary_asset: Optional["AssetSummary"] = None

    class Config:
        from_attributes = True


class AssetSummary(BaseModel):
    """에셋 요약"""
    id: str
    asset_type: str
    thumbnail_url: str
    source_url: str

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    """프로젝트 상세 응답 (블록 + 대표 에셋 포함)"""
    id: str
    title: Optional[str]
    script_raw: str
    created_at: datetime
    updated_at: datetime
    blocks: List[BlockSummary] = []

    class Config:
        from_attributes = True


class GenerateOptions(BaseModel):
    """Generate 옵션"""
    max_block_length: Optional[int] = Field(500, ge=100, le=2000)
    max_candidates_per_block: Optional[int] = Field(10, ge=1, le=20)


class GenerateResponse(BaseModel):
    """Generate 응답"""
    status: str
    message: str
    blocks_count: int


class SplitOptions(BaseModel):
    """분할 옵션"""
    max_keywords: Optional[int] = Field(5, ge=1, le=10)


class SplitResponse(BaseModel):
    """분할 응답"""
    status: str
    message: str
    blocks_count: int
    blocks: List[BlockSummary] = []


class MatchOptions(BaseModel):
    """매칭 옵션"""
    max_candidates_per_block: Optional[int] = Field(10, ge=1, le=20)
    video_priority: Optional[bool] = Field(True, description="영상 우선 검색 여부")


class MatchResponse(BaseModel):
    """매칭 응답"""
    status: str
    message: str
    blocks_count: int


# Forward reference 업데이트
BlockSummary.model_rebuild()
