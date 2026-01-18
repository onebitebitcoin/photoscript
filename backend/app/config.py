from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


def find_env_file() -> Optional[str]:
    """개발/배포 환경에서 .env 파일 경로 찾기"""
    # 시도할 경로 목록 (우선순위 순)
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / ".env",  # 프로젝트 루트
        Path(__file__).parent.parent.parent / ".env",  # backend 폴더
        Path(".env"),  # 현재 디렉토리
        Path("../.env"),  # 상위 디렉토리
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return None  # 환경변수로만 설정됨 (배포 환경)


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./photoscript.db"

    # Security
    secret_key: str = "your-secret-key-change-in-production"

    # Environment
    environment: str = "development"
    log_level: str = "DEBUG"

    # External APIs
    pexels_api_key: str = ""
    openai_api_key: str = ""

    # App settings
    max_script_length: int = 50000
    max_block_length: int = 500
    max_candidates_per_block: int = 10

    class Config:
        env_file = find_env_file()
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
