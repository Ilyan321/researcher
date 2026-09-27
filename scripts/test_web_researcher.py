"""Test harness for Agent 2: Web Researcher and Web Tools."""

import sys
import os
import json

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL
from crew.tools.web_search import perform_web_search, web_search_tool
from crew.tools.web_reader import read_url_content, web_reader_tool


def test_web_tools():
    """Verify web_search and web_reader tools with real HTTP queries."""
    print("=" * 70)
    print("🔬 TESTING PHASE 5: WEB RESEARCH TOOLS")
    print("=" * 70)

    # 1. Test Web Search Tool
    print("\n1. Testing 'perform_web_search' with query: 'autonomous AI coding agents security'...")
    search_json = perform_web_search("autonomous AI coding agents security", max_results=3)
    try:
        search_data = json.loads(search_json)
        results = search_data.get("results", [])
        print(f"✓ Received {len(results)} search results:")
        for idx, res in enumerate(results, 1):
            print(f"   [{idx}] {res.get('title')} -> {res.get('url')}")
            
        test_url = results[0]["url"] if results else "https://en.wikipedia.org/wiki/Artificial_intelligence"
    except Exception as e:
        print(f"⚠️ Search parser warning: {e}")
        test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

    # 2. Test Web Reader Tool
    print(f"\n2. Testing 'read_url_content' on URL: {test_url}...")
    reader_json = read_url_content(test_url, max_chars=800)
    try:
        reader_data = json.loads(reader_json)
        status = reader_data.get("status")
        title = reader_data.get("title")
        chars = reader_data.get("character_count", 0)
        print(f"✓ Reader Status: {status}")
        print(f"✓ Extracted Title: '{title}'")
        print(f"✓ Clean Text Length: {chars} chars")
        print(f"✓ Sample Snippet: {reader_data.get('content', '')[:180]}...")
    except Exception as e:
        print(f"✗ Reader error: {e}")
        return False

    print("\n✅ Web Tools verification completed successfully!")
    return True


if __name__ == "__main__":
    success = test_web_tools()
    sys.exit(0 if success else 1)
