from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database import init_db
from app.utils.logger import logger
from app.routers import projects, blocks

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직"""
    logger.info("PhotoScript 서버 시작")
    logger.info(f"Environment: {settings.environment}")

    # 데이터베이스 초기화
    init_db()
    logger.info("데이터베이스 초기화 완료")

    yield

    logger.info("PhotoScript 서버 종료")


app = FastAPI(
    title="PhotoScript API",
    description="유튜브 스크립트를 블록 단위로 분할하고 이미지/영상을 매칭하는 API",
    version="1.0.0",
    lifespan=lifespan
)

# Trailing slash redirect 비활성화
app.router.redirect_slashes = False

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(blocks.router, prefix="/api/v1/blocks", tags=["Blocks"])


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "PhotoScript"}


# 프로덕션에서 정적 파일 서빙 (Frontend 빌드 결과물)
# 주의: StaticFiles 마운트는 @app.get("/") 보다 먼저 설정해야 프론트엔드가 서빙됨
if settings.environment == "production":
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    logger.info(f"Static path: {static_path}, exists: {os.path.exists(static_path)}")
    if os.path.exists(static_path):
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
        logger.info("Frontend static files mounted at /")
    else:
        logger.warning(f"Static path not found: {static_path}")
        # 정적 파일이 없을 때만 API 응답
        @app.get("/")
        async def root():
            """루트 엔드포인트 (정적 파일 없을 때)"""
            return {
                "message": "PhotoScript API",
                "docs": "/docs",
                "health": "/health"
            }
else:
    # 개발 환경에서는 API 응답
    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return {
            "message": "PhotoScript API",
            "docs": "/docs",
            "health": "/health"
        }
