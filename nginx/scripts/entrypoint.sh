#!/bin/sh

# PORTA Nginx 엔트리포인트 스크립트

set -e

echo "🚀 PORTA Nginx 컨테이너를 시작합니다..."

# nginx 설정 테스트
echo "📋 nginx 설정을 확인합니다..."
nginx -t

# SSL 인증서 확인
if [ -f "/etc/letsencrypt/live/porta-ai.com/fullchain.pem" ]; then
    echo "✅ SSL 인증서가 발견되었습니다."
else
    echo "⚠️  SSL 인증서가 없습니다. HTTP 모드로 시작합니다."
    # SSL 설정이 없는 경우를 위한 임시 설정으로 교체
    if [ ! -f "/etc/letsencrypt/live/porta-ai.com/fullchain.pem" ]; then
        echo "🔄 HTTP 전용 설정으로 전환합니다..."
        cp /etc/nginx/conf.d/porta-ai.com.conf /etc/nginx/conf.d/porta-ai.com.conf.bak
        cat > /etc/nginx/conf.d/porta-ai.com.conf << 'EOF'
# HTTP 서버 블록 (SSL 인증서 없을 때)
server {
    listen 80;
    server_name porta-ai.com www.porta-ai.com;
    
    # Let's Encrypt 인증서 갱신을 위한 경로
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # API 프록시 설정
    location / {
        proxy_pass http://porta_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 헬스체크 경로
    location /health {
        proxy_pass http://porta_backend/health;
        proxy_set_header Host $host;
        access_log off;
    }
}
EOF
    fi
fi

# nginx 설정 재테스트
echo "🔍 최종 nginx 설정을 확인합니다..."
nginx -t

echo "✅ nginx 설정이 완료되었습니다."
echo "🌐 서버를 시작합니다..."

# 전달된 명령 실행
exec "$@"
