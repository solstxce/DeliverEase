from supabase import create_client, Client
from app.config import Config

def get_supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY) 