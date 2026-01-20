from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """회원가입 요청"""
    nickname: str = Field(..., min_length=2, max_length=50, description="닉네임 (2-50자)")
    password: str = Field(..., min_length=4, max_length=100, description="비밀번호 (4-100자)")


class UserLoginRequest(BaseModel):
    """로그인 요청"""
    nickname: str = Field(..., description="닉네임")
    password: str = Field(..., description="비밀번호")


class CheckNicknameRequest(BaseModel):
    """닉네임 중복체크 요청"""
    nickname: str = Field(..., min_length=2, max_length=50, description="닉네임")


class CheckNicknameResponse(BaseModel):
    """닉네임 중복체크 응답"""
    available: bool
    message: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: str
    nickname: str
    is_active: bool
    qa_custom_guideline: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """인증 응답 (로그인/회원가입)"""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserSettingsUpdate(BaseModel):
    """사용자 설정 업데이트 요청"""
    qa_custom_guideline: Optional[str] = Field(None, max_length=10000, description="커스텀 QA 가이드라인 (최대 10,000자)")


class UserSettingsResponse(BaseModel):
    """사용자 설정 응답"""
    qa_custom_guideline: Optional[str]

    class Config:
        from_attributes = True
