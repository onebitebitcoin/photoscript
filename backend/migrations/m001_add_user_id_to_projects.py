"""
마이그레이션: projects 테이블에 user_id 필드 추가

실행 방법:
    cd backend
    python -m migrations.001_add_user_id_to_projects
"""

import sys
import os

# 상위 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.utils.logger import logger


def run_migration():
    """마이그레이션 실행"""
    db = SessionLocal()

    try:
        # 1. user_id 컬럼이 이미 존재하는지 확인
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'projects' AND column_name = 'user_id'
        """))

        if result.fetchone():
            logger.info("user_id 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작: projects 테이블에 user_id 추가")

        # 2. user_id 컬럼 추가 (nullable로 먼저 추가)
        db.execute(text("""
            ALTER TABLE projects
            ADD COLUMN user_id VARCHAR(36)
        """))
        db.commit()
        logger.info("user_id 컬럼 추가 완료")

        # 3. 기존 프로젝트가 있는지 확인
        result = db.execute(text("SELECT COUNT(*) FROM projects"))
        project_count = result.scalar()

        if project_count > 0:
            logger.warning(f"기존 프로젝트 {project_count}개 발견. 기본 사용자 생성 필요.")

            # 기본 사용자가 있는지 확인
            result = db.execute(text("SELECT id FROM users LIMIT 1"))
            first_user = result.fetchone()

            if first_user:
                default_user_id = first_user[0]
                logger.info(f"첫 번째 사용자에게 기존 프로젝트 할당: {default_user_id}")
            else:
                # 기본 사용자 생성
                from uuid import uuid4
                from passlib.context import CryptContext

                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                default_user_id = str(uuid4())
                password_hash = pwd_context.hash("admin1234")

                db.execute(text("""
                    INSERT INTO users (id, nickname, password_hash, is_active)
                    VALUES (:id, :nickname, :password_hash, :is_active)
                """), {
                    "id": default_user_id,
                    "nickname": "admin",
                    "password_hash": password_hash,
                    "is_active": True
                })
                db.commit()
                logger.info(f"기본 사용자 생성: admin (비밀번호: admin1234)")

            # 기존 프로젝트에 user_id 할당
            db.execute(text("""
                UPDATE projects SET user_id = :user_id WHERE user_id IS NULL
            """), {"user_id": default_user_id})
            db.commit()
            logger.info(f"기존 프로젝트 {project_count}개에 user_id 할당 완료")

        # 4. NOT NULL 제약 조건 추가 (PostgreSQL)
        try:
            db.execute(text("""
                ALTER TABLE projects ALTER COLUMN user_id SET NOT NULL
            """))
            db.commit()
            logger.info("NOT NULL 제약 조건 추가 완료")
        except Exception as e:
            logger.warning(f"NOT NULL 제약 조건 추가 실패 (SQLite는 지원 안 함): {e}")

        # 5. 인덱스 추가
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id)
            """))
            db.commit()
            logger.info("인덱스 생성 완료")
        except Exception as e:
            logger.warning(f"인덱스 생성 실패: {e}")

        logger.info("마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


def run_migration_sqlite():
    """SQLite용 마이그레이션 (ALTER TABLE 제한으로 인해 다른 방식 사용)"""
    db = SessionLocal()

    try:
        # SQLite는 information_schema를 지원하지 않으므로 PRAGMA 사용
        result = db.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result.fetchall()]

        if 'user_id' in columns:
            logger.info("user_id 컬럼이 이미 존재합니다. 마이그레이션 스킵.")
            return

        logger.info("마이그레이션 시작 (SQLite): projects 테이블에 user_id 추가")

        # user_id 컬럼 추가
        db.execute(text("ALTER TABLE projects ADD COLUMN user_id VARCHAR(36)"))
        db.commit()
        logger.info("user_id 컬럼 추가 완료")

        # 기존 프로젝트 처리
        result = db.execute(text("SELECT COUNT(*) FROM projects"))
        project_count = result.scalar()

        if project_count > 0:
            result = db.execute(text("SELECT id FROM users LIMIT 1"))
            first_user = result.fetchone()

            if first_user:
                default_user_id = first_user[0]
            else:
                from uuid import uuid4
                from passlib.context import CryptContext

                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                default_user_id = str(uuid4())
                password_hash = pwd_context.hash("admin1234")

                db.execute(text("""
                    INSERT INTO users (id, nickname, password_hash, is_active)
                    VALUES (:id, :nickname, :password_hash, :is_active)
                """), {
                    "id": default_user_id,
                    "nickname": "admin",
                    "password_hash": password_hash,
                    "is_active": True
                })
                db.commit()
                logger.info("기본 사용자 생성: admin (비밀번호: admin1234)")

            db.execute(text("UPDATE projects SET user_id = :user_id WHERE user_id IS NULL"),
                      {"user_id": default_user_id})
            db.commit()
            logger.info(f"기존 프로젝트 {project_count}개에 user_id 할당 완료")

        # 인덱스 생성
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id)"))
            db.commit()
            logger.info("인덱스 생성 완료")
        except Exception as e:
            logger.warning(f"인덱스 생성 실패: {e}")

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
