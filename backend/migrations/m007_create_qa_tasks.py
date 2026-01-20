"""
마이그레이션 m007: qa_tasks 테이블 생성
"""
from sqlalchemy import text
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


def run_migration_sqlite():
    """SQLite용 마이그레이션"""
    db = SessionLocal()

    try:
        logger.info("마이그레이션 시작 (SQLite): qa_tasks 테이블 생성")

        # qa_tasks 테이블 생성
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                error_message TEXT,
                additional_prompt TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """))

        # 인덱스 생성
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_qa_tasks_project_id
            ON qa_tasks(project_id)
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_qa_tasks_status
            ON qa_tasks(status)
        """))

        db.commit()
        logger.info("qa_tasks 테이블 및 인덱스 생성 완료")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


def run_migration_postgres():
    """PostgreSQL용 마이그레이션"""
    db = SessionLocal()

    try:
        logger.info("마이그레이션 시작 (PostgreSQL): qa_tasks 테이블 생성")

        # qa_tasks 테이블 생성
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS qa_tasks (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                error_message TEXT,
                additional_prompt TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """))

        # 인덱스 생성
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_qa_tasks_project_id
            ON qa_tasks(project_id)
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_qa_tasks_status
            ON qa_tasks(status)
        """))

        db.commit()
        logger.info("qa_tasks 테이블 및 인덱스 생성 완료")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    db_url = os.getenv("DATABASE_URL", "sqlite:///./photoscript.db")

    if "postgresql" in db_url:
        run_migration_postgres()
    else:
        run_migration_sqlite()

    print("✅ 마이그레이션 m007 완료: qa_tasks 테이블 생성")
