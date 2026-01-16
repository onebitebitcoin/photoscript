"""
의존성 주입 설정

Unix 철학 원칙 적용:
- 원칙 1 (모듈성): 서비스 계층 분리
- 원칙 4 (분리): Router(인터페이스) / Service(정책) / Model(엔진)
"""

from functools import lru_cache
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings


# =============================================================================
# 서비스 의존성
# =============================================================================


def get_asset_service():
    """AssetService 의존성"""
    from app.services.asset_service import AssetService
    return AssetService()


def get_block_service():
    """BlockService 의존성"""
    from app.services.block_service import BlockService
    return BlockService()


def get_project_service():
    """ProjectService 의존성"""
    from app.services.project_service import ProjectService
    return ProjectService()


# =============================================================================
# 외부 클라이언트 의존성
# =============================================================================


def get_pexels_client():
    """PexelsClient 의존성"""
    from app.services.pexels_client import PexelsClient
    return PexelsClient()
