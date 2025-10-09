from clients.stock_client import StockClient
from clients.supabase_client import SupabaseClient
from supabase import Client
from clients.email_client import EmailClient
from clients.cache_client import CacheClient


def get_stock_client() -> StockClient:
    return StockClient()


def get_supabase_client() -> Client:
    return SupabaseClient().get_client()


def get_supabase_admin_client() -> Client:
    from .supabase_client import SupabaseAdminClient
    return SupabaseAdminClient().get_client()


def get_email_client() -> EmailClient:
    return EmailClient()


def get_cache_client() -> CacheClient:
    return CacheClient()


__all__ = [
    "get_stock_client",
    "get_supabase_client",
    "get_email_client",
    "get_cache_client",
]
