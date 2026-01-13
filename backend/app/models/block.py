from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class BlockStatus:
    """블록 상태 상수"""
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    NO_RESULT = "NO_RESULT"
    CUSTOM = "CUSTOM"


class Block(Base):
    """블록 모델 - 스크립트를 의미 단위로 나눈 조각"""
    __tablename__ = "blocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # ["keyword1", "keyword2", ...]
    status = Column(String(20), default=BlockStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="blocks")
    block_assets = relationship(
        "BlockAsset",
        back_populates="block",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Block(id={self.id}, index={self.index}, status={self.status})>"
