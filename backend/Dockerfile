# PORTA Backend Dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libgobject-2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# UV 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./

# UV를 사용하여 의존성 설치
RUN uv sync --frozen

# 애플리케이션 코드 복사
COPY . .

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8000

# 기본 명령어 (docker-compose에서 오버라이드됨)
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
