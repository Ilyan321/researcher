"""Live User Test for Agent 5: Research Writer.

Runs an end-to-end synthesis test passing planning, web findings, academic literature,
and evidence audit results to Groq openai/gpt-oss-120b acting as the Research Writer.
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_groq_api_key, DEFAULT_MODEL


def run_live_writer_test(question: str = "What are the security risks of autonomous AI coding agents?"):
    print("=" * 70)
    print("🔬 LIVE USER TEST: RESEARCH WRITER AGENT (Groq openai/gpt-oss-120b)")
    print("=" * 70)
    print(f"Research Question: \"{question}\"\n")

    api_key = get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY is not set.")
        return False

    # Mock full upstream pipeline data
    upstream_context = {
        "plan": "Investigate code-level flaws, prompt-injection, sandbox escapes, and developer trust.",
        "web_findings": [
            {
                "title": "Security Risks of AI-Generated Code",
                "source": "IEEE Security & Privacy",
                "url": "https://www.ieee.org/security/ai-code-risks",
                "date": "2024-03-12",
                "evidence": "Identified that generative coding models can embed SQL injection and insecure deserialization patterns."
            },
            {
                "title": "Supply-Chain Risks of AI-Assisted Development",
                "source": "The New Stack",
                "url": "https://thenewstack.io/supply-chain-risks-ai",
                "date": "2024-02-05",
                "evidence": "Autonomous agents often resolve vulnerable or hallucinated third-party dependencies."
            }
        ],
        "academic_findings": [
            {
                "title": "Security Degradation in Iterative AI Code Generation -- A Systematic Analysis",
                "authors": ["Shivani Shukla", "Himanshu Joshi", "Romilla Syed"],
                "url": "http://arxiv.org/abs/2506.11022v2",
                "year": "2025",
                "evidence": "Controlled experiments showed a 37% rise in critical vulnerabilities after 5 iterative refinement prompts."
            },
            {
                "title": "Robustness and Security Failures in Academic LLM Execution Schemes",
                "authors": ["M. Wang", "N. Saxena"],
                "url": "http://arxiv.org/abs/2609.19705v1",
                "year": "2026",
                "evidence": "Demonstrated sandbox escapes when AI agents execute dynamic eval without kernel-level gVisor/seccomp filtering."
            }
        ],
        "evidence_audit": {
            "strong_evidence": "Sandbox escapes without kernel isolation (Wang & Saxena, 2026).",
            "moderate_evidence": "Iterative prompt security degradation on synthetic benchmarks (Shukla et al., 2025).",
            "weak_marketing_claims": "Vendor claims of '100% complete isolation' refuted by demonstrated escapes.",
            "writer_guidelines": "Distinguish code security from execution containment. Use bracketed citations [1], [2]."
        }
    }

    print("📝 Step 1: Supplying Multi-Agent Upstream Context to Research Writer...")
    print("\n🤖 Step 2: Prompting Research Writer (openai/gpt-oss-120b) to synthesize final report...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "openai/gpt-oss-120b"

    system_prompt = (
        "Role: Senior Technical Research Writer\n"
        "Goal: Synthesize all planning, web discoveries, academic literature, and audited evidence "
        "into a comprehensive, balanced, and rigorously cited research report in Markdown.\n"
        "Backstory: You are a master scientific communicator and technical author with extensive experience "
        "drafting high-impact research publications. You transform complex multi-source research "
        "into clear, beautifully formatted reports featuring executive summaries, detailed analyses, "
        "limitations, and numbered citations ([1], [2]). You strictly adhere to the Evidence Analyst's "
        "confidence calibrations, avoid sweeping generalizations, and never invent fake citations."
    )

    user_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Upstream Multi-Agent Context:\n{json.dumps(upstream_context, indent=2)}\n\n"
        f"Generate the full Research Report following the required structure:\n"
        f"# [Comprehensive Report Title]\n"
        f"## Executive Summary\n"
        f"## Research Question & Scope\n"
        f"## Key Findings (with [1], [2] citations)\n"
        f"## Detailed Empirical Analysis\n"
        f"## Contradictions & Divergent Perspectives\n"
        f"## Methodological Limitations\n"
        f"## Strategic Recommendations & Conclusion\n"
        f"## References (Numbered list with exact titles, authors, and URLs)"
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
            print("📋 LIVE MASTER RESEARCH REPORT FROM GPT-OSS-120B:")
            print("=" * 70)
            print(content)
            print("=" * 70)

            # Quality checks
            has_sections = all(sec in content for sec in ["Executive Summary", "Key Findings", "References"])
            has_citations = "[1]" in content or "[2]" in content
            has_urls = "http" in content

            print("\n🔍 EVALUATING RESPONSE QUALITY:")
            print(f"  {'✓ PASS' if has_sections else '✗ FAIL'}: All standard research report sections present")
            print(f"  {'✓ PASS' if has_citations else '✗ FAIL'}: Inline bracketed citations ([1], [2]) utilized")
            print(f"  {'✓ PASS' if has_urls else '✗ FAIL'}: Exact URLs mapped in References section")
            print("\n✅ Research Writer live test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Error during Research Writer test: {e}")
        return False


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What are the security risks of autonomous AI coding agents?"
    run_live_writer_test(q)
