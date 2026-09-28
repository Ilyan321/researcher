"""Agentic Memory and Vector Search Tools for CrewAI."""

import json
from typing import Optional

try:
    from crewai.tools import tool
except ImportError:
    def tool(name_or_func=None):
        def decorator(func):
            func.is_tool = True
            return func
        if callable(name_or_func):
            return decorator(name_or_func)
        return decorator

from crew.memory.rag_memory import recall_evidence, store_evidence


@tool("recall_past_research")
def recall_past_research_tool(query: str) -> str:
    """Search long-term agentic memory in Supabase pgvector for previously discovered research, facts, and citations.
    Useful before conducting redundant web or academic searches.
    Pass a semantic query describing the concept or question.
    """
    clean_query = query.strip()
    if not clean_query:
        return json.dumps({"error": "Empty search query provided.", "results": []})

    results = recall_evidence(clean_query, match_count=4)
    if not results:
        return json.dumps({
            "message": f"No prior memory or verified nodes found for query: '{clean_query}'. Proceed with fresh searches.",
            "results": []
        })

    formatted = []
    for item in results:
        formatted.append({
            "content": item.get("content", ""),
            "metadata": item.get("metadata", {}),
            "similarity": round(item.get("similarity", 0.0), 3)
        })

    return json.dumps({"query": clean_query, "matched_nodes": formatted}, indent=2)


@tool("store_verified_evidence")
def store_verified_evidence_tool(evidence_text: str) -> str:
    """Store a key verified fact, statistic, or academic finding into long-term cloud vector memory (Supabase).
    Pass a clear, self-contained summary of the verified finding.
    """
    clean_text = evidence_text.strip()
    if not clean_text:
        return json.dumps({"error": "No content provided to store."})

    success = store_evidence(clean_text)
    if success:
        return json.dumps({"status": "success", "message": "Evidence node successfully indexed into long-term vector memory."})
    else:
        return json.dumps({"status": "skipped", "message": "Evidence recorded locally; cloud memory unconfigured or unavailable."})
