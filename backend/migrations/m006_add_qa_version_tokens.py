"""
마이그레이션: qa_versions 테이블에 input_tokens, output_tokens 컬럼 추가

실행 방법:
    cd backend
    python -m migrations.m006_add_qa_version_tokens
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
        # 1. input_tokens 컬럼이 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'qa_versions' AND column_name = 'input_tokens'
        """))

        if result.fetchone():
            logger.info("input_tokens 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: qa_versions에 input_tokens, output_tokens 추가")

        # 2. input_tokens, output_tokens 컬럼 추가
        db.execute(text("""
            ALTER TABLE qa_versions
            ADD COLUMN input_tokens INTEGER,
            ADD COLUMN output_tokens INTEGER
        """))
        db.commit()
        logger.info("input_tokens, output_tokens 컬럼 추가 완료")

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
        # SQLite는 PRAGMA를 사용하여 컬럼 존재 여부 확인
        result = db.execute(text("""
            PRAGMA table_info(qa_versions)
        """))

        columns = [row[1] for row in result.fetchall()]
        if 'input_tokens' in columns:
            logger.info("input_tokens 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): qa_versions에 input_tokens, output_tokens 추가")

        # input_tokens 컬럼 추가
        db.execute(text("""
            ALTER TABLE qa_versions
            ADD COLUMN input_tokens INTEGER
        """))

        # output_tokens 컬럼 추가
        db.execute(text("""
            ALTER TABLE qa_versions
            ADD COLUMN output_tokens INTEGER
        """))

        db.commit()
        logger.info("input_tokens, output_tokens 컬럼 추가 완료")

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
