# PORTA Backend 테스트 가이드

## 테스트 구조

### 📂 디렉토리 구성

```
tests/
├── conftest.py                    # 공통 fixtures 및 설정
├── pytest.ini                    # pytest 설정 파일
├── fixtures/                     # 테스트 데이터 및 fixtures
│   ├── __init__.py
│   ├── database_fixtures.py      # DB 관련 fixtures
│   ├── mock_data.py              # 테스트용 Mock 데이터
│   └── agent_fixtures.py         # Agent 관련 fixtures
│
├── unit/                         # 단위 테스트
│   ├── test_clients/             # 클라이언트 테스트
│   ├── test_data/                # 데이터 계층 테스트
│   ├── test_repo/                # Repository 테스트
│   ├── test_usecase/             # UseCase 테스트
│   └── test_graph/               # Agent Graph 테스트
│
├── integration/                  # 통합 테스트
│   ├── test_api/                 # API 엔드투엔드 테스트
│   ├── test_database/            # DB 통합 테스트
│   └── test_agent_flows/         # Agent 워크플로우 테스트
│
├── performance/                  # 성능 테스트
│   ├── test_api_performance.py
│   ├── test_db_performance.py
│   └── test_agent_performance.py
│
└── e2e/                         # End-to-End 테스트
    ├── test_user_journey.py
    └── test_portfolio_management.py
```

## 🧪 테스트 실행

### 전체 테스트 실행

```bash
pytest
```

### 마커별 테스트 실행

```bash
# 단위 테스트만 실행
pytest -m unit

# 통합 테스트만 실행
pytest -m integration

# 성능 테스트만 실행
pytest -m performance

# Agent 관련 테스트만 실행
pytest -m agent

# 빠른 테스트만 실행 (slow 마커 제외)
pytest -m "not slow"
```

### 특정 디렉토리/파일 테스트 실행

```bash
# Repository 테스트만 실행
pytest tests/unit/test_repo/

# 특정 테스트 파일 실행
pytest tests/unit/test_repo/test_user_repo.py

# 특정 테스트 클래스 실행
pytest tests/unit/test_repo/test_user_repo.py::TestUserRepo

# 특정 테스트 메서드 실행
pytest tests/unit/test_repo/test_user_repo.py::TestUserRepo::test_create_user_success
```

### 커버리지 리포트와 함께 실행

```bash
# HTML 커버리지 리포트 생성
pytest --cov-report=html

# 터미널에서 커버리지 확인
pytest --cov-report=term-missing
```

### 병렬 테스트 실행 (선택사항)

```bash
# pytest-xdist 설치 후
pip install pytest-xdist

# 4개 프로세스로 병렬 실행
pytest -n 4
```

## 🏷️ 테스트 마커

- **unit**: 단위 테스트 - 개별 컴포넌트의 독립적인 기능 테스트
- **integration**: 통합 테스트 - 여러 컴포넌트 간의 상호작용 테스트
- **performance**: 성능 테스트 - 응답 시간 및 처리량 측정
- **e2e**: End-to-End 테스트 - 전체 사용자 워크플로우 검증
- **slow**: 실행 시간이 긴 테스트 - 기본적으로 제외하고 실행
- **agent**: Agent 관련 테스트 - AI Agent 및 LLM 기능 테스트
- **db**: 데이터베이스 관련 테스트 - DB 연결 및 쿼리 테스트
- **api**: API 엔드포인트 테스트 - FastAPI 라우터 테스트

## 🔧 테스트 의존성 설치

```bash
# 테스트 의존성 설치
pip install -e ".[test]"

# 또는 개별 설치
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx factory-boy freezegun responses psutil
```

## 📝 테스트 작성 가이드

### 1. 테스트 파일 명명 규칙

- 테스트 파일: `test_*.py`
- 테스트 클래스: `Test*`
- 테스트 메서드: `test_*`

### 2. 테스트 구조

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit  # 적절한 마커 추가
class TestUserRepo:
    """Repository 테스트 클래스"""

    @pytest.fixture
    def mock_client(self):
        """테스트용 Mock 클라이언트"""
        return MagicMock()

    def test_create_user_success(self, mock_client):
        """사용자 생성 성공 테스트"""
        # Given
        user_data = {"email": "test@example.com"}

        # When
        result = user_repo.create(user_data)

        # Then
        assert result is not None
        assert result.email == "test@example.com"
```

### 3. Fixtures 활용

```python
# conftest.py에 정의된 공통 fixtures 사용
def test_with_sample_data(sample_user_data, mock_database):
    # 공통 fixtures를 활용한 테스트
    pass

# 테스트 파일별 fixtures 정의
@pytest.fixture
def specific_test_data():
    return {"specific": "data"}
```

### 4. Mock 사용 패턴

```python
# 외부 의존성 Mock
@patch('module.external_service')
def test_with_external_mock(mock_service):
    mock_service.return_value = "mocked_response"
    # 테스트 로직

# Database Mock
@patch('repo.Database')
def test_with_db_mock(mock_db):
    mock_db.return_value.query.return_value = []
    # 테스트 로직
```

## 🚀 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run unit tests
        run: pytest -m unit --cov-report=xml

      - name: Run integration tests
        run: pytest -m integration

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📊 테스트 메트릭

### 커버리지 목표

- **전체 코드 커버리지**: 80% 이상
- **단위 테스트 커버리지**: 90% 이상
- **핵심 비즈니스 로직**: 95% 이상

### 성능 기준

- **API 응답 시간**: 1초 이내
- **DB 쿼리**: 500ms 이내
- **Agent 처리**: 30초 이내

## 🔍 디버깅 팁

### 실패한 테스트 디버깅

```bash
# 상세한 출력으로 실행
pytest -v -s

# 첫 번째 실패에서 중단
pytest -x

# 마지막 실패한 테스트만 재실행
pytest --lf

# 실패한 테스트들만 재실행
pytest --ff
```

### 로그 출력 확인

```bash
# 로그 출력과 함께 실행
pytest -s --log-cli-level=INFO
```

## 🧹 테스트 환경 정리

### 임시 파일 정리

```python
# conftest.py에서 자동 정리 설정
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # 테스트 후 정리 로직
```

### Mock 상태 초기화

```python
# setUp/tearDown 패턴
def setup_method(self):
    # 테스트 전 초기화
    pass

def teardown_method(self):
    # 테스트 후 정리
    pass
```

## ❓ 자주 묻는 질문

**Q: 테스트가 느려요. 어떻게 개선할 수 있나요?**
A:

- `pytest -m "not slow"` 로 빠른 테스트만 실행
- Mock을 적극 활용하여 외부 의존성 제거
- 병렬 실행 `pytest -n auto` 사용

**Q: Agent 테스트에서 LLM 호출 비용이 걱정됩니다.**
A:

- Mock LLM 클라이언트를 사용 (`mock_llm_client` fixture)
- 실제 LLM 호출은 `@pytest.mark.slow` 마커로 분리

**Q: 데이터베이스 테스트는 어떻게 격리하나요?**
A:

- 각 테스트마다 Mock Database 사용
- 실제 DB 테스트는 트랜잭션 롤백 활용
- 테스트용 별도 DB 스키마 사용

이 가이드를 참고하여 체계적이고 효율적인 테스트 코드를 작성하세요! 🎯
