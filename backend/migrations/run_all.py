"""
모든 마이그레이션을 순서대로 실행하는 스크립트

운영 배포 시 자동으로 실행됨
"""

import sys
import os

# 상위 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import logger
from app.config import get_settings

# 마이그레이션 모듈 import
from migrations import m001_add_user_id_to_projects
from migrations import m002_add_block_unique_constraint


def run_all_migrations():
    """모든 마이그레이션을 순서대로 실행"""
    settings = get_settings()
    is_sqlite = "sqlite" in settings.database_url

    logger.info("=" * 60)
    logger.info("마이그레이션 시작")
    logger.info(f"데이터베이스: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    logger.info("=" * 60)

    migrations = [
        ("001", "projects 테이블에 user_id 추가", m001_add_user_id_to_projects),
        ("002", "blocks 테이블에 Unique Constraint 추가", m002_add_block_unique_constraint),
    ]

    for num, description, module in migrations:
        try:
            logger.info(f"\n[{num}] {description}")
            logger.info("-" * 60)

            if is_sqlite:
                if hasattr(module, 'run_migration_sqlite'):
                    module.run_migration_sqlite()
                else:
                    logger.warning(f"SQLite 마이그레이션 함수가 없습니다: {num}")
            else:
                if hasattr(module, 'run_migration'):
                    module.run_migration()
                else:
                    logger.warning(f"PostgreSQL 마이그레이션 함수가 없습니다: {num}")

            logger.info(f"[{num}] 완료 ✓")

        except Exception as e:
            logger.error(f"[{num}] 실패: {str(e)}", exc_info=True)
            # 마이그레이션 실패 시 계속 진행 (이미 적용된 경우)
            continue

    logger.info("=" * 60)
    logger.info("모든 마이그레이션 완료!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_all_migrations()
