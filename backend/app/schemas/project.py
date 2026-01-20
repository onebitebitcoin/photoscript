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


class QAScriptRequest(BaseModel):
    """QA 검증 요청 (현재는 project_id만으로 충분)"""
    pass


class DiagnosisSummary(BaseModel):
    """진단 요약"""
    problems: List[str] = Field(..., min_length=3, max_length=3, description="문제점 3개")
    strengths: List[str] = Field(..., min_length=2, max_length=2, description="장점 2개")


class StructureCheck(BaseModel):
    """5블록 구조 점검"""
    has_hook: bool = Field(..., description="Hook 블록 존재 여부")
    has_context: bool = Field(..., description="맥락 블록 존재 여부")
    has_promise_outline: bool = Field(..., description="Promise+Outline 블록 존재 여부")
    has_body: bool = Field(..., description="Body 블록 존재 여부")
    has_wrapup: bool = Field(..., description="Wrap-up 블록 존재 여부")
    overall_pass: bool = Field(..., description="전체 구조 통과 여부")
    comments: Optional[str] = Field(None, description="구조 관련 코멘트")


class ChangeLogItem(BaseModel):
    """변경 로그 항목"""
    block_index: int = Field(..., ge=0, description="블록 인덱스 (0부터 시작)")
    change_type: str = Field(..., description="변경 유형: 수정, 추가, 삭제")
    description: str = Field(..., description="변경 내용 설명")


class QAScriptResponse(BaseModel):
    """QA 검증 응답"""
    diagnosis: DiagnosisSummary
    structure_check: StructureCheck
    corrected_script: str = Field(..., description="보정된 전체 스크립트")
    change_logs: List[ChangeLogItem] = Field(default_factory=list, description="블록별 변경 내역")
    model: str = Field(..., description="사용된 LLM 모델")
    created_at: datetime = Field(default_factory=datetime.now, description="검증 시각")


# Forward reference 업데이트
BlockSummary.model_rebuild()
