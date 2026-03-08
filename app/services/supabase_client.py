from supabase import create_client, Client

import config

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        if not config.DB_PROJECT_URL or not config.DB_API_KEY:
            raise ValueError("Missing DB_PROJECT_URL or DB_API_KEY in env")
        _client = create_client(config.DB_PROJECT_URL, config.DB_API_KEY)
    return _client
