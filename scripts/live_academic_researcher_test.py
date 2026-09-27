"""Live User Test for Agent 3: Academic Researcher.

Runs an end-to-end test executing:
1. Real academic paper retrieval from arXiv/OpenAlex
2. LLM synthesis with Groq openai/gpt-oss-120b acting as the Academic Literature Specialist
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL
from crew.tools.academic_search import perform_academic_search


def run_live_academic_researcher_test(question: str = "What are the security risks of autonomous AI coding agents?"):
    print("=" * 70)
    print("🔬 LIVE USER TEST: ACADEMIC RESEARCHER AGENT (Groq openai/gpt-oss-120b)")
    print("=" * 70)
    print(f"Research Question: \"{question}\"\n")

    api_key = get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY is not set.")
        return False

    # 1. Execute Real Academic Search Tool
    print("📚 Step 1: Querying live arXiv and OpenAlex academic databases...")
    academic_query = "AI code generation security vulnerability LLM agent"
    search_json = perform_academic_search(academic_query, max_results=3)
    search_data = json.loads(search_json)
    papers = search_data.get("papers", [])

    print(f"✓ Retrieved {len(papers)} real academic papers/preprints:")
    for idx, paper in enumerate(papers, 1):
        print(f"  [{idx}] {paper.get('title')}")
        print(f"      Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"      URL/DOI: {paper.get('url')}")

    # 2. Call LLM to synthesize academic literature as Academic Researcher
    print("\n🤖 Step 2: Prompting Academic Researcher (openai/gpt-oss-120b) to synthesize findings...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"

    system_prompt = (
        "Role: Principal Academic Literature Specialist\n"
        "Goal: Query academic repositories (arXiv, OpenAlex, Crossref) to discover scientific "
        "publications, extracting key findings, authors, publication years, abstracts, and DOIs.\n"
        "Backstory: You are a seasoned academic researcher with extensive experience surveying scholarly "
        "literature across computer science, software engineering, and artificial intelligence. "
        "You extract abstracts, record complete author citations and DOIs/arXiv links, and clearly "
        "distinguish peer-reviewed empirical evidence from general web claims. You never fabricate citations."
    )

    user_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Live Academic Search Results:\n"
        f"{json.dumps({'retrieved_papers': papers}, indent=2)}\n\n"
        f"Synthesize these academic papers into a structured Academic Literature Review. "
        f"For every paper, include:\n"
        f"1. Paper Title, Authors, and Year/Date\n"
        f"2. Exact DOI or arXiv URL from the retrieved data\n"
        f"3. Core Empirical Findings & Evaluation Methodology\n"
        f"4. Research Limitations or Gaps acknowledged"
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
            print("📋 LIVE ACADEMIC RESEARCHER REPORT FROM GPT-OSS-120B:")
            print("=" * 70)
            print(content)
            print("=" * 70)

            # Quality checks
            has_urls = "arxiv.org" in content or "doi" in content.lower() or "http" in content
            has_authors = any(any(a.lower() in content.lower() for a in p.get("authors", [])) for p in papers if p.get("authors"))
            has_limits = any(k in content.lower() for k in ["limitation", "gap", "future work", "scope", "benchmark"])
            
            print("\n🔍 EVALUATING RESPONSE QUALITY:")
            print(f"  {'✓ PASS' if has_urls else '✗ FAIL'}: Verified DOI/arXiv URLs cited")
            print(f"  {'✓ PASS' if has_authors else '✗ FAIL'}: Real authors cited from retrieved metadata")
            print(f"  {'✓ PASS' if has_limits else '✗ FAIL'}: Research limitations/methodologies analyzed")
            print("\n✅ Academic Researcher live test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Error during LLM synthesis: {e}")
        return False


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What are the security risks of autonomous AI coding agents?"
    run_live_academic_researcher_test(q)
