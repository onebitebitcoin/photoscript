"""
마이그레이션: users 테이블에 qa_custom_guideline 컬럼 추가

실행 방법:
    cd backend
    python -m migrations.m005_add_user_qa_settings
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
        # 1. qa_custom_guideline 컬럼이 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'qa_custom_guideline'
        """))

        if result.fetchone():
            logger.info("qa_custom_guideline 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: users.qa_custom_guideline 추가")

        # 2. qa_custom_guideline 컬럼 추가
        db.execute(text("""
            ALTER TABLE users
            ADD COLUMN qa_custom_guideline TEXT
        """))
        db.commit()
        logger.info("qa_custom_guideline 컬럼 추가 완료")

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
            PRAGMA table_info(users)
        """))

        columns = [row[1] for row in result.fetchall()]
        if 'qa_custom_guideline' in columns:
            logger.info("qa_custom_guideline 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): users.qa_custom_guideline 추가")

        # qa_custom_guideline 컬럼 추가
        db.execute(text("""
            ALTER TABLE users
            ADD COLUMN qa_custom_guideline TEXT
        """))
        db.commit()
        logger.info("qa_custom_guideline 컬럼 추가 완료")

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
