#!/bin/bash

# PORTA systemd 서비스 설치 스크립트

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
    echo "  --uninstall       systemd 서비스를 제거합니다"
    echo "  --enable          서비스를 활성화합니다 (부팅 시 자동 시작)"
    echo "  --disable         서비스를 비활성화합니다"
    echo ""
    echo "예시:"
    echo "  $0                # 서비스 설치"
    echo "  $0 --enable       # 서비스 설치 + 활성화"
    echo "  $0 --uninstall    # 서비스 제거"
}

# 기본값 설정
ACTION="install"
ENABLE_SERVICE=false

# 명령행 인수 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --uninstall)
            ACTION="uninstall"
            shift
            ;;
        --enable)
            ENABLE_SERVICE=true
            shift
            ;;
        --disable)
            ENABLE_SERVICE=false
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# root 권한 확인
if [[ $EUID -ne 0 ]]; then
    log_error "이 스크립트는 root 권한이 필요합니다."
    log_info "다음과 같이 실행하세요: sudo $0"
    exit 1
fi

SERVICE_NAME="porta"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SOURCE_FILE="$PROJECT_DIR/porta.service"

if [[ "$ACTION" == "uninstall" ]]; then
    # 서비스 제거
    log_info "PORTA systemd 서비스를 제거합니다..."
    
    # 서비스 중지 및 비활성화
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "서비스를 중지합니다..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        log_info "서비스를 비활성화합니다..."
        systemctl disable "$SERVICE_NAME"
    fi
    
    # 서비스 파일 삭제
    if [[ -f "$SERVICE_FILE" ]]; then
        rm "$SERVICE_FILE"
        log_success "서비스 파일이 삭제되었습니다."
    fi
    
    # systemd 데몬 리로드
    systemctl daemon-reload
    
    log_success "PORTA systemd 서비스가 성공적으로 제거되었습니다!"
    
else
    # 서비스 설치
    log_info "PORTA systemd 서비스를 설치합니다..."
    
    # 서비스 파일 존재 확인
    if [[ ! -f "$SOURCE_FILE" ]]; then
        log_error "서비스 파일을 찾을 수 없습니다: $SOURCE_FILE"
        exit 1
    fi
    
    # 기존 서비스 중지 (있다면)
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "기존 서비스를 중지합니다..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # 서비스 파일 복사
    cp "$SOURCE_FILE" "$SERVICE_FILE"
    
    # 권한 설정
    chmod 644 "$SERVICE_FILE"
    
    # systemd 데몬 리로드
    systemctl daemon-reload
    
    log_success "서비스 파일이 설치되었습니다: $SERVICE_FILE"
    
    # 서비스 활성화 (요청된 경우)
    if [[ "$ENABLE_SERVICE" == true ]]; then
        log_info "서비스를 활성화합니다..."
        systemctl enable "$SERVICE_NAME"
        log_success "서비스가 활성화되었습니다. 부팅 시 자동으로 시작됩니다."
    fi
    
    log_success "PORTA systemd 서비스가 성공적으로 설치되었습니다!"
    
    echo ""
    log_info "사용 가능한 명령어:"
    log_info "  sudo systemctl start porta     # 서비스 시작"
    log_info "  sudo systemctl stop porta      # 서비스 중지"
    log_info "  sudo systemctl restart porta   # 서비스 재시작"
    log_info "  sudo systemctl status porta    # 서비스 상태 확인"
    log_info "  sudo systemctl enable porta    # 부팅 시 자동 시작 활성화"
    log_info "  sudo systemctl disable porta   # 부팅 시 자동 시작 비활성화"
    
    if [[ "$ENABLE_SERVICE" != true ]]; then
        echo ""
        log_warning "서비스가 아직 활성화되지 않았습니다."
        log_info "부팅 시 자동 시작하려면: sudo systemctl enable porta"
    fi
fi
