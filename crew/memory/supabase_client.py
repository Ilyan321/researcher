"""Supabase client initialization and management."""

import logging
from typing import Optional
from config import get_supabase_credentials

logger = logging.getLogger(__name__)

_supabase_client = None


def get_supabase_client():
    """Return a singleton Supabase client instance or None if unconfigured/failed."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url, key = get_supabase_credentials()
    if not url or not key:
        logger.warning("Supabase URL or Key not provided. Cloud memory will be disabled.")
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None
