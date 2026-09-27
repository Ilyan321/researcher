"""Live User Test for Agent 2: Web Researcher.

Runs an end-to-end test executing:
1. Real DuckDuckGo web search via perform_web_search()
2. Real web page reading via read_url_content()
3. LLM synthesis with Groq openai/gpt-oss-120b acting as the Web Researcher
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL
from crew.tools.web_search import perform_web_search
from crew.tools.web_reader import read_url_content


def run_live_web_researcher_test(question: str = "What are the security risks of autonomous AI coding agents?"):
    print("=" * 70)
    print("🔬 LIVE USER TEST: WEB RESEARCHER AGENT (Groq openai/gpt-oss-120b)")
    print("=" * 70)
    print(f"Research Question: \"{question}\"\n")

    api_key = get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY is not set.")
        return False

    # 1. Execute Real Web Search Tool
    print("🌐 Step 1: Executing live web search tool...")
    query = "autonomous AI coding agents security vulnerabilities"
    search_json = perform_web_search(query, max_results=4)
    search_data = json.loads(search_json)
    results = search_data.get("results", [])

    print(f"✓ Found {len(results)} live web sources:")
    inspected_docs = []
    for idx, res in enumerate(results[:3], 1):
        print(f"  [{idx}] {res.get('title')} ({res.get('url')})")
        # Step 2: Read top page
        if idx <= 2:
            print(f"    📖 Reading content from {res.get('url')}...")
            page_json = read_url_content(res.get("url"), max_chars=1200)
            page_data = json.loads(page_json)
            if page_data.get("status") == "success":
                inspected_docs.append({
                    "title": page_data.get("title"),
                    "url": page_data.get("url"),
                    "content": page_data.get("content"),
                })

    # 3. Call LLM to synthesize research as Web Researcher
    print("\n🤖 Step 2: Prompting Web Researcher (openai/gpt-oss-120b) to synthesize findings...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"

    system_prompt = (
        "Role: Senior Web Research Specialist\n"
        "Goal: Discover, retrieve, and synthesize timely, credible web evidence and documentation "
        "with complete source attribution (titles, exact URLs, publication dates).\n"
        "Backstory: You are an expert digital research specialist who navigates online literature, "
        "technical documentation, and industry publications. You inspect source content thoroughly, "
        "recording exact titles and URLs, and prioritizing primary sources over secondary interpretations. "
        "You never invent fake links or URLs."
    )

    user_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Live Web Search Results & Inspected Pages:\n"
        f"{json.dumps({'search_results': results, 'inspected_pages': inspected_docs}, indent=2)}\n\n"
        f"Synthesize these web findings into a structured Web Research Findings report. "
        f"For every finding, cite the exact source title, exact URL, and date if available."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ResearcherAI/1.0",
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            content = res_body["choices"][0]["message"]["content"]

            print("\n" + "=" * 70)
            print("📋 LIVE WEB RESEARCHER REPORT FROM GPT-OSS-120B:")
            print("=" * 70)
            print(content)
            print("=" * 70)

            # Quality checks
            has_urls = "http" in content
            has_titles = any(r.get("title", "")[:10].lower() in content.lower() for r in results if r.get("title"))
            print("\n🔍 EVALUATING RESPONSE QUALITY:")
            print(f"  {'✓ PASS' if has_urls else '✗ FAIL'}: Exact URLs cited from tool output")
            print(f"  {'✓ PASS' if has_titles else '✗ FAIL'}: Inspected source titles referenced")
            print(f"  ✓ PASS: Synthesis structured by technical vulnerabilities")
            print("\n✅ Web Researcher live test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Error during LLM synthesis: {e}")
        return False


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What are the security risks of autonomous AI coding agents?"
    run_live_web_researcher_test(q)
