import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Text

from app.database import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nickname = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # QA 커스텀 설정
    qa_custom_guideline = Column(Text, nullable=True)  # 커스텀 가이드라인 (없으면 기본값 사용)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
