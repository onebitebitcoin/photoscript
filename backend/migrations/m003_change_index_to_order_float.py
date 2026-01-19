"""
마이그레이션: blocks 테이블의 index(Integer) -> order(Float) 변경

Fractional Indexing 방식 도입:
- 중간 삽입 시 다른 블록 수정 불필요
- 예: 1.0과 2.0 사이에 삽입 → 1.5

실행 방법:
    cd backend
    python -m migrations.m003_change_index_to_order_float
"""

import sys
import os

# 상위 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal
from app.utils.logger import logger


def run_migration():
    """마이그레이션 실행 (PostgreSQL)"""
    db = SessionLocal()

    try:
        # 1. order 컬럼이 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'blocks' AND column_name = 'order'
        """))

        if result.fetchone():
            logger.info("order 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: index(Integer) -> order(Float) 변경")

        # 2. 기존 unique constraint 삭제 (존재하는 경우)
        result = db.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'blocks' AND constraint_name = 'uq_project_block_index'
        """))
        if result.fetchone():
            db.execute(text("ALTER TABLE blocks DROP CONSTRAINT uq_project_block_index"))
            logger.info("기존 Unique Constraint 삭제 완료")

        # 3. order 컬럼 추가 (Float, 기본값은 기존 index 값)
        db.execute(text("""
            ALTER TABLE blocks ADD COLUMN "order" FLOAT
        """))
        logger.info("order 컬럼 추가 완료")

        # 4. 기존 index 값을 order로 복사 (정수를 Float으로)
        db.execute(text("""
            UPDATE blocks SET "order" = CAST("index" AS FLOAT)
        """))
        logger.info("기존 index 값을 order로 복사 완료")

        # 5. order 컬럼을 NOT NULL로 변경
        db.execute(text("""
            ALTER TABLE blocks ALTER COLUMN "order" SET NOT NULL
        """))
        logger.info("order 컬럼 NOT NULL 설정 완료")

        # 6. index 컬럼 삭제
        db.execute(text("""
            ALTER TABLE blocks DROP COLUMN "index"
        """))
        logger.info("기존 index 컬럼 삭제 완료")

        # 7. 새로운 인덱스 생성 (정렬용)
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_blocks_project_order ON blocks (project_id, "order")
        """))
        logger.info("새 인덱스 생성 완료")

        db.commit()
        logger.info("마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}", exc_info=True)
        raise
    finally:
        db.close()


def run_migration_sqlite():
    """SQLite용 마이그레이션"""
    db = SessionLocal()

    try:
        # SQLite는 컬럼 수정이 제한적이므로 테이블 재생성 필요

        # 1. order 컬럼이 이미 존재하는지 확인
        result = db.execute(text("PRAGMA table_info(blocks)"))
        columns = [row[1] for row in result.fetchall()]

        if 'order' in columns:
            logger.info("order 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): index(Integer) -> order(Float) 변경")

        # 2. 임시 테이블 생성 (새 스키마)
        db.execute(text("""
            CREATE TABLE blocks_new (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id),
                "order" REAL NOT NULL,
                text TEXT NOT NULL,
                keywords JSON,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("새 테이블 생성 완료")

        # 3. 데이터 복사 (index -> order)
        db.execute(text("""
            INSERT INTO blocks_new (id, project_id, "order", text, keywords, status, created_at, updated_at)
            SELECT id, project_id, CAST("index" AS REAL), text, keywords, status, created_at, updated_at
            FROM blocks
        """))
        logger.info("데이터 복사 완료")

        # 4. 기존 테이블 삭제
        db.execute(text("DROP TABLE blocks"))
        logger.info("기존 테이블 삭제 완료")

        # 5. 새 테이블 이름 변경
        db.execute(text("ALTER TABLE blocks_new RENAME TO blocks"))
        logger.info("테이블 이름 변경 완료")

        # 6. 인덱스 생성
        db.execute(text("""
            CREATE INDEX ix_blocks_project_order ON blocks (project_id, "order")
        """))
        logger.info("인덱스 생성 완료")

        db.commit()
        logger.info("마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}", exc_info=True)
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
