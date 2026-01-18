"""
의존성 주입 설정

Unix 철학 원칙 적용:
- 원칙 1 (모듈성): 서비스 계층 분리
- 원칙 4 (분리): Router(인터페이스) / Service(정책) / Model(엔진)
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import auth_service
from app.models.user import User

# =============================================================================
# 인증 의존성
# =============================================================================

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 인증된 사용자 반환"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "인증이 필요합니다", "error": "missing_token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = auth_service.decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "유효하지 않은 토큰입니다", "error": "invalid_token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "유효하지 않은 토큰입니다", "error": "invalid_token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "사용자를 찾을 수 없습니다", "error": "user_not_found"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "비활성화된 계정입니다", "error": "inactive_user"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """현재 인증된 사용자 반환 (선택적)"""
    if not credentials:
        return None

    payload = auth_service.decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        return None

    return user


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
