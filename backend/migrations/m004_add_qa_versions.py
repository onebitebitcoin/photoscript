"""
마이그레이션: qa_versions 테이블 생성

실행 방법:
    cd backend
    python -m migrations.m004_add_qa_versions
"""

import sys
import os

# 상위 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.utils.logger import logger


def run_migration():
    """마이그레이션 실행 (PostgreSQL)"""
    db = SessionLocal()

    try:
        # 1. qa_versions 테이블이 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'qa_versions'
        """))

        if result.fetchone():
            logger.info("qa_versions 테이블이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: qa_versions 테이블 생성")

        # 2. qa_versions 테이블 생성
        db.execute(text("""
            CREATE TABLE qa_versions (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL,
                version_number INTEGER NOT NULL,
                version_name VARCHAR(255),
                memo TEXT,
                corrected_script TEXT NOT NULL,
                model VARCHAR(50) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """))
        db.commit()
        logger.info("qa_versions 테이블 생성 완료")

        # 3. 인덱스 생성
        db.execute(text("""
            CREATE INDEX ix_qa_versions_project_id ON qa_versions (project_id)
        """))
        db.execute(text("""
            CREATE INDEX ix_qa_versions_created_at ON qa_versions (created_at)
        """))
        db.commit()
        logger.info("인덱스 생성 완료")

        logger.info("마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


def run_migration_sqlite():
    """SQLite용 마이그레이션"""
    db = SessionLocal()

    try:
        # SQLite는 PRAGMA를 사용하여 테이블 존재 여부 확인
        result = db.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='qa_versions'
        """))

        if result.fetchone():
            logger.info("qa_versions 테이블이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): qa_versions 테이블 생성")

        # qa_versions 테이블 생성
        db.execute(text("""
            CREATE TABLE qa_versions (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL,
                version_number INTEGER NOT NULL,
                version_name VARCHAR(255),
                memo TEXT,
                corrected_script TEXT NOT NULL,
                model VARCHAR(50) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """))
        db.commit()
        logger.info("qa_versions 테이블 생성 완료")

        # 인덱스 생성
        db.execute(text("""
            CREATE INDEX ix_qa_versions_project_id ON qa_versions (project_id)
        """))
        db.execute(text("""
            CREATE INDEX ix_qa_versions_created_at ON qa_versions (created_at)
        """))
        db.commit()
        logger.info("인덱스 생성 완료")

        logger.info("마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    from app.config import get_settings
    settings = get_settings()

    if "sqlite" in settings.database_url:
        run_migration_sqlite()
    else:
        run_migration()
