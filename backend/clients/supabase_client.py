import os
from supabase import create_client, Client


class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(f"Missing Supabase config: URL={bool(url)}, KEY={bool(key)}")
        self.client: Client = create_client(url, key)

    def get_client(self) -> Client:
        return self.client


class SupabaseAdminClient:
    """Admin 권한이 필요한 작업용 Supabase 클라이언트"""
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        # Service Role 키가 없으면 일반 키 사용 (fallback)
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not service_key:
            raise ValueError(f"Missing Supabase admin config: URL={bool(url)}, SERVICE_KEY={bool(service_key)}")
        self.client: Client = create_client(url, service_key)

    def get_client(self) -> Client:
        return self.client
