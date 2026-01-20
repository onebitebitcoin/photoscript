"""
QAVersionService - QA 버전 관리 서비스

QA 검증 결과 버전을 관리합니다.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import QAVersion
from app.utils.logger import logger


class QAVersionService:
    """QA 버전 관리 서비스"""

    def get_latest_version(self, db: Session, project_id: str) -> Optional[QAVersion]:
        """
        최신 버전 조회

        Args:
            db: DB 세션
            project_id: 프로젝트 ID

        Returns:
            최신 QAVersion 또는 None
        """
        return db.query(QAVersion).filter(
            QAVersion.project_id == project_id
        ).order_by(QAVersion.created_at.desc()).first()

    def get_versions(self, db: Session, project_id: str) -> List[QAVersion]:
        """
        전체 버전 목록 조회 (최신순)

        Args:
            db: DB 세션
            project_id: 프로젝트 ID

        Returns:
            QAVersion 리스트
        """
        return db.query(QAVersion).filter(
            QAVersion.project_id == project_id
        ).order_by(QAVersion.created_at.desc()).all()

    def get_version_by_id(self, db: Session, version_id: str) -> Optional[QAVersion]:
        """
        특정 버전 조회

        Args:
            db: DB 세션
            version_id: 버전 ID

        Returns:
            QAVersion 또는 None
        """
        return db.query(QAVersion).filter(QAVersion.id == version_id).first()

    def create_version(
        self,
        db: Session,
        project_id: str,
        corrected_script: str,
        model: str,
        version_name: Optional[str] = None,
        memo: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> QAVersion:
        """
        버전 생성 (version_number 자동 증가)

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            corrected_script: 보정된 스크립트
            model: 사용된 LLM 모델
            version_name: 버전 이름 (선택)
            memo: 메모 (선택)
            input_tokens: 입력 토큰 수 (선택)
            output_tokens: 출력 토큰 수 (선택)

        Returns:
            생성된 QAVersion
        """
        # 현재 프로젝트의 최대 버전 번호 조회
        max_version = db.query(func.max(QAVersion.version_number)).filter(
            QAVersion.project_id == project_id
        ).scalar() or 0

        # 새 버전 번호
        new_version_number = max_version + 1

        version = QAVersion(
            project_id=project_id,
            version_number=new_version_number,
            version_name=version_name,
            memo=memo,
            corrected_script=corrected_script,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        db.add(version)
        db.commit()
        db.refresh(version)

        logger.info(f"QA 버전 생성: project_id={project_id}, version={new_version_number}")
        return version

    def update_version(
        self,
        db: Session,
        version_id: str,
        version_name: Optional[str] = None,
        memo: Optional[str] = None
    ) -> Optional[QAVersion]:
        """
        메타데이터 수정 (version_name, memo)

        Args:
            db: DB 세션
            version_id: 버전 ID
            version_name: 버전 이름
            memo: 메모

        Returns:
            수정된 QAVersion 또는 None
        """
        version = self.get_version_by_id(db, version_id)
        if not version:
            return None

        if version_name is not None:
            version.version_name = version_name
        if memo is not None:
            version.memo = memo

        db.commit()
        db.refresh(version)

        logger.info(f"QA 버전 수정: id={version_id}")
        return version

    def delete_version(self, db: Session, version_id: str) -> bool:
        """
        버전 삭제

        Args:
            db: DB 세션
            version_id: 버전 ID

        Returns:
            삭제 성공 여부
        """
        version = self.get_version_by_id(db, version_id)
        if not version:
            return False

        db.delete(version)
        db.commit()

        logger.info(f"QA 버전 삭제: id={version_id}")
        return True

    def get_latest_corrected_script(self, db: Session, project_id: str) -> Optional[str]:
        """
        최신 보정 스크립트 조회

        Args:
            db: DB 세션
            project_id: 프로젝트 ID

        Returns:
            최신 보정 스크립트 또는 None
        """
        latest = self.get_latest_version(db, project_id)
        return latest.corrected_script if latest else None
