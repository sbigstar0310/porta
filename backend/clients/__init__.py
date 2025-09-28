from clients.stock_client import StockClient
from clients.supabase_client import SupabaseClient
from supabase import Client
from clients.email_client import EmailClient


def get_stock_client() -> StockClient:
    return StockClient()


def get_supabase_client() -> Client:
    return SupabaseClient().get_client()


def get_email_client() -> EmailClient:
    return EmailClient()


__all__ = [
    "get_stock_client",
    "get_supabase_client",
    "get_email_client",
]
