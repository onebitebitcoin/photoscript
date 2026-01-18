import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from app.config import get_settings

settings = get_settings()

# backend 폴더 기준 debug.log 경로
BACKEND_DIR = Path(__file__).parent.parent.parent
LOG_FILE = BACKEND_DIR / "debug.log"


class JSONFormatter(logging.Formatter):
    """프로덕션용 JSON 포맷터 (12-Factor App - Factor XI)"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
        }

        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 추가 속성 (extra 데이터)
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName"
            ):
                try:
                    json.dumps(value)  # JSON 직렬화 가능 여부 확인
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False)


class DevFormatter(logging.Formatter):
    """개발용 가독성 높은 포맷터"""

    def __init__(self):
        super().__init__(
            '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
        )


def setup_logger(name: str) -> logging.Logger:
    """로거 설정 (환경에 따라 다른 설정 적용)"""
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 재설정 방지
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper()))

    if settings.is_production:
        # 프로덕션: stdout + JSON 형식 (12-Factor App)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)
    else:
        # 개발: stdout + 파일 + 가독성 높은 형식
        dev_formatter = DevFormatter()

        # 서버 시작 시 기존 로그 삭제 (개발 환경만)
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print(f"[LOG] 기존 로그 파일 삭제: {LOG_FILE}")

        # 파일 핸들러
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(dev_formatter)
        logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(dev_formatter)
        logger.addHandler(console_handler)

    return logger


# 기본 로거
logger = setup_logger("photoscript")
