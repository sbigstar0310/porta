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
