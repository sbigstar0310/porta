# PORTA Nginx Dockerfile
# 빌드 컨텍스트는 repo 루트 (docker-compose.yml: context: .)

# ===== 1) Flutter web 빌드 스테이지 =====
FROM ghcr.io/cirruslabs/flutter:stable AS flutter-build

WORKDIR /app

# 의존성 먼저 받아서 레이어 캐시 활용
COPY frontend/pubspec.yaml frontend/pubspec.lock ./
RUN flutter pub get

# 소스 복사 후 웹 빌드
# 릴리스 빌드에서는 dotenv가 로드되지 않으므로 API_URL을 dart-define으로 주입
COPY frontend/ ./
RUN flutter pub get \
 && flutter build web --release \
      --dart-define=API_URL=https://porta-ai.com/api

# ===== 2) Nginx 스테이지 =====
FROM nginx:1.25-alpine

# 필요한 패키지 설치
RUN apk add --no-cache \
    certbot \
    certbot-nginx \
    openssl \
    curl

# nginx 설정 파일 복사 (컨텍스트가 루트이므로 nginx/ 접두사)
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/ /etc/nginx/conf.d/

# 로그 / certbot 디렉토리 생성
RUN mkdir -p /var/log/nginx /var/www/certbot

# 엔트리포인트 스크립트
COPY nginx/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Flutter web 정적 산출물 배치
COPY --from=flutter-build /app/build/web /usr/share/nginx/html

# 포트 노출
EXPOSE 80 443

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 엔트리포인트 설정
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
