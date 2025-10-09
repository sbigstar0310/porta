# PORTA Nginx Dockerfile
FROM nginx:1.25-alpine

# 필요한 패키지 설치
RUN apk add --no-cache \
    certbot \
    certbot-nginx \
    openssl \
    curl

# nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# 로그 디렉토리 생성
RUN mkdir -p /var/log/nginx

# certbot을 위한 디렉토리 생성
RUN mkdir -p /var/www/certbot

# nginx 설정 테스트 스크립트
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 포트 노출
EXPOSE 80 443

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 엔트리포인트 설정
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
