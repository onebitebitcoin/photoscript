from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class ChosenBy:
    """선택 주체 상수"""
    AUTO = "AUTO"
    USER = "USER"


class BlockAsset(Base):
    """블록-에셋 연결 모델"""
    __tablename__ = "block_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    block_id = Column(String, ForeignKey("blocks.id"), nullable=False)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    score = Column(Float, default=0.0)
    is_primary = Column(Boolean, default=False)
    chosen_by = Column(String(20), default=ChosenBy.AUTO)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    block = relationship("Block", back_populates="block_assets")
    asset = relationship("Asset")

    def __repr__(self):
        return f"<BlockAsset(block_id={self.block_id}, asset_id={self.asset_id}, is_primary={self.is_primary})>"
