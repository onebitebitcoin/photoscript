import logging
from pathlib import Path
from app.config import get_settings

settings = get_settings()

# backend 폴더 기준 debug.log 경로
BACKEND_DIR = Path(__file__).parent.parent.parent
LOG_FILE = BACKEND_DIR / "debug.log"

# 서버 시작 시 기존 로그 삭제
if LOG_FILE.exists():
    LOG_FILE.unlink()
    print(f"[LOG] 기존 로그 파일 삭제: {LOG_FILE}")


def setup_logger(name: str) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
    )

    # 파일 핸들러
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# 기본 로거
logger = setup_logger("photoscript")
