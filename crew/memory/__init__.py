"""Supabase and Agentic RAG Memory module."""

from crew.memory.supabase_client import get_supabase_client
from crew.memory.session_manager import (
    create_session,
    get_all_sessions,
    get_session,
    delete_session,
    save_report,
    get_report,
    add_chat_message,
    get_chat_messages,
)
from crew.memory.rag_memory import (
    store_evidence,
    recall_evidence,
    generate_embedding,
)

__all__ = [
    "get_supabase_client",
    "create_session",
    "get_all_sessions",
    "get_session",
    "delete_session",
    "save_report",
    "get_report",
    "add_chat_message",
    "get_chat_messages",
    "store_evidence",
    "recall_evidence",
    "generate_embedding",
]
