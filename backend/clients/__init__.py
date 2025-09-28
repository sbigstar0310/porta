from clients.stock_client import StockClient
from clients.supabase_client import SupabaseClient


def get_stock_client() -> StockClient:
    return StockClient()


def get_supabase_client() -> SupabaseClient:
    return SupabaseClient()


__all__ = ["get_stock_client", "get_supabase_client"]
