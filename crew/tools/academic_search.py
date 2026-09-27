"""Academic Search Tool for Researcher AI.

Queries legitimate scholarly repositories (arXiv, OpenAlex, Crossref) for peer-reviewed
papers, technical preprints, author listings, abstracts, and DOIs.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from config import USER_AGENT, REQUEST_TIMEOUT

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


def search_arxiv(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Query the official arXiv API for scientific preprints and abstracts."""
    papers: List[Dict[str, Any]] = []
    clean_query = query.strip().strip('"').strip("'")
    if not clean_query:
        return papers

    encoded_query = urllib.parse.quote_plus(f"all:{clean_query}")
    url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"

    headers = {"User-Agent": USER_AGENT}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            xml_data = response.read().decode("utf-8")

        # Parse Atom XML
        root = ET.fromstring(xml_data)
        atom_ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", atom_ns):
            title_elem = entry.find("atom:title", atom_ns)
            summary_elem = entry.find("atom:summary", atom_ns)
            published_elem = entry.find("atom:published", atom_ns)
            id_elem = entry.find("atom:id", atom_ns)

            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled"
            summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
            published = published_elem.text.strip()[:10] if published_elem is not None and published_elem.text else "N/A"
            paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

            # Extract Authors
            authors = []
            for author_elem in entry.findall("atom:author", atom_ns):
                name_elem = author_elem.find("atom:name", atom_ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            papers.append({
                "title": title,
                "authors": authors[:5],
                "publication_date": published,
                "abstract": summary[:1200] + ("..." if len(summary) > 1200 else ""),
                "url": paper_url,
                "repository": "arXiv",
                "source_type": "academic_preprint",
            })

    except Exception:
        pass

    return papers


def search_openalex(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Query OpenAlex free academic catalog for published journal/conference papers."""
    papers: List[Dict[str, Any]] = []
    clean_query = query.strip().strip('"').strip("'")
    if not clean_query:
        return papers

    encoded = urllib.parse.quote_plus(clean_query)
    url = f"https://api.openalex.org/works?search={encoded}&per_page={max_results}&mailto=contact@example.com"

    headers = {"User-Agent": USER_AGENT}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        for work in data.get("results", []):
            title = work.get("title") or "Untitled"
            year = str(work.get("publication_year") or "N/A")
            doi = work.get("doi") or work.get("id") or ""
            
            # Extract authors
            authors = []
            for authorship in work.get("authorships", []):
                author_name = authorship.get("author", {}).get("display_name")
                if author_name:
                    authors.append(author_name)

            # Reconstruct abstract if available from inverted index
            abstract = ""
            inv_index = work.get("abstract_inverted_index")
            if inv_index:
                word_positions = []
                for word, pos_list in inv_index.items():
                    for pos in pos_list:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)[:1000]

            venue = work.get("primary_location", {}).get("source", {}) or {}
            venue_name = venue.get("display_name", "Academic Venue") if venue else "Academic Venue"

            papers.append({
                "title": title,
                "authors": authors[:5],
                "publication_year": year,
                "venue": venue_name,
                "abstract": abstract if abstract else "Abstract not directly indexed in metadata.",
                "url": doi if doi else f"https://openalex.org/{work.get('id', '')}",
                "repository": "OpenAlex",
                "source_type": "peer_reviewed_academic",
            })

    except Exception:
        pass

    return papers


def perform_academic_search(query: str, max_results: int = 5) -> str:
    """Perform a combined academic search over arXiv and OpenAlex."""
    clean_query = query.strip().strip('"').strip("'")
    if not clean_query:
        return json.dumps({"error": "Empty academic search query provided.", "papers": []})

    # 1. Search arXiv
    results = search_arxiv(clean_query, max_results=max_results)

    # 2. If arXiv has fewer than requested, enrich from OpenAlex
    if len(results) < max_results:
        openalex_results = search_openalex(clean_query, max_results=max_results - len(results))
        results.extend(openalex_results)

    if not results:
        return json.dumps({
            "message": f"No academic papers found for query: '{clean_query}'. Try broader scholarly keywords.",
            "papers": [],
        })

    return json.dumps({
        "query": clean_query,
        "total_papers_found": len(results),
        "papers": results,
    }, indent=2)


@tool("academic_search")
def academic_search_tool(query: str) -> str:
    """Search academic databases (arXiv, OpenAlex) for scientific papers, preprints, and abstracts.
    Pass scholarly keywords or paper topics (e.g., 'large language model code security vulnerability').
    Returns a JSON string containing paper titles, authors, publication dates, abstracts, and DOI/arXiv URLs.
    """
    return perform_academic_search(query, max_results=5)
