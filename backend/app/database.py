from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from app.config import get_settings

settings = get_settings()

# Database URL
SQLALCHEMY_DATABASE_URL = settings.database_url

# SQLite vs PostgreSQL 설정
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # SQLite: StaticPool 사용 (단일 연결)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL: QueuePool 사용 (커넥션 풀링)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,           # 기본 커넥션 수
        max_overflow=10,       # 추가 허용 커넥션 수
        pool_pre_ping=True,    # 연결 상태 확인 (끊어진 연결 자동 복구)
        pool_recycle=3600,     # 1시간마다 연결 재생성
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 테이블 생성"""
    from app.models import project, block, asset, block_asset, user  # noqa: F401
    Base.metadata.create_all(bind=engine)


def dispose_engine():
    """데이터베이스 엔진 연결 풀 정리 (Graceful Shutdown용)"""
    engine.dispose()
    from app.utils.logger import logger
    logger.info("데이터베이스 엔진 연결 풀 dispose 완료")
