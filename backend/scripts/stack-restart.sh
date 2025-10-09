#!/bin/bash

# PORTA 스택 재시작 스크립트

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 프로젝트 루트로 이동
cd "$PROJECT_DIR" || exit 1

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 도움말 출력
show_help() {
    echo "사용법: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "서비스:"
    echo "  nginx             Nginx 리버스 프록시만 재시작"
    echo "  api               FastAPI 서버만 재시작"
    echo "  worker            Celery Worker만 재시작"
    echo "  beat              Celery Beat만 재시작"
    echo "  redis             Redis 서버만 재시작"
    echo "  flower            Flower 모니터링만 재시작"
    echo "  (없음)            모든 서비스 재시작"
    echo ""
    echo "옵션:"
    echo "  -h, --help        이 도움말을 표시합니다"
    echo "  -d, --dev         개발 모드로 재시작합니다"
    echo "  -p, --prod        프로덕션 모드로 재시작합니다 (기본값)"
    echo "  -b, --build       이미지를 다시 빌드합니다"
    echo "  --hard            완전 중지 후 재시작 (down -> up)"
    echo "  --soft            서비스만 재시작 (restart, 기본값)"
    echo ""
    echo "예시:"
    echo "  $0                # 모든 서비스 재시작"
    echo "  $0 api            # API 서버만 재시작"
    echo "  $0 --build        # 이미지 재빌드 후 재시작"
    echo "  $0 --hard         # 완전 중지 후 재시작"
}

# 기본값 설정
SERVICE=""
BUILD_FLAG=""
RESTART_MODE="soft"
MODE="prod"

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            MODE="dev"
            shift
            ;;
        -p|--prod)
            MODE="prod"
            shift
            ;;
        -b|--build)
            BUILD_FLAG="--build"
            RESTART_MODE="hard"  # 빌드 시에는 hard restart 필요
            shift
            ;;
        --hard)
            RESTART_MODE="hard"
            shift
            ;;
        --soft)
            RESTART_MODE="soft"
            shift
            ;;
        nginx|api|worker|beat|redis|flower)
            SERVICE="$1"
            shift
            ;;
        *)
            log_error "알 수 없는 옵션 또는 서비스: $1"
            show_help
            exit 1
            ;;
    esac
done

# Docker Compose 명령어 결정
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# 컴포즈 파일 결정
COMPOSE_FILES="-f docker-compose.yml"
if [[ "$MODE" == "dev" && -f "docker-compose.override.yml" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.override.yml"
fi

# 스택 상태 확인
if ! $DOCKER_COMPOSE_CMD $COMPOSE_FILES ps -q | grep -q .; then
    log_warning "실행 중인 PORTA 스택이 없습니다."
    log_info "스택을 새로 시작합니다..."
    exec "$SCRIPT_DIR/stack-start.sh"
fi

# 재시작 실행
if [[ "$RESTART_MODE" == "hard" ]]; then
    # Hard restart: down -> up
    if [[ -n "$SERVICE" ]]; then
        log_info "$SERVICE 서비스를 완전 재시작합니다..."
        
        # 특정 서비스 중지
        $DOCKER_COMPOSE_CMD $COMPOSE_FILES stop "$SERVICE"
        
        # 특정 서비스 시작
        if $DOCKER_COMPOSE_CMD $COMPOSE_FILES up -d $BUILD_FLAG "$SERVICE"; then
            log_success "$SERVICE 서비스가 성공적으로 재시작되었습니다!"
        else
            log_error "$SERVICE 서비스 재시작에 실패했습니다."
            exit 1
        fi
    else
        log_info "모든 서비스를 완전 재시작합니다..."
        
        # 전체 스택 중지
        $DOCKER_COMPOSE_CMD $COMPOSE_FILES down
        
        # 전체 스택 시작
        if $DOCKER_COMPOSE_CMD $COMPOSE_FILES up -d $BUILD_FLAG; then
            log_success "PORTA 스택이 성공적으로 재시작되었습니다!"
            
            # nginx DNS 캐시 갱신을 위한 추가 재시작
            if $DOCKER_COMPOSE_CMD $COMPOSE_FILES ps nginx | grep -q "Up"; then
                log_info "nginx DNS 캐시 갱신을 위해 재시작합니다..."
                $DOCKER_COMPOSE_CMD $COMPOSE_FILES restart nginx
                sleep 3
            fi
        else
            log_error "스택 재시작에 실패했습니다."
            exit 1
        fi
    fi
else
    # Soft restart: restart command
    if [[ -n "$SERVICE" ]]; then
        log_info "$SERVICE 서비스를 재시작합니다..."
        
        if $DOCKER_COMPOSE_CMD $COMPOSE_FILES restart "$SERVICE"; then
            log_success "$SERVICE 서비스가 성공적으로 재시작되었습니다!"
        else
            log_error "$SERVICE 서비스 재시작에 실패했습니다."
            exit 1
        fi
    else
        log_info "모든 서비스를 재시작합니다..."
        
        if $DOCKER_COMPOSE_CMD $COMPOSE_FILES restart; then
            log_success "PORTA 스택이 성공적으로 재시작되었습니다!"
        else
            log_error "스택 재시작에 실패했습니다."
            exit 1
        fi
    fi
fi

# 서비스 상태 확인
log_info "서비스 상태를 확인합니다..."
$DOCKER_COMPOSE_CMD $COMPOSE_FILES ps

echo ""
log_info "서비스 주소:"
# 프로덕션/개발 모드 확인
if [[ "$COMPOSE_FILES" == *"override"* ]]; then
    log_info "  - 웹사이트: http://localhost"
    log_info "  - API 서버: http://localhost:8000"
    log_info "  - API 문서: http://localhost:8000/docs"
else
    log_info "  - 웹사이트: https://porta-ai.com"
    log_info "  - API 문서: https://porta-ai.com/docs"
    log_info "  - API 서버 (직접): http://localhost:8000"
fi
log_info "  - Flower (Celery 모니터링): http://localhost:5555"
