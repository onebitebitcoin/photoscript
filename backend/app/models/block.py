from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class BlockStatus:
    """블록 상태 상수"""
    DRAFT = "DRAFT"          # 분할 완료, 매칭 대기 (편집 가능)
    PENDING = "PENDING"      # 매칭 진행 중
    MATCHED = "MATCHED"      # 자동 매칭 완료
    NO_RESULT = "NO_RESULT"  # 검색 결과 없음
    CUSTOM = "CUSTOM"        # 사용자 선택


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

    # Constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'index', name='uq_project_block_index'),
    )

    def __repr__(self):
        return f"<Block(id={self.id}, index={self.index}, status={self.status})>"
