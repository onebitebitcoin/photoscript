from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    CheckNicknameRequest,
    CheckNicknameResponse,
    AuthResponse,
    UserResponse,
)
from app.services import auth_service
from app.utils.logger import logger

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """회원가입"""
    logger.info(f"Register attempt: {request.nickname}")

    # 닉네임 중복 체크
    existing_user = auth_service.get_user_by_nickname(db, request.nickname)
    if existing_user:
        logger.debug(f"Nickname already exists: {request.nickname}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "이미 사용 중인 닉네임입니다", "error": "nickname_exists"}
        )

    # 사용자 생성
    user = auth_service.create_user(db, request.nickname, request.password)

    # 토큰 생성
    access_token = auth_service.create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=auth_service.ACCESS_TOKEN_EXPIRE_DAYS)
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=auth_service.get_token_expires_in()
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """로그인"""
    logger.info(f"Login attempt: {request.nickname}")

    user = auth_service.authenticate_user(db, request.nickname, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "닉네임 또는 비밀번호가 올바르지 않습니다", "error": "invalid_credentials"}
        )

    # 토큰 생성
    access_token = auth_service.create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=auth_service.ACCESS_TOKEN_EXPIRE_DAYS)
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=auth_service.get_token_expires_in()
    )


@router.post("/check-nickname", response_model=CheckNicknameResponse)
async def check_nickname(
    request: CheckNicknameRequest,
    db: Session = Depends(get_db)
):
    """닉네임 중복체크"""
    logger.debug(f"Checking nickname: {request.nickname}")

    existing_user = auth_service.get_user_by_nickname(db, request.nickname)
    if existing_user:
        return CheckNicknameResponse(
            available=False,
            message="이미 사용 중인 닉네임입니다"
        )

    return CheckNicknameResponse(
        available=True,
        message="사용 가능한 닉네임입니다"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """현재 사용자 정보 조회"""
    logger.debug(f"Get me: {current_user.nickname}")
    return UserResponse.model_validate(current_user)
