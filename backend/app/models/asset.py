from sqlalchemy import Column, String, Text, DateTime, JSON
from datetime import datetime
from uuid import uuid4

from app.database import Base


class AssetType:
    """에셋 타입 상수"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class Asset(Base):
    """에셋 모델 - 이미지/영상 후보"""
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    provider = Column(String(50), nullable=False)  # pexels, unsplash 등
    asset_type = Column(String(20), nullable=False)  # IMAGE, VIDEO
    source_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    license = Column(String(100), nullable=True)
    meta = Column(JSON, nullable=True)  # 추가 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Asset(id={self.id}, type={self.asset_type}, provider={self.provider})>"
