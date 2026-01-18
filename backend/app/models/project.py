from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class Project(Base):
    """프로젝트 모델 - 하나의 유튜브 영상 제작 단위"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    script_raw = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # User relationship
    user = relationship("User", backref="projects")

    # Relationships
    blocks = relationship(
        "Block",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Block.index"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, title={self.title})>"
