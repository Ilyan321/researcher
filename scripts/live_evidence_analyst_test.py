"""Live User Test for Agent 4: Evidence Analyst.

Runs an end-to-end test passing web findings and academic papers to Groq openai/gpt-oss-120b
acting as the Chief Evidence Analyst & Fact-Checker.
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL


def run_live_evidence_analyst_test(question: str = "What are the security risks of autonomous AI coding agents?"):
    print("=" * 70)
    print("🔬 LIVE USER TEST: EVIDENCE ANALYST AGENT (Groq openai/gpt-oss-120b)")
    print("=" * 70)
    print(f"Research Question: \"{question}\"\n")

    api_key = get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY is not set.")
        return False

    # Sample gathered findings from Web & Academic researchers
    web_evidence = [
        {
            "claim": "AI code generators introduce critical vulnerabilities in 40% of generated functions.",
            "source_title": "Security Risks of AI-Generated Code - Industry Whitepaper",
            "url": "https://example.com/industry-ai-report-2024",
            "type": "Industry Whitepaper",
            "date": "2024-03-12",
        },
        {
            "claim": "Vendor sandboxes provide 100% complete isolation against malicious AI execution.",
            "source_title": "Enterprise Cloud AI Sandbox Announcement",
            "url": "https://cloud.example.com/sandbox-announcement",
            "type": "Vendor Marketing Announcement",
            "date": "2024-04-09",
        }
    ]

    academic_evidence = [
        {
            "claim": "Iterative prompt refinement degrades code security, increasing critical bugs by 37% after 5 iterations across synthetic benchmark suites.",
            "paper_title": "Security Degradation in Iterative AI Code Generation -- A Systematic Analysis",
            "authors": ["Shivani Shukla", "Himanshu Joshi", "Romilla Syed"],
            "url": "http://arxiv.org/abs/2506.11022v2",
            "venue": "arXiv preprint 2025",
            "limitations": "Tested on synthetic benchmarks; real-world CI/CD interaction not fully modeled.",
        },
        {
            "claim": "Sandbox escapes remain a demonstrated vector when AI agents execute dynamic bash/python eval without kernel-level gVisor/seccomp filtering.",
            "paper_title": "Robustness and Security Failures in Academic LLM Execution Schemes",
            "authors": ["M. Wang", "N. Saxena"],
            "url": "http://arxiv.org/abs/2609.19705v1",
            "venue": "arXiv preprint 2026",
            "limitations": "Simulated sandbox environments with specific syscall restrictions.",
        }
    ]

    print("📊 Step 1: Supplying Web & Academic Findings to Evidence Analyst...")
    print(f"  - Web Findings: {len(web_evidence)} records")
    print(f"  - Academic Papers: {len(academic_evidence)} records")

    print("\n🤖 Step 2: Prompting Evidence Analyst (openai/gpt-oss-120b) to audit claims and detect contradictions...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"

    system_prompt = (
        "Role: Chief Evidence Analyst & Fact-Checker\n"
        "Goal: Critically audit gathered web and academic research, cross-examine claims against "
        "sources, detect contradictions and weak evidence, and calibrate claim certainty.\n"
        "Backstory: You are a meticulous epistemologist, scientific peer reviewer, and rigorous fact-checker. "
        "You scrutinize every finding made by researchers, cross-examining citations against source excerpts. "
        "You flag over-generalized conclusions (e.g. turning a single controlled study into a universal claim), "
        "detect conflicting findings between industry whitepapers and academic peer reviews, and clearly "
        "distinguish documented empirical data from vendor marketing or subjective opinions. You never invent evidence."
    )

    user_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Evidence:\n{json.dumps(web_evidence, indent=2)}\n\n"
        f"Academic Evidence:\n{json.dumps(academic_evidence, indent=2)}\n\n"
        f"Conduct a critical Evidence Audit. Produce:\n"
        f"1. Claim-by-Claim Verification & Calibration (distinguish marketing vs empirical proof)\n"
        f"2. Contradiction & Divergence Analysis (e.g. '100% sandbox isolation' vs academic escape vectors)\n"
        f"3. Confidence Calibration Matrix (Strong, Moderate, Contested, Weak)\n"
        f"4. Concrete Guidelines for the Research Writer (what can be stated with certainty vs caution)"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
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
            print("📋 LIVE EVIDENCE AUDIT REPORT FROM GPT-OSS-120B:")
            print("=" * 70)
            print(content)
            print("=" * 70)

            # Quality checks
            has_contradiction = any(k in content.lower() for k in ["contradiction", "divergence", "conflict", "discrepancy"])
            has_calibration = any(k in content.lower() for k in ["marketing", "over-generaliz", "caution", "vendor"])
            has_matrix = any(k in content.lower() for k in ["matrix", "tier", "strong", "moderate", "weak", "contested"])

            print("\n🔍 EVALUATING RESPONSE QUALITY:")
            print(f"  {'✓ PASS' if has_contradiction else '✗ FAIL'}: Detected contradiction between vendor marketing & academic escapes")
            print(f"  {'✓ PASS' if has_calibration else '✗ FAIL'}: Calibrated over-generalized assertions")
            print(f"  {'✓ PASS' if has_matrix else '✗ FAIL'}: Structured Confidence Calibration Matrix produced")
            print("\n✅ Evidence Analyst live test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Error during Evidence Analyst test: {e}")
        return False


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What are the security risks of autonomous AI coding agents?"
    run_live_evidence_analyst_test(q)
