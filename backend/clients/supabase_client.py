import os
from supabase import create_client, Client


class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )

    def get_client(self) -> Client:
        return self.client
