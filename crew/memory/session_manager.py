"""Session, report, and chat history CRUD operations with dual Supabase + Local persistence."""

import os
import json
import uuid
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from crew.memory.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

LOCAL_SESSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".sessions"))


def _ensure_local_dir():
    os.makedirs(LOCAL_SESSIONS_DIR, exist_ok=True)


def _get_local_session_dir(session_id: str) -> str:
    _ensure_local_dir()
    s_dir = os.path.join(LOCAL_SESSIONS_DIR, session_id)
    os.makedirs(s_dir, exist_ok=True)
    return s_dir


def create_session(title: str) -> Optional[Dict[str, Any]]:
    """Create a new research session record and return the created session object."""
    session_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    session_data = {
        "id": session_id,
        "title": title,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    # 1. Save locally
    try:
        s_dir = _get_local_session_dir(session_id)
        with open(os.path.join(s_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving local session meta: {e}")

    # 2. Sync to Supabase
    client = get_supabase_client()
    if client:
        try:
            response = client.table("sessions").insert({"id": session_id, "title": title}).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error(f"Error creating Supabase session '{title}': {e}")

    return session_data


def get_all_sessions() -> List[Dict[str, Any]]:
    """Fetch all research sessions ordered by last updated (merging Supabase & local)."""
    sessions_by_id = {}

    # 1. Load local sessions
    _ensure_local_dir()
    try:
        for s_id in os.listdir(LOCAL_SESSIONS_DIR):
            meta_path = os.path.join(LOCAL_SESSIONS_DIR, s_id, "meta.json")
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        sessions_by_id[s_id] = meta
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error loading local sessions: {e}")

    # 2. Load Supabase sessions
    client = get_supabase_client()
    if client:
        try:
            response = client.table("sessions").select("*").order("updated_at", desc=True).execute()
            for s in (response.data or []):
                sessions_by_id[s["id"]] = s
        except Exception as e:
            logger.error(f"Error fetching Supabase sessions: {e}")

    session_list = list(sessions_by_id.values())
    session_list.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
    return session_list


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single session by its UUID."""
    # 1. Check Supabase
    client = get_supabase_client()
    if client:
        try:
            response = client.table("sessions").select("*").eq("id", session_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error(f"Error fetching session {session_id} from Supabase: {e}")

    # 2. Check local
    meta_path = os.path.join(LOCAL_SESSIONS_DIR, session_id, "meta.json")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return None


def delete_session(session_id: str) -> bool:
    """Delete a session and cascade delete all its reports, messages, and evidence."""
    # 1. Delete local
    s_dir = os.path.join(LOCAL_SESSIONS_DIR, session_id)
    if os.path.exists(s_dir):
        try:
            shutil.rmtree(s_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error deleting local session dir: {e}")

    # 2. Delete Supabase
    client = get_supabase_client()
    if client:
        try:
            client.table("sessions").delete().eq("id", session_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting Supabase session {session_id}: {e}")

    return True


def save_report(session_id: str, markdown_content: str, version: int = 1) -> Optional[Dict[str, Any]]:
    """Save or update the compiled markdown report for a session (local + Supabase)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    report_data = {
        "session_id": session_id,
        "markdown_content": markdown_content,
        "version": version,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    # 1. Save locally
    try:
        s_dir = _get_local_session_dir(session_id)
        with open(os.path.join(s_dir, "report.md"), "w", encoding="utf-8") as f:
            f.write(markdown_content)

        meta_path = os.path.join(s_dir, "meta.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["updated_at"] = now_iso
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error saving local report: {e}")

    # 2. Save to Supabase
    client = get_supabase_client()
    if client:
        try:
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

            client.table("sessions").update({"updated_at": "now()"}).eq("id", session_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error(f"Error saving report to Supabase {session_id}: {e}")

    return report_data


def get_report(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the latest report for a session (from Supabase or local disk)."""
    # 1. Try Supabase
    client = get_supabase_client()
    if client:
        try:
            response = client.table("reports").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
            if response.data and len(response.data) > 0 and response.data[0].get("markdown_content"):
                return response.data[0]
        except Exception as e:
            logger.error(f"Error fetching Supabase report {session_id}: {e}")

    # 2. Try local file
    report_path = os.path.join(LOCAL_SESSIONS_DIR, session_id, "report.md")
    if os.path.isfile(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                return {
                    "session_id": session_id,
                    "markdown_content": content,
                    "version": 1
                }
        except Exception as e:
            logger.error(f"Error reading local report: {e}")

    return None


def add_chat_message(session_id: str, role: str, content: str) -> Optional[Dict[str, Any]]:
    """Add a chat message (user, assistant, manager, writer, etc.) to the session history."""
    now_iso = datetime.now(timezone.utc).isoformat()
    msg_data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": now_iso
    }

    # 1. Save local
    try:
        s_dir = _get_local_session_dir(session_id)
        chat_path = os.path.join(s_dir, "chat.json")
        messages = []
        if os.path.isfile(chat_path):
            with open(chat_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
        messages.append(msg_data)
        with open(chat_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving local chat message: {e}")

    # 2. Save to Supabase
    client = get_supabase_client()
    if client:
        try:
            response = client.table("chat_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content
            }).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.error(f"Error adding message to Supabase {session_id}: {e}")

    return msg_data


def get_chat_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve all chat messages for a session ordered chronologically."""
    # 1. Try Supabase
    client = get_supabase_client()
    if client:
        try:
            response = client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
            if response.data and len(response.data) > 0:
                return response.data
        except Exception as e:
            logger.error(f"Error fetching Supabase chat messages {session_id}: {e}")

    # 2. Try local
    chat_path = os.path.join(LOCAL_SESSIONS_DIR, session_id, "chat.json")
    if os.path.isfile(chat_path):
        try:
            with open(chat_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return []
