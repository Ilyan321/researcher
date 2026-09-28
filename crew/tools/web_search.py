"""Web Search Tool for Researcher AI.

Searches the web using DuckDuckGo and free search APIs, returning structured results
containing titles, URLs, snippets, and source types.
"""

import json
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any

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


def perform_web_search(query: str, max_results: int = 5) -> str:
    """Execute a web search using DuckDuckGo/Wikipedia and return formatted results."""
    raw_query = query.strip().strip('"').strip("'")
    if not raw_query:
        return json.dumps({"error": "Empty search query provided.", "results": []})

    # Prune full paragraph queries down to high-precision search keywords
    clean_query = raw_query
    if len(raw_query.split()) > 8:
        words = [w for w in re.findall(r'\b[A-Za-z0-9\-_]{3,}\b', raw_query) if w.lower() not in {"deep", "research", "analyze", "empirical", "design", "novel", "beyond", "what", "which", "how", "create", "creating"}]
        clean_query = " ".join(words[:6]) if words else raw_query[:50]

    results: List[Dict[str, Any]] = []

    # 1. Try DuckDuckGo Python Library if installed (with 5s timeout)
    try:
        from duckduckgo_search import DDGS
        with DDGS(timeout=5) as ddgs:
            raw_results = list(ddgs.text(clean_query, max_results=max_results))
            for item in raw_results:
                results.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("href", item.get("link", "")),
                    "snippet": item.get("body", item.get("snippet", "")),
                    "source_type": "web",
                })
    except Exception:
        pass

    # 2. Fallback: DuckDuckGo Instant Answer API / Wikipedia Search API
    if not results:
        try:
            # Try Wikipedia OpenSearch for high-authority foundational technical articles
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote_plus(clean_query)}&limit={max_results}&namespace=0&format=json"
            req = urllib.request.Request(wiki_url, headers={"User-Agent": "ResearcherAI/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                wiki_data = json.loads(resp.read().decode("utf-8"))
                if len(wiki_data) >= 4:
                    titles = wiki_data[1]
                    snippets = wiki_data[2]
                    urls = wiki_data[3]
                    for t, s, u in zip(titles, snippets, urls):
                        results.append({
                            "title": t,
                            "url": u,
                            "snippet": s if s else f"Wikipedia technical reference for {t}",
                            "source_type": "encyclopedic_web",
                        })
        except Exception:
            pass

    if not results:
        return json.dumps({
            "message": f"No web results found for query: '{clean_query}'",
            "results": [],
        })

    return json.dumps({"query": clean_query, "total_results": len(results), "results": results}, indent=2)


@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the web for recent articles, documentation, industry reports, and factual sources.
    Pass a concise keyword query (e.g. 'autonomous AI coding agents security vulnerabilities').
    Returns a JSON string of search results with titles, URLs, and snippets.
    """
    return perform_web_search(query, max_results=5)
