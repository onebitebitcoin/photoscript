"""
마이그레이션: blocks 테이블에 (project_id, index) Unique Constraint 추가

실행 방법:
    cd backend
    python -m migrations.m002_add_block_unique_constraint
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
        # 1. Constraint가 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'blocks' AND constraint_name = 'uq_project_block_index'
        """))

        if result.fetchone():
            logger.info("Unique Constraint가 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: blocks 테이블에 Unique Constraint 추가")

        # 2. 중복 데이터 확인
        result = db.execute(text("""
            SELECT project_id, "index", COUNT(*)
            FROM blocks
            GROUP BY project_id, "index"
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()

        if duplicates:
            logger.warning(f"중복된 (project_id, index) 조합 발견: {len(duplicates)}개")

            # 3. 중복 데이터 수정 (각 프로젝트의 블록을 0부터 순차적으로 재정렬)
            for dup in duplicates:
                project_id = dup[0]
                logger.info(f"프로젝트 {project_id}의 블록 인덱스 재정렬 중...")

                # 해당 프로젝트의 모든 블록을 created_at 순으로 재정렬
                db.execute(text("""
                    WITH ranked_blocks AS (
                        SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) - 1 AS new_index
                        FROM blocks
                        WHERE project_id = :project_id
                    )
                    UPDATE blocks
                    SET "index" = ranked_blocks.new_index
                    FROM ranked_blocks
                    WHERE blocks.id = ranked_blocks.id
                """), {"project_id": project_id})
                db.commit()
                logger.info(f"프로젝트 {project_id} 재정렬 완료")

        # 4. Unique Constraint 추가
        db.execute(text("""
            ALTER TABLE blocks
            ADD CONSTRAINT uq_project_block_index UNIQUE (project_id, "index")
        """))
        db.commit()
        logger.info("Unique Constraint 추가 완료")

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
        # SQLite는 PRAGMA로 constraint 확인
        result = db.execute(text("PRAGMA index_list(blocks)"))
        indexes = [row[1] for row in result.fetchall()]

        if 'uq_project_block_index' in indexes:
            logger.info("Unique Constraint가 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): blocks 테이블에 Unique Constraint 추가")

        # 2. 중복 데이터 확인
        result = db.execute(text("""
            SELECT project_id, "index", COUNT(*)
            FROM blocks
            GROUP BY project_id, "index"
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()

        if duplicates:
            logger.warning(f"중복된 (project_id, index) 조합 발견: {len(duplicates)}개")

            # 3. 중복 데이터 수정
            for dup in duplicates:
                project_id = dup[0]
                logger.info(f"프로젝트 {project_id}의 블록 인덱스 재정렬 중...")

                # 해당 프로젝트의 모든 블록 조회
                result = db.execute(text("""
                    SELECT id FROM blocks
                    WHERE project_id = :project_id
                    ORDER BY created_at, id
                """), {"project_id": project_id})
                block_ids = [row[0] for row in result.fetchall()]

                # 순차적으로 인덱스 할당
                for new_index, block_id in enumerate(block_ids):
                    db.execute(text("""
                        UPDATE blocks SET "index" = :new_index WHERE id = :block_id
                    """), {"new_index": new_index, "block_id": block_id})
                db.commit()
                logger.info(f"프로젝트 {project_id} 재정렬 완료")

        # 4. SQLite는 ALTER TABLE로 constraint 추가 불가
        # 대신 UNIQUE INDEX 생성
        db.execute(text("""
            CREATE UNIQUE INDEX uq_project_block_index ON blocks (project_id, "index")
        """))
        db.commit()
        logger.info("Unique Index 추가 완료")

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
