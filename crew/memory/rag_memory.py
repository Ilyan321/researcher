"""RAG memory module for storing and retrieving evidence nodes via Supabase pgvector."""

import logging
from typing import List, Dict, Any, Optional
from crew.memory.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

_embedding_model = None


def get_embedding_model():
    """Lazily load the FastEmbed embedding model."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    try:
        from fastembed import TextEmbedding
        # BAAI/bge-small-en-v1.5 produces 384 dims.
        # We can also use standard text embeddings.
        _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return _embedding_model
    except Exception as e:
        logger.warning(f"FastEmbed initialization note: {e}")
        return None


def generate_embedding(text: str, target_dim: int = 1536) -> List[float]:
    """Generate a dense vector embedding for the given text.
    
    If local model produces 384 dimensions, it pads to target_dim (1536) for schema compatibility.
    """
    model = get_embedding_model()
    if model is not None:
        try:
            embeddings = list(model.embed([text]))
            if embeddings:
                raw_vector = list(embeddings[0])
                # Pad to target_dim if necessary
                if len(raw_vector) < target_dim:
                    raw_vector.extend([0.0] * (target_dim - len(raw_vector)))
                elif len(raw_vector) > target_dim:
                    raw_vector = raw_vector[:target_dim]
                return [float(x) for x in raw_vector]
        except Exception as e:
            logger.error(f"Error embedding text locally: {e}")

    # Fallback zero-vector if model fails to load
    return [0.0] * target_dim


def store_evidence(
    content: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Embed and store an evidence node in Supabase pgvector."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        embedding = generate_embedding(content)
        payload = {
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        if session_id:
            payload["session_id"] = session_id

        client.table("evidence_nodes").insert(payload).execute()
        return True
    except Exception as e:
        logger.error(f"Error storing evidence in Supabase: {e}")
        return False


def recall_evidence(
    query: str,
    session_id: Optional[str] = None,
    match_threshold: float = 0.1,
    match_count: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve relevant evidence nodes matching the query via Supabase RPC `match_evidence`."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        query_embedding = generate_embedding(query)
        params = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }
        if session_id:
            params["p_session_id"] = session_id

        response = client.rpc("match_evidence", params).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error recalling evidence from Supabase RPC: {e}")
        # Fallback to direct table select if RPC not yet created
        try:
            query_builder = client.table("evidence_nodes").select("id, session_id, content, metadata")
            if session_id:
                query_builder = query_builder.eq("session_id", session_id)
            fallback = query_builder.limit(match_count).execute()
            return fallback.data or []
        except Exception:
            return []
