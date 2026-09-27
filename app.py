"""Researcher AI — Multi-Agent Research Platform.

A research-focused multi-agent system powered by CrewAI and Groq (openai/gpt-oss-120b).
"""

import os
import json
import time
import urllib.request
import urllib.error
import streamlit as st
from config import get_groq_api_key, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from crew.tools.web_search import perform_web_search
from crew.tools.academic_search import perform_academic_search

# Page configuration
st.set_page_config(
    page_title="Researcher AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "research_result" not in st.session_state:
    st.session_state.research_result = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "pipeline_details" not in st.session_state:
    st.session_state.pipeline_details = {}


def call_groq_api(system_prompt: str, user_prompt: str, api_key: str, temperature: float = 0.2, max_retries: int = 5) -> str:
    """Call Groq API with automatic rate-limit backoff and token budget management."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ResearcherAI/1.0",
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_time = [6, 12, 20, 30, 45][attempt]
                time.sleep(wait_time)
            elif e.code == 413:
                # Truncate context if payload is too large
                payload["messages"][1]["content"] = user_prompt[:2500]
                time.sleep(2)
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise e

    raise RuntimeError("Failed to complete LLM request after retries.")


def execute_multi_agent_pipeline(question: str, api_key: str, status_container) -> dict:
    """Run all 5 specialized agents with live step-by-step status updates."""
    pipeline_data = {}

    # Step 1: Research Manager
    status_container.write("🧭 **Step 1/5: Research Manager** — Analyzing question and decomposing research strategy...")
    manager_system = (
        "Role: Lead Research Manager & Strategist\n"
        "Goal: Deconstruct research questions into structured subtopics, identify necessary evidence, "
        "and establish targeted directives for Web and Academic researchers."
    )
    manager_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Create a concise Research Plan with:\n"
        f"1. Core Sub-Questions\n"
        f"2. Top 2 targeted Web Search Queries\n"
        f"3. Top 2 targeted Academic Keywords\n"
        f"4. Evidence Verification Criteria"
    )
    plan_output = call_groq_api(manager_system, manager_prompt, api_key, temperature=0.2)
    pipeline_data["plan"] = plan_output
    time.sleep(1)

    # Step 2: Web Researcher
    status_container.write("🌐 **Step 2/5: Web Researcher** — Searching live web sources and inspecting documentation...")
    web_query = f"{question} documentation technical report CVE"
    search_json = perform_web_search(web_query, max_results=4)
    web_system = "Role: Senior Web Research Specialist\nGoal: Synthesize timely web findings with exact source titles and URLs."
    web_prompt = f"Question: {question}\nPlan: {plan_output[:800]}\nSearch Data:\n{search_json}\nSynthesize web findings into a structured list with exact URLs."
    web_output = call_groq_api(web_system, web_prompt, api_key, temperature=0.2)
    pipeline_data["web_findings"] = web_output
    time.sleep(1)

    # Step 3: Academic Researcher
    status_container.write("📚 **Step 3/5: Academic Researcher** — Querying arXiv and OpenAlex for peer-reviewed literature...")
    academic_query = f"{question} empirical study benchmark"
    academic_json = perform_academic_search(academic_query, max_results=3)
    academic_system = "Role: Principal Academic Literature Specialist\nGoal: Synthesize peer-reviewed literature, abstracts, and DOIs."
    academic_prompt = f"Question: {question}\nPlan: {plan_output[:800]}\nAcademic Data:\n{academic_json}\nSynthesize 3 key academic papers into a concise summary with URLs/DOIs."
    academic_output = call_groq_api(academic_system, academic_prompt, api_key, temperature=0.2)
    pipeline_data["academic_findings"] = academic_output
    time.sleep(1)

    # Step 4: Evidence Analyst
    status_container.write("⚖️ **Step 4/5: Evidence Analyst** — Auditing claims, checking contradictions, and calibrating certainty...")
    analyst_system = "Role: Chief Evidence Analyst & Fact-Checker\nGoal: Audit claims against sources, detect contradictions, and calibrate certainty."
    analyst_prompt = (
        f"Question: {question}\n\n"
        f"Web Findings:\n{web_output[:1500]}\n\n"
        f"Academic Findings:\n{academic_output[:1500]}\n\n"
        f"Perform an Evidence Audit. Output:\n"
        f"1. Confidence Calibration Matrix (Strong, Moderate, Contested, Weak)\n"
        f"2. Contradiction Analysis\n"
        f"3. Strict Directives for the Research Writer"
    )
    analyst_output = call_groq_api(analyst_system, analyst_prompt, api_key, temperature=0.1)
    pipeline_data["evidence_audit"] = analyst_output
    time.sleep(1)

    # Step 5: Research Writer
    status_container.write("✍️ **Step 5/5: Research Writer** — Compiling comprehensive cited research report...")
    writer_system = "Role: Senior Technical Research Writer\nGoal: Synthesize multi-agent research into a publication-grade Markdown report with numbered citations."
    writer_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Evidence:\n{web_output[:1800]}\n\n"
        f"Academic Evidence:\n{academic_output[:1800]}\n\n"
        f"Evidence Audit Matrix:\n{analyst_output[:1800]}\n\n"
        f"Produce the final Research Report in Markdown:\n"
        f"# [Title]\n"
        f"## Executive Summary\n"
        f"## Research Question & Scope\n"
        f"## Key Findings (with [1], [2] citations)\n"
        f"## Detailed Empirical Analysis\n"
        f"## Contradictions & Divergent Perspectives\n"
        f"## Methodological Limitations\n"
        f"## Strategic Recommendations & Conclusion\n"
        f"## References (Numbered list with URLs)"
    )
    final_report = call_groq_api(writer_system, writer_prompt, api_key, temperature=0.2)
    pipeline_data["final_report"] = final_report

    return pipeline_data


def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.caption("AI Model & Credentials")
        
        # Model info
        st.info(f"🧠 **Model:** `{DEFAULT_MODEL}`\n\n⚡ Ultra-fast LPU inference via Groq", icon="🤖")

        detected_key = get_groq_api_key()
        
        if detected_key:
            # Secrets / Env key detected cleanly
            masked = f"{detected_key[:6]}...{detected_key[-4:]}" if len(detected_key) > 10 else "••••••••"
            st.success(f"**API Key Active**\n\nLoaded from Secrets (`{masked}`)", icon="🔒")
            
            with st.expander("✏️ Override with custom key"):
                override_key = st.text_input(
                    "Custom Groq API Key:",
                    type="password",
                    placeholder="gsk_...",
                    help="Leave blank to use the Secrets key.",
                )
            active_api_key = override_key.strip() if override_key.strip() else detected_key
        else:
            # No key in secrets
            st.warning("No API Key found in Secrets", icon="⚠️")
            active_api_key = st.text_input(
                "Enter Groq API Key:",
                type="password",
                placeholder="gsk_...",
                help="Get your free API key at console.groq.com",
            ).strip()
            
            if active_api_key:
                st.success("API Key Provided", icon="✅")
            else:
                st.caption("💡 *Tip: Add `GROQ_API_KEY` to Streamlit Secrets to skip manual entry.*")

        if active_api_key:
            os.environ["GROQ_API_KEY"] = active_api_key

        st.divider()
        st.markdown("### 👥 Multi-Agent Research Team")
        st.markdown("- 🧭 **Research Manager**: Scopes investigation & strategy")
        st.markdown("- 🌐 **Web Researcher**: Live web discovery & URL inspection")
        st.markdown("- 📚 **Academic Researcher**: arXiv & OpenAlex paper retrieval")
        st.markdown("- ⚖️ **Evidence Analyst**: Fact-checking & contradiction audit")
        st.markdown("- ✍️ **Research Writer**: Publication-grade report compilation")

    # Main Layout
    st.title("🔬 Researcher AI")
    st.caption("Autonomous Multi-Agent Research Team powered by Groq & CrewAI")

    # Example Inquiries
    with st.expander("💡 Click to view example research inquiries"):
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            if st.button("AI Coding Agent Security", use_container_width=True):
                st.session_state.example_q = "What are the security risks of autonomous AI coding agents?"
        with col_e2:
            if st.button("AI Memory Architectures", use_container_width=True):
                st.session_state.example_q = "Compare the current approaches to AI agent memory systems."
        with col_e3:
            if st.button("Developer Productivity Impact", use_container_width=True):
                st.session_state.example_q = "What are the benefits and empirical limitations of AI coding assistants?"

    default_question = st.session_state.get("example_q", "")

    # Input Box
    question = st.text_area(
        "Enter your research question:",
        value=default_question,
        placeholder="e.g., What are the security risks of autonomous AI coding agents?",
        height=100,
        disabled=st.session_state.is_researching,
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        start_btn = st.button(
            "🚀 Start Research",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_researching,
        )
    with col2:
        if st.session_state.research_result:
            if st.button("🔄 New Research", use_container_width=False):
                st.session_state.research_result = None
                st.session_state.pipeline_details = {}
                st.session_state.example_q = ""
                st.rerun()

    # Execution Trigger
    if start_btn:
        if not question.strip():
            st.error("Please enter a research question before starting.")
        elif not active_api_key:
            st.error("Groq API Key is required. Please provide it in the sidebar or Streamlit Secrets.")
        else:
            st.session_state.is_researching = True
            
            with st.status("🔍 Conducting Autonomous Multi-Agent Research...", expanded=True) as status_box:
                try:
                    results = execute_multi_agent_pipeline(question, active_api_key, status_box)
                    st.session_state.pipeline_details = results
                    st.session_state.research_result = {
                        "question": question,
                        "report": results.get("final_report", "No report generated."),
                    }
                    status_box.update(label="✅ Research Complete!", state="complete", expanded=False)
                except Exception as e:
                    status_box.update(label="❌ Research Process Interrupted", state="error", expanded=True)
                    st.error(f"Error during research execution: {str(e)}")
                finally:
                    st.session_state.is_researching = False
                    st.rerun()

    # Results Display
    if st.session_state.research_result:
        st.divider()
        report_text = st.session_state.research_result["report"]

        tab1, tab2, tab3 = st.tabs(["📄 Structured Report", "🔍 Agent Pipeline Telemetry", "📥 Raw Markdown"])
        
        with tab1:
            st.markdown(report_text)
            st.download_button(
                label="📥 Download Research Report (.md)",
                data=report_text,
                file_name="researcher_ai_report.md",
                mime="text/markdown",
            )

        with tab2:
            st.subheader("🕵️ Agent Artifacts & Intermediate Evidence")
            details = st.session_state.pipeline_details
            
            with st.expander("🧭 1. Research Manager Strategy"):
                st.markdown(details.get("plan", "N/A"))

            with st.expander("🌐 2. Web Researcher Findings"):
                st.markdown(details.get("web_findings", "N/A"))

            with st.expander("📚 3. Academic Researcher Literature"):
                st.markdown(details.get("academic_findings", "N/A"))

            with st.expander("⚖️ 4. Evidence Analyst Audit Matrix"):
                st.markdown(details.get("evidence_audit", "N/A"))

        with tab3:
            st.code(report_text, language="markdown")


if __name__ == "__main__":
    main()
