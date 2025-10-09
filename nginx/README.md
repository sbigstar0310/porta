# PORTA Nginx 설정

이 디렉토리는 PORTA 프로젝트의 nginx 리버스 프록시 설정을 포함합니다.

## 구조

```
nginx/
├── Dockerfile              # nginx Docker 이미지 빌드 설정
├── nginx.conf              # 메인 nginx 설정
├── conf.d/
│   └── porta-ai.com.conf   # 도메인별 서버 설정
├── scripts/
│   └── entrypoint.sh       # 컨테이너 시작 스크립트
└── README.md               # 이 파일
```

## 주요 기능

### 🔒 SSL/TLS 보안
- Let's Encrypt 인증서 지원
- TLS 1.2/1.3 프로토콜
- HSTS (HTTP Strict Transport Security)
- 보안 헤더 자동 추가

### 🚀 성능 최적화
- HTTP/2 지원
- Gzip 압축
- 정적 파일 캐싱
- Keep-alive 연결
- 업스트림 로드 밸런싱

### 🔄 프록시 설정
- FastAPI 백엔드로 리버스 프록시
- WebSocket 지원
- 적절한 헤더 전달
- 타임아웃 설정

## 사용법

### 개발 환경
```bash
# 개발 모드로 시작 (HTTP만)
docker compose up nginx

# 직접 API 접근도 가능
curl http://localhost:8000/health
```

### 프로덕션 환경
```bash
# 프로덕션 모드로 시작 (HTTPS 포함)
docker compose -f docker-compose.yml up nginx

# 도메인으로 접근
curl https://porta-ai.com/health
```

## SSL 인증서 설정

### 기존 인증서 사용
현재 시스템의 Let's Encrypt 인증서를 마운트:
```yaml
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro
  - /var/www/certbot:/var/www/certbot:ro
```

### 새 인증서 발급
```bash
# certbot을 사용하여 새 인증서 발급
sudo certbot --nginx -d porta-ai.com -d www.porta-ai.com
```

## 설정 파일 설명

### nginx.conf
- 메인 nginx 설정
- 성능 최적화 옵션
- 보안 헤더 설정
- 업스트림 서버 정의

### porta-ai.com.conf
- 도메인별 서버 블록
- SSL 설정
- 프록시 규칙
- 캐싱 정책

## 모니터링

### 로그 확인
```bash
# nginx 로그 확인
docker-compose logs nginx

# 실시간 로그 모니터링
docker-compose logs -f nginx
```

### 헬스체크
```bash
# nginx 상태 확인
curl http://localhost/health

# SSL 인증서 확인
openssl s_client -connect porta-ai.com:443 -servername porta-ai.com
```

## 트러블슈팅

### SSL 인증서 문제
1. 인증서 파일 권한 확인
2. 인증서 만료일 확인
3. nginx 설정 문법 검사: `nginx -t`

### 프록시 연결 문제
1. 백엔드 서비스 상태 확인
2. 네트워크 연결 확인
3. 업스트림 설정 확인

### 성능 문제
1. nginx 로그 분석
2. 리소스 사용량 모니터링
3. 캐싱 설정 최적화
