"""
QA 작업 모델 (비동기 처리)
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class QATask(Base):
    """QA 검증 비동기 작업"""
    __tablename__ = "qa_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # 작업 상태
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    progress = Column(Integer, nullable=False, default=0)  # 0-100

    # 결과 (완료 시)
    result_json = Column(Text, nullable=True)  # JSON 직렬화된 QA 결과

    # 에러 (실패 시)
    error_message = Column(Text, nullable=True)

    # 추가 옵션
    additional_prompt = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # 관계
    project = relationship("Project", back_populates="qa_tasks")
