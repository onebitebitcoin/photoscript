from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from app.database import Base


class QAVersion(Base):
    """QA 검증 버전 모델 - 보정된 스크립트 버전 관리"""
    __tablename__ = "qa_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # 버전 메타데이터
    version_number = Column(Integer, nullable=False)  # 자동 증가 (1, 2, 3, ...)
    version_name = Column(String(255), nullable=True)  # 사용자 정의 이름
    memo = Column(Text, nullable=True)  # 메모

    # 저장 데이터
    corrected_script = Column(Text, nullable=False)  # 보정된 스크립트만
    model = Column(String(50), nullable=False)  # 사용된 LLM 모델
    input_tokens = Column(Integer, nullable=True)  # 입력 토큰 수
    output_tokens = Column(Integer, nullable=True)  # 출력 토큰 수

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    project = relationship("Project", backref="qa_versions")

    def __repr__(self):
        return f"<QAVersion(id={self.id}, project_id={self.project_id}, version={self.version_number})>"
