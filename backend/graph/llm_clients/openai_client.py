# llm_clients/openai_client.py
from langchain_openai import ChatOpenAI
import os


def get_openai_client(model_name: str = "gpt-4o-mini"):
    """OpenAI 클라이언트를 반환하는 함수"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            "다음 명령어로 설정하세요: export OPENAI_API_KEY='your-api-key'"
        )

    return ChatOpenAI(model=model_name, temperature=0.1, api_key=api_key)


# OpenAI API 키가 있을 때만 초기화
openai_llm = None
try:
    if os.getenv("OPENAI_API_KEY"):
        openai_llm = get_openai_client()
        print("✅ OpenAI 클라이언트 초기화 완료")
    else:
        print("⚠️  OPENAI_API_KEY not set. OpenAI 클라이언트를 사용하려면 API 키를 설정하세요.")
        print("   설정 방법: export OPENAI_API_KEY='your-api-key'")
except Exception as e:
    print(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
    openai_llm = None
