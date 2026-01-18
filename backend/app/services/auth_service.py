from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.utils.logger import logger

settings = get_settings()

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        return None


def get_user_by_nickname(db: Session, nickname: str) -> Optional[User]:
    """닉네임으로 사용자 조회"""
    return db.query(User).filter(User.nickname == nickname).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """ID로 사용자 조회"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, nickname: str, password: str) -> User:
    """새 사용자 생성"""
    password_hash = get_password_hash(password)
    user = User(nickname=nickname, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user created: {nickname}")
    return user


def authenticate_user(db: Session, nickname: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = get_user_by_nickname(db, nickname)
    if not user:
        logger.debug(f"User not found: {nickname}")
        return None
    if not verify_password(password, user.password_hash):
        logger.debug(f"Invalid password for user: {nickname}")
        return None
    if not user.is_active:
        logger.debug(f"User is inactive: {nickname}")
        return None
    logger.info(f"User authenticated: {nickname}")
    return user


def get_token_expires_in() -> int:
    """토큰 만료 시간 (초)"""
    return ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
