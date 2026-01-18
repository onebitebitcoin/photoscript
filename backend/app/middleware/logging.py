import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logger import setup_logger

# 요청 로깅 전용 로거
request_logger = setup_logger("photoscript.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 요청/응답 자동 로깅 미들웨어"""

    # 헬스체크 엔드포인트 (DEBUG 레벨로 로깅)
    HEALTH_ENDPOINTS = {"/health", "/ready"}

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # 요청 정보
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # 응답 처리
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # 예외 발생 시 로깅
            request_logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "error": str(e),
                }
            )
            raise

        # 처리 시간 계산
        process_time = (time.time() - start_time) * 1000  # ms

        # 로그 레벨 결정
        log_level = logging.DEBUG if path in self.HEALTH_ENDPOINTS else logging.INFO

        # 응답 로깅
        request_logger.log(
            log_level,
            f"{method} {path} {status_code} ({process_time:.2f}ms)",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "client_ip": client_ip,
                "process_time_ms": round(process_time, 2),
            }
        )

        return response
