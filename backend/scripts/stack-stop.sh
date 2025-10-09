#!/bin/bash

# PORTA 스택 중지 스크립트

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
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -h, --help        이 도움말을 표시합니다"
    echo "  -v, --volumes     볼륨도 함께 삭제합니다"
    echo "  --remove-images   이미지도 함께 삭제합니다"
    echo "  -f, --force       강제로 중지합니다"
    echo ""
    echo "예시:"
    echo "  $0                # 스택 중지"
    echo "  $0 -v             # 스택 중지 + 볼륨 삭제"
    echo "  $0 --remove-images # 스택 중지 + 이미지 삭제"
}

# 기본값 설정
VOLUMES_FLAG=""
IMAGES_FLAG=""
FORCE_FLAG=""

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--volumes)
            VOLUMES_FLAG="-v"
            shift
            ;;
        --remove-images)
            IMAGES_FLAG="--rmi all"
            shift
            ;;
        -f|--force)
            FORCE_FLAG="--timeout 0"
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
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
log_info "PORTA 스택 상태를 확인합니다..."

if ! $DOCKER_COMPOSE_CMD $COMPOSE_FILES ps -q | grep -q .; then
    log_warning "실행 중인 PORTA 스택이 없습니다."
    exit 0
fi

# 스택 중지
log_info "PORTA 스택을 중지합니다..."

if [[ -n "$VOLUMES_FLAG" ]]; then
    log_warning "볼륨도 함께 삭제됩니다. Redis 데이터가 삭제됩니다!"
fi

if [[ -n "$IMAGES_FLAG" ]]; then
    log_warning "이미지도 함께 삭제됩니다!"
fi

# 확인 메시지 (force 모드가 아닐 때)
if [[ -z "$FORCE_FLAG" && (-n "$VOLUMES_FLAG" || -n "$IMAGES_FLAG") ]]; then
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "취소되었습니다."
        exit 0
    fi
fi

# Docker Compose down 실행
if $DOCKER_COMPOSE_CMD $COMPOSE_FILES down $VOLUMES_FLAG $IMAGES_FLAG $FORCE_FLAG; then
    log_success "PORTA 스택이 성공적으로 중지되었습니다!"
    
    if [[ -n "$VOLUMES_FLAG" ]]; then
        log_info "볼륨이 삭제되었습니다."
    fi
    
    if [[ -n "$IMAGES_FLAG" ]]; then
        log_info "이미지가 삭제되었습니다."
    fi
else
    log_error "스택 중지에 실패했습니다."
    exit 1
fi

# 정리 작업
log_info "정리 작업을 수행합니다..."

# 사용하지 않는 네트워크 정리
docker network prune -f &> /dev/null || true

log_success "모든 작업이 완료되었습니다!"
