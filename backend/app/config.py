from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache


# 기본 SECRET_KEY (프로덕션에서 사용 금지)
DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"


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
    secret_key: str = DEFAULT_SECRET_KEY

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

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment.lower() == "development"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """환경 값 검증"""
        valid_environments = ["development", "production", "test"]
        if v.lower() not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}, got '{v}'")
        return v.lower()

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """프로덕션 환경에서의 설정 검증"""
        if self.is_production:
            # 프로덕션에서 기본 SECRET_KEY 사용 금지
            if self.secret_key == DEFAULT_SECRET_KEY or not self.secret_key:
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set in production environment. "
                    "Do not use the default key."
                )

            # 프로덕션에서 SQLite 사용 금지
            if "sqlite" in self.database_url.lower():
                raise ValueError(
                    "CRITICAL: SQLite is not allowed in production. "
                    "Use PostgreSQL instead. Set DATABASE_URL to a PostgreSQL connection string."
                )
        return self


class ConfigurationError(Exception):
    """설정 오류"""
    pass


@lru_cache()
def get_settings() -> Settings:
    """설정 객체 반환 (캐싱됨)"""
    try:
        return Settings()
    except Exception as e:
        raise ConfigurationError(f"Configuration error: {e}") from e
