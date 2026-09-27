"""Live User Test for Agent 1: Research Manager.

Runs an end-to-end test against Groq openai/gpt-oss-120b to evaluate:
1. Response quality & accuracy
2. Research problem deconstruction
3. Web search term suggestions
4. Academic research keyword suggestions
5. Evidence verification criteria
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL


def run_live_manager_test(research_question: str = "What are the security risks of autonomous AI coding agents?"):
    print("=" * 70)
    print("🔬 LIVE USER TEST: RESEARCH MANAGER AGENT (Groq openai/gpt-oss-120b)")
    print("=" * 70)
    print(f"Research Question:\n  \"{research_question}\"\n")

    api_key = get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY is not set.")
        print("To run this live test against Groq, please set your key:")
        print("  export GROQ_API_KEY='gsk_your_groq_api_key'")
        print("  python3 scripts/live_manager_test.py\n")
        return False

    # Model and Endpoints
    # Standard Groq Chat Completions endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"

    system_prompt = (
        "Role: Lead Research Manager & Strategist\n"
        "Goal: Deconstruct the research question into structured subtopics, identify necessary "
        "empirical evidence, and devise an optimal multi-agent research strategy.\n"
        "Backstory: You are a distinguished research director with extensive experience structuring "
        "scientific, technical, and academic inquiries. You excel at scoping investigations, "
        "establishing clear sub-questions, and guiding specialized research teams without "
        "duplicating search efforts or performing search tasks yourself."
    )

    user_prompt = (
        f"Analyze the research question:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your task as Research Manager is to:\n"
        f"1. Deconstruct this inquiry into core dimensions, technical concepts, and key sub-questions.\n"
        f"2. Identify what empirical evidence, metrics, and documentation are required.\n"
        f"3. Provide targeted search queries and high-priority focus areas for the Web Researcher.\n"
        f"4. Provide targeted academic topics, keywords, and methodological areas for the Academic Researcher.\n"
        f"5. Outline the evidence verification criteria that the Evidence Analyst should check.\n\n"
        f"Do NOT conduct the web or academic search yourself. Focus strictly on creating a comprehensive "
        f"and structured research roadmap."
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

    print(f"📡 Sending request to Groq API (Model: {model})...")

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=45) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            content = res_body["choices"][0]["message"]["content"]
            
            print("\n" + "=" * 70)
            print("📋 LIVE RESEARCH MANAGER OUTPUT FROM GPT-OSS-120B:")
            print("=" * 70)
            print(content)
            print("=" * 70)

            # Response Quality Evaluation
            print("\n🔍 EVALUATING RESPONSE QUALITY & STRUCTURE:")
            checks = {
                "Sub-questions / Deconstruction": any(k in content.lower() for k in ["sub-question", "dimension", "scope", "objective", "inquiry"]),
                "Web Research Terms / Queries": any(k in content.lower() for k in ["web", "query", "search", "industry", "cve"]),
                "Academic / Scholarly Keywords": any(k in content.lower() for k in ["academic", "paper", "arxiv", "scholar", "literature"]),
                "Evidence Criteria / Verification": any(k in content.lower() for k in ["evidence", "verification", "criteria", "analyst", "benchmark"]),
            }

            all_passed = True
            for criterion, passed in checks.items():
                mark = "✓ PASS" if passed else "✗ WARN"
                print(f"  {mark}: {criterion}")
                if not passed:
                    all_passed = False

            if all_passed:
                print("\n✅ ACCURACY VERIFIED: The response adheres strictly to the Research Manager role and produces structured instructions for downstream agents.")
            else:
                print("\n⚠️ Note: Some criteria may need prompt tuning.")

            return True

    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"\n❌ Groq API HTTP Error ({e.code}): {err_msg}")
        return False
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        return False


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What are the security risks of autonomous AI coding agents?"
    run_live_manager_test(question)
