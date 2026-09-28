"""Session, report, and chat history CRUD operations backed by Supabase."""

import logging
from typing import List, Dict, Any, Optional
from crew.memory.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def create_session(title: str) -> Optional[Dict[str, Any]]:
    """Create a new research session record and return the created session object."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("sessions").insert({"title": title}).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error creating session '{title}': {e}")

    return None


def get_all_sessions() -> List[Dict[str, Any]]:
    """Fetch all research sessions ordered by last updated."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        response = client.table("sessions").select("*").order("updated_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return []


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single session by its UUID."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("sessions").select("*").eq("id", session_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")

    return None


def delete_session(session_id: str) -> bool:
    """Delete a session and cascade delete all its reports, messages, and evidence."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("sessions").delete().eq("id", session_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return False


def save_report(session_id: str, markdown_content: str, version: int = 1) -> Optional[Dict[str, Any]]:
    """Save or update the compiled markdown report for a session."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        # Check if report already exists for this session
        existing = client.table("reports").select("id, version").eq("session_id", session_id).execute()
        if existing.data and len(existing.data) > 0:
            current_version = existing.data[0].get("version", 1)
            response = client.table("reports").update({
                "markdown_content": markdown_content,
                "version": current_version + 1,
            }).eq("session_id", session_id).execute()
        else:
            response = client.table("reports").insert({
                "session_id": session_id,
                "markdown_content": markdown_content,
                "version": version
            }).execute()

        # Update session updated_at timestamp
        client.table("sessions").update({"updated_at": "now()"}).eq("id", session_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error saving report for session {session_id}: {e}")

    return None


def get_report(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the latest report for a session."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("reports").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching report for session {session_id}: {e}")

    return None


def add_chat_message(session_id: str, role: str, content: str) -> Optional[Dict[str, Any]]:
    """Add a chat message (user, assistant, manager, writer, etc.) to the session history."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content
        }).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.error(f"Error adding message to session {session_id}: {e}")

    return None


def get_chat_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve all chat messages for a session ordered chronologically."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        response = client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching chat messages for session {session_id}: {e}")
        return []
