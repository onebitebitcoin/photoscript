# ============================================
# Stage 1: Frontend Build
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY frontend/ ./

# Build frontend (generates static files in dist/)
RUN npm run build

# ============================================
# Stage 2: Backend Production
# ============================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies file
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy frontend build output (static files)
# main.py에서 backend/static/ 경로를 참조하므로 해당 위치에 복사
COPY --from=frontend-builder /app/frontend/dist ./backend/static/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV WORKERS=2

# Expose port (Railway provides PORT env var)
EXPOSE 7100

# Health check (readiness probe)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7100}/ready || exit 1

# Start server with Gunicorn + Uvicorn workers
# Railway injects PORT env var automatically
# --timeout: 워커 프로세스 타임아웃 (QA 검증 등 긴 작업 지원)
# --graceful-timeout: 종료 요청 후 진행 중인 요청 완료 대기 시간
# 마이그레이션을 먼저 실행한 후 서버 시작
CMD ["sh", "-c", "cd backend && python -m migrations.run_all && gunicorn app.main:app \
    --workers ${WORKERS:-2} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-7100} \
    --timeout 600 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -"]
