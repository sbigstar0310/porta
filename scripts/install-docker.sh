#!/bin/bash

# PORTA Docker + Docker Compose 설치 스크립트 (Ubuntu/Debian)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo "사용법: sudo $0 [OPTIONS]"
    echo ""
    echo "Docker Engine과 Docker Compose를 설치합니다. (Ubuntu/Debian)"
    echo ""
    echo "옵션:"
    echo "  -h, --help        이 도움말을 표시합니다"
    echo "  --uninstall       Docker를 제거합니다"
    echo "  --check           설치 상태만 확인합니다"
    echo ""
    echo "예시:"
    echo "  sudo $0            # Docker 설치"
    echo "  sudo $0 --check    # 설치 상태 확인"
    echo "  sudo $0 --uninstall # Docker 제거"
}

# root 권한 확인
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "이 스크립트는 root 권한이 필요합니다."
        log_info "다음과 같이 실행하세요: sudo $0"
        exit 1
    fi
}

# OS 확인
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "지원되지 않는 OS입니다. Ubuntu/Debian만 지원합니다."
        exit 1
    fi

    . /etc/os-release

    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_error "지원되지 않는 OS입니다: $ID"
        log_info "이 스크립트는 Ubuntu/Debian만 지원합니다."
        exit 1
    fi

    OS_ID="$ID"
    OS_VERSION="$VERSION_CODENAME"
    log_info "감지된 OS: $PRETTY_NAME"
}

# 설치 상태 확인
check_status() {
    echo ""
    echo "========================================="
    echo "  Docker 설치 상태"
    echo "========================================="
    echo ""

    # Docker Engine
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>/dev/null)
        log_success "Docker Engine: $DOCKER_VERSION"
    else
        log_warning "Docker Engine: 설치되지 않음"
    fi

    # Docker Compose
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version 2>/dev/null)
        log_success "Docker Compose: $COMPOSE_VERSION"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version 2>/dev/null)
        log_success "Docker Compose (standalone): $COMPOSE_VERSION"
    else
        log_warning "Docker Compose: 설치되지 않음"
    fi

    # Docker 데몬 상태
    if systemctl is-active --quiet docker 2>/dev/null; then
        log_success "Docker 데몬: 실행 중"
    else
        log_warning "Docker 데몬: 중지됨"
    fi

    # 현재 사용자 docker 그룹 확인
    CURRENT_USER="${SUDO_USER:-$USER}"
    if id -nG "$CURRENT_USER" 2>/dev/null | grep -qw docker; then
        log_success "사용자 '$CURRENT_USER': docker 그룹에 포함됨"
    else
        log_warning "사용자 '$CURRENT_USER': docker 그룹에 포함되지 않음"
    fi

    echo ""
}

