"""Test harness for Academic Search Tool (arXiv + OpenAlex)."""

import sys
import os
import json

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crew.tools.academic_search import perform_academic_search, search_arxiv, search_openalex


def test_academic_search():
    print("=" * 70)
    print("🔬 TESTING PHASE 6: ACADEMIC SEARCH TOOL (arXiv & OpenAlex)")
    print("=" * 70)

    query = "large language model code security vulnerability"
    print(f"\n1. Querying live academic databases for: '{query}'...")

    result_json = perform_academic_search(query, max_results=3)
    try:
        data = json.loads(result_json)
        papers = data.get("papers", [])
        print(f"✓ Retrieved {len(papers)} academic papers/preprints:")
        for idx, paper in enumerate(papers, 1):
            print(f"\n  [{idx}] {paper.get('title')}")
            print(f"      Authors: {', '.join(paper.get('authors', [])[:3])}")
            print(f"      Date/Year: {paper.get('publication_date') or paper.get('publication_year')}")
            print(f"      Repo/Venue: {paper.get('repository')}")
            print(f"      URL/DOI: {paper.get('url')}")
            print(f"      Abstract: {paper.get('abstract', '')[:140]}...")

        if papers:
            print("\n✅ Academic Search tool test PASSED with live scholarly records!")
            return True
        else:
            print("\n⚠️ Note: No papers returned.")
            return False

    except Exception as e:
        print(f"✗ Error parsing academic search results: {e}")
        return False


if __name__ == "__main__":
    success = test_academic_search()
    sys.exit(0 if success else 1)
