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


class BlockUpdate(BaseModel):
    """블록 수정 요청"""
    text: Optional[str] = Field(None, min_length=1)
    keywords: Optional[List[str]] = None


class BlockSplitRequest(BaseModel):
    """블록 나누기 요청"""
    split_position: int = Field(..., ge=1, description="나눌 위치 (문자 인덱스)")


class BlockMergeRequest(BaseModel):
    """블록 합치기 요청"""
    block_ids: List[str] = Field(..., min_length=2, max_length=5, description="합칠 블록 ID 목록")


class BlockSearchRequest(BaseModel):
    """키워드 검색 요청"""
    keyword: str = Field(..., min_length=1, max_length=100, description="검색할 키워드")
    video_priority: Optional[bool] = Field(True, description="영상 우선 검색 여부")


class BlockCreate(BaseModel):
    """새 블록 생성 요청"""
    text: str = Field(default="", description="블록 텍스트")
    keywords: Optional[List[str]] = Field(default=[], description="키워드 목록")
    insert_at: int = Field(..., ge=0, description="삽입할 인덱스 위치")


class KeywordExtractRequest(BaseModel):
    """키워드 추출 요청"""
    max_keywords: int = Field(default=5, ge=1, le=10, description="추출할 최대 키워드 수")