# 기존 비공식 Docker 패키지 제거
remove_unofficial() {
    log_info "기존 비공식 Docker 패키지를 확인합니다..."
    local UNOFFICIAL_PKGS=(docker.io docker-doc docker-compose podman-docker containerd runc)
    local TO_REMOVE=()

    for pkg in "${UNOFFICIAL_PKGS[@]}"; do
        if dpkg -l "$pkg" &> /dev/null 2>&1; then
            TO_REMOVE+=("$pkg")
        fi
    done

    if [[ ${#TO_REMOVE[@]} -gt 0 ]]; then
        log_info "제거할 패키지: ${TO_REMOVE[*]}"
        apt-get remove -y "${TO_REMOVE[@]}" > /dev/null 2>&1
        log_success "비공식 패키지가 제거되었습니다."
    else
        log_info "제거할 비공식 패키지가 없습니다."
    fi
}

# Docker 공식 GPG 키 및 저장소 설정
setup_repository() {
    log_info "Docker 공식 저장소를 설정합니다..."

    # 필수 패키지 설치
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg > /dev/null 2>&1

    # GPG 키 디렉토리 생성
    install -m 0755 -d /etc/apt/keyrings

    # Docker 공식 GPG 키 다운로드
    if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
        curl -fsSL "https://download.docker.com/linux/$OS_ID/gpg" -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        log_success "Docker GPG 키가 추가되었습니다."
    else
        log_info "Docker GPG 키가 이미 존재합니다."
    fi

    # 저장소 추가
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$OS_ID \
        $OS_VERSION stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    log_success "Docker 저장소가 설정되었습니다."
}

# Docker 설치
install_docker() {
    log_info "Docker Engine + Docker Compose를 설치합니다..."

    apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin \
        > /dev/null 2>&1

    if [[ $? -ne 0 ]]; then
        log_error "Docker 설치에 실패했습니다."
        exit 1
    fi

    log_success "Docker가 설치되었습니다."
}

# Docker 데몬 시작 및 활성화
start_docker() {
    log_info "Docker 데몬을 시작합니다..."

    systemctl start docker
    systemctl enable docker > /dev/null 2>&1

    if systemctl is-active --quiet docker; then
        log_success "Docker 데몬이 실행 중입니다."
    else
        log_error "Docker 데몬 시작에 실패했습니다."
        exit 1
    fi
}

# 현재 사용자를 docker 그룹에 추가
setup_user() {
    CURRENT_USER="${SUDO_USER:-$USER}"

    if [[ "$CURRENT_USER" == "root" ]]; then
        log_info "root 사용자로 실행 중이므로 docker 그룹 설정을 건너뜁니다."
        return
    fi

    if id -nG "$CURRENT_USER" | grep -qw docker; then
        log_info "사용자 '$CURRENT_USER'는 이미 docker 그룹에 포함되어 있습니다."
    else
        usermod -aG docker "$CURRENT_USER"
        log_success "사용자 '$CURRENT_USER'를 docker 그룹에 추가했습니다."
        log_warning "그룹 변경을 적용하려면 로그아웃 후 다시 로그인하세요."
    fi
}

# 설치 검증
verify_installation() {
    echo ""
    log_info "설치를 검증합니다..."

    # Docker 버전 확인
    docker --version > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        log_success "Docker: $(docker --version)"
    else
        log_error "Docker 설치 검증 실패"
        exit 1
    fi

    # Docker Compose 버전 확인
    docker compose version > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        log_success "Compose: $(docker compose version)"
    else
        log_error "Docker Compose 설치 검증 실패"
        exit 1
    fi

    # hello-world 테스트
    log_info "hello-world 컨테이너로 테스트합니다..."
    if docker run --rm hello-world > /dev/null 2>&1; then
        log_success "Docker가 정상적으로 작동합니다!"
    else
        log_error "Docker 테스트 실패"
        exit 1
    fi
}

# Docker 제거
uninstall_docker() {
    log_info "Docker를 제거합니다..."

    # 서비스 중지
    systemctl stop docker > /dev/null 2>&1
    systemctl disable docker > /dev/null 2>&1

    # 패키지 제거
    apt-get purge -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin \
        > /dev/null 2>&1

    # 저장소 및 키 제거
    rm -f /etc/apt/sources.list.d/docker.list
    rm -f /etc/apt/keyrings/docker.asc

    log_success "Docker 패키지가 제거되었습니다."

    echo ""
    log_warning "Docker 데이터(이미지, 컨테이너, 볼륨)는 유지됩니다."
    log_info "완전히 삭제하려면: sudo rm -rf /var/lib/docker /var/lib/containerd"
}

# 기본값 설정
ACTION="install"

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
        --check)
            ACTION="check"
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

# 실행
check_root

case "$ACTION" in
    check)
        check_status
        ;;
    uninstall)
        check_os
        uninstall_docker
        ;;
    install)
        check_os

        # 이미 설치되어 있는지 확인
        if command -v docker &> /dev/null && docker compose version &> /dev/null; then
            log_warning "Docker가 이미 설치되어 있습니다."
            check_status
            log_info "재설치하려면 먼저 제거하세요: sudo $0 --uninstall"
            exit 0
        fi

        echo ""
        echo "========================================="
        echo "  PORTA - Docker 설치"
        echo "========================================="
        echo ""

        remove_unofficial
        setup_repository
        install_docker
        start_docker
        setup_user
        verify_installation

        echo ""
        echo "========================================="
        log_success "Docker 설치가 완료되었습니다!"
        echo "========================================="
        echo ""
        log_info "다음 단계:"
        log_info "  1. 로그아웃 후 다시 로그인 (docker 그룹 적용)"
        log_info "  2. cd porta && cp .env.example .env  (환경 변수 설정)"
        log_info "  3. ./scripts/stack-start.sh --prod  (서비스 시작)"
        echo ""
        ;;
esac
