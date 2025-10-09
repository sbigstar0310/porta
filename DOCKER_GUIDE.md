# PORTA Docker Compose 가이드

PORTA 프로젝트의 모든 백엔드 서비스(FastAPI, Celery Worker, Celery Beat, Redis)를 Docker Compose로 통합 관리하는 방법입니다.

## 📁 파일 구조

```
porta/
├── docker-compose.yml              # 메인 컴포즈 파일
├── docker-compose.override.yml     # 개발용 오버라이드
├── porta.service                   # systemd 서비스 파일
├── backend/
│   ├── Dockerfile                  # 백엔드 이미지
│   └── scripts/
│       ├── stack-start.sh          # 스택 시작
│       ├── stack-stop.sh           # 스택 중지
│       ├── stack-logs.sh           # 로그 확인
│       ├── stack-restart.sh        # 스택 재시작
│       └── install-systemd.sh      # systemd 설치
└── .env                           # 환경변수
```

## 🚀 빠른 시작

### 1. 개발 모드로 시작
```bash
# 개발 모드 (자동 리로드, 디버그 로그)
./backend/scripts/stack-start.sh

# 또는 포그라운드에서 실행 (로그 실시간 확인)
./backend/scripts/stack-start.sh --foreground
```

### 2. 프로덕션 모드로 시작
```bash
./backend/scripts/stack-start.sh --prod
```

### 3. 로그 확인
```bash
# 모든 서비스 로그 실시간 확인
./backend/scripts/stack-logs.sh

# 특정 서비스 로그만 확인
./backend/scripts/stack-logs.sh api
./backend/scripts/stack-logs.sh worker
./backend/scripts/stack-logs.sh beat
```

### 4. 스택 중지
```bash
./backend/scripts/stack-stop.sh
```

## 🛠️ 상세 사용법

### 스택 시작 옵션
```bash
./backend/scripts/stack-start.sh [OPTIONS]

옵션:
  -d, --dev         개발 모드 (기본값)
  -p, --prod        프로덕션 모드
  -b, --build       이미지 재빌드
  --no-flower       Flower 제외
  --foreground      포그라운드 실행
```

### 스택 중지 옵션
```bash
./backend/scripts/stack-stop.sh [OPTIONS]

옵션:
  -v, --volumes     볼륨도 삭제 (Redis 데이터 삭제됨)
  --remove-images   이미지도 삭제
  -f, --force       강제 중지
```

### 로그 확인 옵션
```bash
./backend/scripts/stack-logs.sh [OPTIONS] [SERVICE]

서비스: api, worker, beat, redis, flower
옵션:
  -t, --tail LINES  마지막 N줄만 표시
  --since TIME      특정 시간 이후 로그
  --no-follow       실시간 추적 안함
```

### 재시작 옵션
```bash
./backend/scripts/stack-restart.sh [OPTIONS] [SERVICE]

옵션:
  -b, --build       이미지 재빌드
  --hard            완전 중지 후 재시작
  --soft            서비스만 재시작 (기본값)
```

## 🔧 systemd 통합

### systemd 서비스 설치
```bash
# 서비스 설치
sudo ./backend/scripts/install-systemd.sh

# 서비스 설치 + 부팅 시 자동 시작 활성화
sudo ./backend/scripts/install-systemd.sh --enable
```

### systemd 명령어
```bash
# 서비스 시작
sudo systemctl start porta

# 서비스 중지
sudo systemctl stop porta

# 서비스 재시작
sudo systemctl restart porta

# 서비스 상태 확인
sudo systemctl status porta

# 부팅 시 자동 시작 활성화
sudo systemctl enable porta

# 부팅 시 자동 시작 비활성화
sudo systemctl disable porta

# 서비스 제거
sudo ./backend/scripts/install-systemd.sh --uninstall
```

## 🌐 서비스 주소

- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Flower (Celery 모니터링)**: http://localhost:5555

## 🐛 트러블슈팅

### 포트 충돌 해결
```bash
# 기존 서비스 확인
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :6379

# 기존 Redis 컨테이너 중지
docker stop $(docker ps -q --filter "ancestor=redis")
```

### 권한 문제 해결
```bash
# 스크립트 실행 권한 부여
chmod +x backend/scripts/*.sh

# Docker 그룹에 사용자 추가 (재로그인 필요)
sudo usermod -aG docker $USER
```

### 이미지 재빌드
```bash
# 캐시 없이 완전 재빌드
./backend/scripts/stack-start.sh --build

# 또는 직접 Docker Compose 사용
docker-compose build --no-cache
```

### 볼륨 초기화
```bash
# 모든 데이터 삭제 후 재시작
./backend/scripts/stack-stop.sh --volumes
./backend/scripts/stack-start.sh
```

## 📊 모니터링

### 서비스 상태 확인
```bash
docker-compose ps
```

### 리소스 사용량 확인
```bash
docker stats
```

### Celery 작업 모니터링
- Flower 웹 인터페이스: http://localhost:5555
- 실시간 작업 상태, 큐 상태, 워커 상태 확인 가능

## 🔄 개발 워크플로우

### 코드 변경 시
```bash
# 개발 모드에서는 자동 리로드됨 (API 서버)
# Worker/Beat는 재시작 필요
./backend/scripts/stack-restart.sh worker
./backend/scripts/stack-restart.sh beat
```

### 의존성 변경 시
```bash
# 이미지 재빌드 필요
./backend/scripts/stack-restart.sh --build
```

### 환경변수 변경 시
```bash
# .env 파일 수정 후 재시작
./backend/scripts/stack-restart.sh --hard
```

## 🚨 주의사항

1. **데이터 백업**: `stack-stop.sh -v` 사용 시 Redis 데이터가 삭제됩니다.
2. **포트 충돌**: 8000, 6379, 5555 포트가 사용 중이면 충돌할 수 있습니다.
3. **메모리 사용량**: 모든 서비스가 동시에 실행되므로 충분한 메모리가 필요합니다.
4. **개발/운영 분리**: 개발 시에는 override 파일이 자동 적용됩니다.

이제 개별 systemd 서비스 4개 대신 Docker Compose로 통합 관리할 수 있습니다! 🎉
