import os
from pydantic_settings import BaseSettings
from functools import lru_cache


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
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
