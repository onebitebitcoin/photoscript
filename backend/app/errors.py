"""
커스텀 예외 클래스

Unix 철학 원칙 적용:
- 원칙 8 (견고성): 명시적 에러 타입, 적절한 예외 처리
- 원칙 12 (복구): Fail-fast, 명확한 에러 전파
"""


class PhotoScriptError(Exception):
    """PhotoScript 기본 예외"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Asset 관련 예외
# =============================================================================


class AssetError(PhotoScriptError):
    """에셋 관련 기본 예외"""
    pass


class AssetNotFoundError(AssetError):
    """에셋을 찾을 수 없음"""
    pass


class AssetSaveError(AssetError):
    """에셋 저장 실패"""
    pass


class AssetSearchError(AssetError):
    """에셋 검색 실패"""
    pass


# =============================================================================
# Block 관련 예외
# =============================================================================


class BlockError(PhotoScriptError):
    """블록 관련 기본 예외"""
    pass


class BlockNotFoundError(BlockError):
    """블록을 찾을 수 없음"""
    pass


class BlockValidationError(BlockError):
    """블록 유효성 검증 실패"""
    pass


class BlockMergeError(BlockError):
    """블록 합치기 실패"""
    pass


class BlockSplitError(BlockError):
    """블록 나누기 실패"""
    pass


# =============================================================================
# Project 관련 예외
# =============================================================================


class ProjectError(PhotoScriptError):
    """프로젝트 관련 기본 예외"""
    pass


class ProjectNotFoundError(ProjectError):
    """프로젝트를 찾을 수 없음"""
    pass


class ProjectValidationError(ProjectError):
    """프로젝트 유효성 검증 실패"""
    pass


# =============================================================================
# External Service 관련 예외
# =============================================================================


class ExternalServiceError(PhotoScriptError):
    """외부 서비스 관련 기본 예외"""
    pass


class PexelsAPIError(ExternalServiceError):
    """Pexels API 오류"""
    pass


class LLMServiceError(ExternalServiceError):
    """LLM 서비스 오류 (OpenAI 등)"""
    pass
