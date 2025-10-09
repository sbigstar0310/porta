#!/bin/bash

# PORTA 스택 로그 확인 스크립트

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
    echo "  api               FastAPI 서버 로그"
    echo "  worker            Celery Worker 로그"
    echo "  beat              Celery Beat 로그"
    echo "  redis             Redis 서버 로그"
    echo "  flower            Flower 모니터링 로그"
    echo "  (없음)            모든 서비스 로그"
    echo ""
    echo "옵션:"
    echo "  -h, --help        이 도움말을 표시합니다"
    echo "  -f, --follow      실시간으로 로그를 따라갑니다 (기본값)"
    echo "  --no-follow       실시간 추적을 하지 않습니다"
    echo "  -t, --tail LINES  마지막 N줄만 표시합니다 (기본값: 100)"
    echo "  --since TIME      특정 시간 이후의 로그만 표시합니다"
    echo "  --timestamps      타임스탬프를 표시합니다"
    echo ""
    echo "예시:"
    echo "  $0                # 모든 서비스 로그 실시간 확인"
    echo "  $0 api            # API 서버 로그만 확인"
    echo "  $0 worker -t 50   # Worker 로그 마지막 50줄"
    echo "  $0 --since 1h     # 1시간 전부터의 로그"
    echo "  $0 --no-follow    # 실시간 추적 없이 현재 로그만"
}

# 기본값 설정
SERVICE=""
FOLLOW_FLAG="-f"
TAIL_LINES="100"
SINCE_FLAG=""
TIMESTAMPS_FLAG=""

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--follow)
            FOLLOW_FLAG="-f"
            shift
            ;;
        --no-follow)
            FOLLOW_FLAG=""
            shift
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        --since)
            SINCE_FLAG="--since $2"
            shift 2
            ;;
        --timestamps)
            TIMESTAMPS_FLAG="-t"
            shift
            ;;
        api|worker|beat|redis|flower)
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
if [[ -f "docker-compose.override.yml" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.override.yml"
fi

# 스택 상태 확인
if ! $DOCKER_COMPOSE_CMD $COMPOSE_FILES ps -q | grep -q .; then
    log_error "실행 중인 PORTA 스택이 없습니다."
    log_info "먼저 스택을 시작하세요: backend/scripts/stack-start.sh"
    exit 1
fi

# 로그 표시
if [[ -n "$SERVICE" ]]; then
    log_info "$SERVICE 서비스의 로그를 확인합니다..."
    if [[ -n "$FOLLOW_FLAG" ]]; then
        log_info "실시간 로그 추적 중... (Ctrl+C로 종료)"
    fi
else
    log_info "모든 서비스의 로그를 확인합니다..."
    if [[ -n "$FOLLOW_FLAG" ]]; then
        log_info "실시간 로그 추적 중... (Ctrl+C로 종료)"
    fi
fi

# 인터럽트 신호 처리
cleanup() {
    log_info "로그 확인을 종료합니다..."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Docker Compose logs 실행
$DOCKER_COMPOSE_CMD $COMPOSE_FILES logs $FOLLOW_FLAG --tail="$TAIL_LINES" $SINCE_FLAG $TIMESTAMPS_FLAG $SERVICE
