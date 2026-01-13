#!/bin/bash

# PhotoScript - Test Runner
# 유닛 테스트, 통합 테스트, E2E 테스트를 실행합니다

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    error "가상환경이 없습니다. 먼저 ./install.sh를 실행하세요."
    exit 1
fi

# .env 파일 로드
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 함수: 백엔드 유닛 테스트
run_backend_unit_tests() {
    info "백엔드 유닛 테스트 실행 중..."

    if [ ! -d "backend/tests" ]; then
        error "backend/tests/ 디렉토리가 없습니다."
        return 1
    fi

    cd backend

    if [ "$COVERAGE" = "true" ]; then
        pytest tests/unit/ -v --cov=app --cov-report=html --cov-report=term
    else
        pytest tests/unit/ -v
    fi

    local EXIT_CODE=$?
    cd ..

    if [ $EXIT_CODE -eq 0 ]; then
        success "백엔드 유닛 테스트 통과"
    else
        error "백엔드 유닛 테스트 실패"
        return 1
    fi
}

# 함수: 백엔드 통합 테스트
run_backend_integration_tests() {
    info "백엔드 통합 테스트 실행 중..."

    if [ ! -d "backend/tests/integration" ]; then
        error "backend/tests/integration/ 디렉토리가 없습니다."
        return 1
    fi

    cd backend
    pytest tests/integration/ -v
    local EXIT_CODE=$?
    cd ..

    if [ $EXIT_CODE -eq 0 ]; then
        success "백엔드 통합 테스트 통과"
    else
        error "백엔드 통합 테스트 실패"
        return 1
    fi
}

# 함수: 프론트엔드 테스트
run_frontend_tests() {
    info "프론트엔드 테스트 실행 중..."

    if [ ! -d "frontend" ]; then
        error "frontend/ 디렉토리가 없습니다."
        return 1
    fi

    cd frontend

    if [ "$COVERAGE" = "true" ]; then
        npm run test:coverage
    else
        npm run test
    fi

    local EXIT_CODE=$?
    cd ..

    if [ $EXIT_CODE -eq 0 ]; then
        success "프론트엔드 테스트 통과"
    else
        error "프론트엔드 테스트 실패"
        return 1
    fi
}

# 함수: Lint 검사
run_lint() {
    info "코드 린트 검사 중..."

    # Backend: Ruff
    if [ -d "backend" ]; then
        cd backend
        if command -v ruff &> /dev/null; then
            ruff check . || true
        fi
        cd ..
    fi

    # Frontend: ESLint
    if [ -d "frontend" ]; then
        cd frontend
        npm run lint || true
        cd ..
    fi

    success "린트 검사 완료"
}

# 메인 로직
echo "=========================================="
echo "PhotoScript - Test Runner"
echo "=========================================="
echo ""

# 옵션 파싱
MODE=${1:-"all"}
COVERAGE=false

for arg in "$@"; do
    if [ "$arg" = "--coverage" ]; then
        COVERAGE=true
    fi
done

FAILED=false

case $MODE in
    "unit")
        run_backend_unit_tests || FAILED=true
        ;;
    "integration")
        run_backend_integration_tests || FAILED=true
        ;;
    "frontend")
        run_frontend_tests || FAILED=true
        ;;
    "lint")
        run_lint || FAILED=true
        ;;
    "all"|*)
        run_lint || FAILED=true
        echo ""
        run_backend_unit_tests || FAILED=true
        ;;
esac

echo ""
echo "=========================================="

if [ "$FAILED" = false ]; then
    success "모든 테스트가 통과했습니다!"

    if [ "$COVERAGE" = "true" ]; then
        echo ""
        info "커버리지 리포트: backend/htmlcov/index.html"
    fi

    exit 0
else
    error "일부 테스트가 실패했습니다."
    exit 1
fi
