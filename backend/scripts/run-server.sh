#!/bin/bash

# PORTA 백엔드 서버 실행 스크립트

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 백엔드 디렉토리로 이동
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
    echo "  -p, --port PORT   서버 포트를 지정합니다 (기본값: 8000)"
    echo "  -d, --dev         개발 모드로 실행합니다 (기본값)"
    echo "  -r, --reload      자동 리로드를 활성화합니다 (개발 모드에서 기본값)"
    echo "  --prod            프로덕션 모드로 실행합니다"
    echo "  --no-reload       자동 리로드를 비활성화합니다"
    echo "  --host HOST       바인딩할 호스트를 지정합니다 (기본값: 0.0.0.0)"
    echo ""
    echo "예시:"
    echo "  $0                # 개발 모드로 포트 8000에서 실행"
    echo "  $0 -p 8080        # 포트 8080에서 실행"
    echo "  $0 --prod         # 프로덕션 모드로 실행"
}

# 기본값 설정
PORT=8000
HOST="0.0.0.0"
MODE="dev"
RELOAD_FLAG=""

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--dev)
            MODE="dev"
            RELOAD_FLAG="--reload"
            shift
            ;;
        --prod)
            MODE="prod"
            RELOAD_FLAG=""
            shift
            ;;
        -r|--reload)
            RELOAD_FLAG="--reload"
            shift
            ;;
        --no-reload)
            RELOAD_FLAG=""
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 개발 모드 기본값 설정
if [[ "$MODE" == "dev" && -z "$RELOAD_FLAG" ]]; then
    RELOAD_FLAG="--reload"
fi

# 환경 확인
log_info "PORTA 백엔드 서버를 시작합니다..."

# UV 설치 확인
if ! command -v uv &> /dev/null; then
    log_error "UV가 설치되어 있지 않습니다. UV를 먼저 설치해주세요."
    log_info "설치 명령: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 가상환경 및 의존성 설정
log_info "의존성을 확인하고 설치합니다..."
if ! uv sync --quiet; then
    log_error "의존성 설치에 실패했습니다."
    exit 1
fi

# 환경변수 파일 확인
if [[ -f ".env" ]]; then
    log_info ".env 파일을 발견했습니다."
    export $(grep -v '^#' .env | xargs)
else
    log_warning ".env 파일을 찾을 수 없습니다. 기본 설정을 사용합니다."
fi

# 데이터베이스 초기화 (필요시)
if [[ ! -f "db.pt" ]]; then
    log_info "데이터베이스를 초기화합니다..."
fi

# 서버 시작
log_info "서버 모드: $MODE"
log_info "포트: $PORT"
log_info "호스트: $HOST"

# 인터럽트 신호 처리
cleanup() {
    log_info "서버를 종료합니다..."
    exit 0
}
trap cleanup SIGINT SIGTERM

if [[ "$MODE" == "dev" ]]; then
    log_success "개발 서버를 시작합니다..."
    log_info "서버 주소: http://$HOST:$PORT"
    log_info "API 문서: http://$HOST:$PORT/docs"
    log_info "종료하려면 Ctrl+C를 누르세요."
    echo ""
    
    # 개발 모드 실행 (uvicorn 직접 사용)
    uv run uvicorn app:app --host "$HOST" --port "$PORT" $RELOAD_FLAG --log-level info
else
    log_success "프로덕션 서버를 시작합니다..."
    log_info "서버 주소: http://$HOST:$PORT"
    echo ""
    
    # 프로덕션 모드 실행
    uv run uvicorn app:app --host "$HOST" --port "$PORT" --workers 4 --log-level warning
fi

# 서버 종료 시 정리
log_info "서버가 종료되었습니다."