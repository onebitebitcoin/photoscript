from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON, Index
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
    """블록 모델 - 스크립트를 의미 단위로 나눈 조각

    순서 관리: Fractional Indexing 방식
    - order 필드를 Float로 사용하여 중간 삽입 시 다른 블록 수정 불필요
    - 예: 1.0과 2.0 사이에 삽입 → 1.5
    """
    __tablename__ = "blocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    order = Column(Float, nullable=False, default=0.0)  # Fractional indexing
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

    # Indexes (UniqueConstraint 제거 - Float은 중간값 사용으로 충돌 없음)
    __table_args__ = (
        Index('ix_blocks_project_order', 'project_id', 'order'),
    )

    def __repr__(self):
        return f"<Block(id={self.id}, order={self.order}, status={self.status})>"
