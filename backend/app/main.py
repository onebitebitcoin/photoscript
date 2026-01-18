from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.database import init_db
from app.utils.logger import logger
from app.routers import projects, blocks, auth

settings = get_settings()


def run_migrations():
    """마이그레이션 실행"""
    try:
        from migrations.m001_add_user_id_to_projects import run_migration, run_migration_sqlite
        if "sqlite" in settings.database_url:
            run_migration_sqlite()
        else:
            run_migration()
    except Exception as e:
        logger.warning(f"마이그레이션 실행 중 오류 (무시됨): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직"""
    logger.info("PhotoScript 서버 시작")
    logger.info(f"Environment: {settings.environment}")

    # 데이터베이스 초기화
    init_db()
    logger.info("데이터베이스 초기화 완료")

    # 마이그레이션 실행
    run_migrations()

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(blocks.router, prefix="/api/v1/blocks", tags=["Blocks"])


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "PhotoScript"}


# 프로덕션에서 정적 파일 서빙 (Frontend 빌드 결과물)
if settings.environment == "production":
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    index_path = os.path.join(static_path, "index.html")
    logger.info(f"Static path: {static_path}, exists: {os.path.exists(static_path)}")

    if os.path.exists(static_path):
        # 정적 파일 서빙 (assets 폴더)
        assets_path = os.path.join(static_path, "assets")
        if os.path.exists(assets_path):
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

        # SPA fallback - API가 아닌 모든 경로에 index.html 반환
        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """SPA fallback - 모든 경로에 index.html 반환"""
            # API 경로는 제외 (이미 위에서 등록됨)
            if full_path.startswith("api/") or full_path in ["health", "docs", "openapi.json", "redoc"]:
                return {"detail": "Not Found"}

            # 정적 파일이 존재하면 해당 파일 반환
            file_path = os.path.join(static_path, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)

            # 그 외에는 index.html 반환 (SPA 라우팅)
            return FileResponse(index_path)

        logger.info("Frontend static files mounted with SPA fallback")
    else:
        logger.warning(f"Static path not found: {static_path}")
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
