import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# TEST_DATABASE_URL 환경 변수 지원 (Factor X: Dev/Prod Parity)
# PostgreSQL로 테스트하려면: TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# SQLite vs PostgreSQL 설정
if "sqlite" in TEST_DATABASE_URL:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 DB 세션"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """테스트용 DB 세션 픽스처"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 테이블 삭제
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session):
    """테스트용 사용자 픽스처"""
    from app.models import User

    user = User(
        nickname="testuser",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db_session, test_user):
    """테스트 클라이언트 픽스처 (인증 포함)"""
    from app.dependencies import get_current_user

    app.dependency_overrides[get_db] = override_get_db

    # 인증 우회: 테스트용 사용자로 설정
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    # 테이블 삭제
    Base.metadata.drop_all(bind=engine)

    app.dependency_overrides.clear()
