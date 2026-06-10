#!/bin/bash

# PORTA 스택 시작 스크립트

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"


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
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -h, --help        이 도움말을 표시합니다"
    echo "  -d, --dev         개발 모드로 실행합니다"
    echo "  -p, --prod        프로덕션 모드로 실행합니다 (기본값)"
    echo "  -b, --build       이미지를 다시 빌드합니다"
    echo "  --no-flower       Flower 서비스를 제외합니다"
    echo "  --detach          백그라운드에서 실행합니다 (기본값)"
    echo "  --foreground      포그라운드에서 실행합니다"
    echo ""
    echo "예시:"
    echo "  $0                # 개발 모드로 백그라운드 실행"
    echo "  $0 --prod         # 프로덕션 모드로 실행"
    echo "  $0 --build        # 이미지 재빌드 후 실행"
    echo "  $0 --foreground   # 포그라운드에서 실행 (로그 실시간 확인)"
}

# 기본값 설정
MODE="prod"
BUILD_FLAG=""
DETACH_FLAG="-d"
COMPOSE_FILES="-f docker-compose.yml"
EXCLUDE_SERVICES=""

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            MODE="dev"
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.override.yml"
            # dev 모드는 반드시 .env.dev로 Supabase를 덮어쓴다 (prod DB 사용 금지)
            if [ -f ".env.dev" ]; then
                DEV_SUPABASE_URL=$(grep -E '^SUPABASE_URL=' .env.dev | head -1 | cut -d= -f2-)
                PROD_SUPABASE_URL=$(grep -E '^SUPABASE_URL=' .env | head -1 | cut -d= -f2-)
                if [ -z "$DEV_SUPABASE_URL" ] || [ "$DEV_SUPABASE_URL" = "$PROD_SUPABASE_URL" ]; then
                    log_error ".env.dev의 SUPABASE_URL이 비어 있거나 프로덕션(.env)과 동일합니다. dev DB로 분리해주세요."
                    exit 1
                fi
                export PORTA_ENV_FILE=".env.dev"
                log_info "dev 환경 오버레이 사용: .env.dev"
            else
                log_error ".env.dev가 없습니다. dev 모드는 프로덕션 DB(.env) 사용이 금지됩니다."
                log_error "루트에 .env.dev를 만들고 dev Supabase의 SUPABASE_URL/KEY/SERVICE_ROLE_KEY를 넣어주세요."
                exit 1
            fi
            shift
            ;;
        -p|--prod)
            MODE="prod"
            COMPOSE_FILES="-f docker-compose.yml"
            unset PORTA_ENV_FILE
            shift
            ;;
        -b|--build)
            BUILD_FLAG="--build"
            shift
            ;;
        --no-flower)
            EXCLUDE_SERVICES="--scale flower=0"
            shift
            ;;
        --detach)
            DETACH_FLAG="-d"
            shift
            ;;
        --foreground)
            DETACH_FLAG=""
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# Docker 및 Docker Compose 확인
log_info "Docker 환경을 확인합니다..."

if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# Docker Compose 명령어 결정
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# 환경변수 파일 확인
if [[ ! -f ".env" ]]; then
    log_warning ".env 파일을 찾을 수 없습니다. 기본 설정을 사용합니다."
fi

# 기존 컨테이너 정리 (필요시)
log_info "기존 컨테이너 상태를 확인합니다..."
if $DOCKER_COMPOSE_CMD $COMPOSE_FILES ps -q | grep -q .; then
    log_info "기존 컨테이너를 정리합니다..."
    $DOCKER_COMPOSE_CMD $COMPOSE_FILES down
fi

# 스택 시작
log_info "PORTA 스택을 시작합니다..."
log_info "모드: $MODE"
log_info "컴포즈 파일: $COMPOSE_FILES"

# 인터럽트 신호 처리 (포그라운드 모드일 때)
if [[ -z "$DETACH_FLAG" ]]; then
    cleanup() {
        log_info "스택을 종료합니다..."
        $DOCKER_COMPOSE_CMD $COMPOSE_FILES down
        exit 0
    }
    trap cleanup SIGINT SIGTERM
fi

# Docker Compose 실행
if $DOCKER_COMPOSE_CMD $COMPOSE_FILES up $DETACH_FLAG $BUILD_FLAG $EXCLUDE_SERVICES; then
    if [[ -n "$DETACH_FLAG" ]]; then
        log_success "PORTA 스택이 백그라운드에서 시작되었습니다!"
        echo ""
        log_info "서비스 상태 확인: $0 status"
        log_info "로그 확인: scripts/stack-logs.sh"
        log_info "스택 중지: scripts/stack-stop.sh"
        echo ""
        log_info "서비스 주소:"
        if [[ "$MODE" == "prod" ]]; then
            log_info "  - 웹사이트: https://porta-ai.com"
            log_info "  - API 문서: https://porta-ai.com/docs"
            log_info "  - API 서버 (직접): http://localhost:8000"
        else
            log_info "  - 웹사이트: http://localhost"
            log_info "  - API 서버: http://localhost:8000"
            log_info "  - API 문서: http://localhost:8000/docs"
        fi
        log_info "  - Flower (Celery 모니터링): http://localhost:5555"
    else
        log_info "스택이 종료되었습니다."
    fi
else
    log_error "스택 시작에 실패했습니다."
    exit 1
fi
