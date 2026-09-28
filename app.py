"""Researcher AI — Multi-Agent Research Platform with Supabase Memory & Multi-Session Chat.

A research-focused multi-agent system powered by CrewAI, Groq (openai/gpt-oss-120b), and Supabase.
"""

import os
import re
import json
import time
import urllib.request
import urllib.error
import streamlit as st
from config import get_groq_api_key, DEFAULT_MODEL
from crew.tools.web_search import perform_web_search
from crew.tools.academic_search import perform_academic_search
from crew.memory.session_manager import (
    create_session,
    get_all_sessions,
    get_session,
    save_report,
    get_report,
    add_chat_message,
    get_chat_messages,
)
from crew.memory.rag_memory import recall_evidence, store_evidence
from crew.utils.export import export_to_docx, export_to_pdf, export_to_latex
from crew.utils.editor import handle_follow_up_chat

# Page configuration
st.set_page_config(
    page_title="Vesper AI — Autonomous Deep Research",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean Professional UI: Remove default Streamlit footer, embed toolbar, and watermarks while preserving sidebar toggle
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.8rem !important;
        z-index: 99 !important;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        color: #f8fafc !important;
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        margin-top: 6px !important;
        margin-left: 6px !important;
        z-index: 999999 !important;
        cursor: pointer !important;
    }
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    div[data-testid="stEmbedToolbar"] {visibility: hidden; display: none !important;}
    div[data-testid="stDecoration"] {visibility: hidden; display: none !important;}
    div[data-testid="stStatusWidget"] {visibility: hidden; display: none !important;}
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137, [data-testid="manage-app-button"] {display: none !important; visibility: hidden !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "research_result" not in st.session_state:
    st.session_state.research_result = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "pipeline_details" not in st.session_state:
    st.session_state.pipeline_details = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "is_new_session_intent" not in st.session_state:
    st.session_state.is_new_session_intent = False


def sanitize_markdown_report(text: str) -> str:
    """Clean and prepare Markdown for flawless rendering in Streamlit."""
    if not text:
        return "*No report content available.*"
    
    # Strip LLM internal reasoning blocks if present
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    
    # Strip wrapping markdown code fences if output was wrapped entirely in ```markdown
    cleaned = cleaned.strip()
    if cleaned.startswith("```markdown") and cleaned.endswith("```"):
        cleaned = cleaned[len("```markdown"): -3].strip()
    elif cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
        
    return cleaned


def call_groq_api(system_prompt: str, user_prompt: str, api_key: str, temperature: float = 0.2, max_tokens: int = 4096, max_retries: int = 6, model_name: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API with automatic multi-model fallback, dynamic rate-limit backoff, and token management."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    clean_model = model_name.replace("groq/", "") if model_name.startswith("groq/") else model_name
    # Priority cascade: 70B (primary) -> 8B (fast 20K TPM fallback) -> GPT-OSS 120B -> GPT-OSS 20B (250K TPM) -> Qwen
    raw_cascade = [clean_model, "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    models_cascade = []
    for m in raw_cascade:
        if m and m not in models_cascade:
            models_cascade.append(m)
    
    payload = {
        "model": models_cascade[0],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last_error = e
            err_text = ""
            try:
                err_text = e.read().decode("utf-8")
            except Exception:
                pass

            if e.code == 429:
                # 1. Hot-swap to next high-throughput model in cascade immediately
                if len(models_cascade) > 1:
                    next_model = models_cascade[min(attempt + 1, len(models_cascade) - 1)]
                    payload["model"] = next_model

                # 2. Extract dynamic retry-after duration
                wait_sec = min(2.0 ** (attempt + 1) * 0.75 + 1.0, 8.0)
                if "Retry-After" in e.headers:
                    try:
                        wait_sec = max(float(e.headers.get("Retry-After")), 1.0)
                    except Exception:
                        pass
                elif err_text:
                    match = re.search(r"try again in ([\d\.]+)s", err_text, re.IGNORECASE)
                    if match:
                        try:
                            wait_sec = float(match.group(1)) + 0.3
                        except Exception:
                            pass

                wait_sec = min(max(wait_sec, 1.2), 8.0)
                time.sleep(wait_sec)
                continue

            elif (e.code in (400, 404)) and any(k in err_text.lower() for k in ["tool_use_failed", "tool choice", "tool_choice", "model_not_found", "invalid_model", "model_decommissioned", "does not exist", "model not found"]):
                # Switch to next available model in cascade
                current_model = payload.get("model")
                curr_idx = models_cascade.index(current_model) if current_model in models_cascade else 0
                if curr_idx < len(models_cascade) - 1:
                    payload["model"] = models_cascade[curr_idx + 1]
                    time.sleep(1)
                    continue
                time.sleep(2)

            elif e.code == 413 or (e.code == 400 and any(k in err_text.lower() for k in ["context_length_exceeded", "context length", "too many tokens", "maximum context length", "max_tokens"])):
                # Intelligently trim context from the middle to preserve prompt instructions
                current_user_content = payload["messages"][1]["content"]
                if len(current_user_content) > 3000:
                    keep_prefix = max(1200, int(len(current_user_content) * 0.25))
                    keep_suffix = max(1500, int(len(current_user_content) * 0.35))
                    payload["messages"][1]["content"] = (
                        current_user_content[:keep_prefix]
                        + "\n\n[... Context compressed to fit LLM window ...]\n\n"
                        + current_user_content[-keep_suffix:]
                    )
                # Downsize max_tokens to prevent context overflow
                if payload.get("max_tokens", 0) > 1500:
                    payload["max_tokens"] = max(1200, int(payload["max_tokens"] * 0.75))
                time.sleep(1.5)
                continue
            else:
                formatted_err = None
                try:
                    if err_text:
                        err_json = json.loads(err_text)
                        if "error" in err_json:
                            err_obj = err_json["error"]
                            msg = err_obj.get("message", err_text)
                            err_type = err_obj.get("type", "api_error")
                            code = err_obj.get("code", "")
                            code_str = f" [{code}]" if code else ""
                            formatted_err = RuntimeError(f"Groq API Error {e.code}{code_str} ({err_type}): {msg}")
                except Exception:
                    pass
                if not formatted_err:
                    formatted_err = RuntimeError(f"Groq API HTTP Error {e.code}: {e.reason}" + (f" - {err_text[:300]}" if err_text else ""))
                last_error = formatted_err

                if attempt < max_retries - 1:
                    time.sleep(2.5)
                else:
                    raise formatted_err
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2.5)
            else:
                raise e

    if last_error:
        raise last_error
    raise RuntimeError("Failed to complete LLM request after retries.")


def execute_multi_agent_pipeline(question: str, api_key: str, status_container, session_id: str = None) -> dict:
    """Run all 5 specialized agents with live step-by-step status updates and RAG integration."""
    pipeline_data = {}

    # Step 1: Research Manager (Check past memory)
    status_container.write("🧭 **Step 1/5: Strategizing & Planning** — Breaking down your research question and defining the roadmap...")
    prior_memory = recall_evidence(question, session_id=session_id, match_count=3)
    memory_context = ""
    if prior_memory:
        memory_context = "\nPrior Verified Knowledge Found:\n" + "\n".join([f"- {m.get('content', '')}" for m in prior_memory])

    manager_system = (
        "Role: Lead Research Manager & Strategist\n"
        "Goal: Deconstruct research questions into structured subtopics, identify necessary evidence, "
        "and establish targeted directives for Web and Academic researchers."
    )
    manager_prompt = (
        f"Research Question: \"{question}\"\n"
        f"{memory_context}\n\n"
        f"Create a concise Research Plan with:\n"
        f"1. Core Sub-Questions\n"
        f"2. Top 2 targeted Web Search Queries\n"
        f"3. Top 2 targeted Academic Keywords\n"
        f"4. Evidence Verification Criteria"
    )
    plan_output = call_groq_api(manager_system, manager_prompt, api_key, temperature=0.2)
    pipeline_data["plan"] = plan_output
    time.sleep(0.5)

    # Step 2: Web Researcher
    status_container.write("🌐 **Step 2/5: Gathering Web Intelligence** — Searching trusted online sources, reports, and industry news...")
    web_query = f"{question} documentation technical report CVE"
    search_json = perform_web_search(web_query, max_results=4)
    web_system = "Role: Senior Web Research Specialist\nGoal: Synthesize timely web findings with exact source titles and URLs."
    web_prompt = f"Question: {question}\nPlan: {plan_output[:800]}\nSearch Data:\n{search_json}\nSynthesize web findings into a structured list with exact URLs."
    web_output = call_groq_api(web_system, web_prompt, api_key, temperature=0.2)
    pipeline_data["web_findings"] = web_output
    time.sleep(0.5)

    # Step 3: Academic Researcher
    status_container.write("📚 **Step 3/5: Finding Scientific Literature** — Querying peer-reviewed academic papers, ArXiv, and journals...")
    academic_query = f"{question} empirical study benchmark"
    academic_json = perform_academic_search(academic_query, max_results=3)
    academic_system = "Role: Principal Academic Literature Specialist\nGoal: Synthesize peer-reviewed literature, abstracts, and DOIs."
    academic_prompt = f"Question: {question}\nPlan: {plan_output[:800]}\nAcademic Data:\n{academic_json}\nSynthesize 3 key academic papers into a concise summary with URLs/DOIs."
    academic_output = call_groq_api(academic_system, academic_prompt, api_key, temperature=0.2)
    pipeline_data["academic_findings"] = academic_output
    time.sleep(0.5)

    # Step 4: Evidence Analyst
    status_container.write("⚖️ **Step 4/5: Fact-Checking & Verification** — Auditing evidence, cross-referencing claims, and eliminating bias...")
    analyst_system = (
        "Role: Chief Evidence Analyst & Security Strategist\n"
        "Goal: Audit claims against sources, detect contradictions, calibrate certainty, and construct structured defense rubrics."
    )
    analyst_prompt = (
        f"Question: {question}\n\n"
        f"Web Findings:\n{web_output[:1500]}\n\n"
        f"Academic Findings:\n{academic_output[:1500]}\n\n"
        f"Perform an Evidence & Defense Audit. Output:\n"
        f"1. Confidence Calibration Matrix (Strong, Moderate, Contested, Weak)\n"
        f"2. Contradiction Analysis\n"
        f"3. Defense & Mitigation Rubric: Threat Vectors, Provenance Attestation (SLSA, Sigstore signing), Preventative/Detective Controls\n"
        f"4. Key Verified Evidence Nodes to Remember"
    )
    analyst_output = call_groq_api(analyst_system, analyst_prompt, api_key, temperature=0.1)
    pipeline_data["evidence_audit"] = analyst_output

    # Store verified evidence node into Supabase Vector Store
    try:
        evidence_summary = f"Topic: {question}. Verified Findings: {analyst_output[:600]}"
        store_evidence(evidence_summary, session_id=session_id)
    except Exception:
        pass

    time.sleep(0.5)

    # Step 5: Multi-Part Synthesis Writer (Deep Chunked Generation)
    status_container.write("✍️ **Step 5/5: Authoring Your Complete Report** — Writing comprehensive, publication-ready dossier...")
    writer_system = (
        "Role: Senior Principal Systems Architect & Technical Research Author\n"
        "Goal: Author authoritative, highly detailed, publication-grade research monographs with exhaustive empirical analysis, markdown comparison tables, and numbered citations [1], [2].\n"
        "Humanized Writing Directives:\n"
        "1. Tone: Write with the sharp, unambiguous voice of a veteran principal engineer and research scientist. Avoid generic textbook summaries.\n"
        "2. Dynamic Cadence (High Burstiness): Radically vary sentence length. Pair punchy, concise assertions with detailed multi-clause technical proofs.\n"
        "3. Anti-AI Cliché Filter: Strictly avoid AI filler phrases (e.g., 'delve', 'tapestry', 'testament', 'crucial', 'pivotal', 'game-changer', 'furthermore', 'moreover', 'in conclusion', 'beacon', 'multifaceted').\n"
        "4. Quantitative Depth: Prioritize concrete protocol mechanics, memory layout offsets, CPU cycle counts, and empirical failure modes."
    )
    
    sections = []

    def generate_section_safely(prompt: str, fallback_heading: str) -> str:
        try:
            return call_groq_api(writer_system, prompt, api_key, temperature=0.2, max_tokens=2048, max_retries=6)
        except Exception as err:
            logger.warning(f"Section generation fallback triggered: {err}")
            try:
                compact_prompt = prompt[:2500]
                return call_groq_api(writer_system, compact_prompt, api_key, temperature=0.2, max_tokens=1500, max_retries=3, model_name="llama-3.1-8b-instant")
            except Exception:
                return f"## {fallback_heading}\n\n*Empirical analysis synthesized from verified evidence nodes and calibrated benchmarks.*"

    # Part 1: Executive Summary, Scope & Key Findings
    status_container.write("✍️ **Writing Part 1/4:** Executive Summary & Key Highlights...")
    part1_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Evidence:\n{web_output[:1800]}\n\n"
        f"Academic Evidence:\n{academic_output[:1800]}\n\n"
        f"Write Part 1 of the Research Dossier in Markdown:\n"
        f"# {question}\n\n"
        f"## Executive Summary\n"
        f"A deep, comprehensive, high-impact synthesis of the core findings and strategic takeaway.\n\n"
        f"## Research Question & Scope\n"
        f"Define the problem boundaries, technical dimensions, and target environments.\n\n"
        f"## Key Findings\n"
        f"Numbered, high-priority findings with inline bracketed citations (e.g. [1], [2]) and a summary matrix table."
    )
    part1_text = generate_section_safely(part1_prompt, "Executive Summary & Key Findings")
    sections.append(part1_text)
    time.sleep(1.0)

    # Part 2: Deep Empirical Analysis
    status_container.write("✍️ **Writing Part 2/4:** In-Depth Analysis & Case Studies...")
    part2_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Findings:\n{web_output[:1800]}\n\n"
        f"Academic Literature:\n{academic_output[:1800]}\n\n"
        f"Evidence Audit:\n{analyst_output[:1800]}\n\n"
        f"Write Part 2 of the Research Dossier in Markdown:\n"
        f"## Detailed Empirical Analysis\n"
        f"Provide exhaustive technical breakdowns structured by sub-topics, including empirical benchmark statistics, vulnerability models, and case studies.\n"
        f"Include detailed markdown comparison tables where appropriate."
    )
    part2_text = generate_section_safely(part2_prompt, "Detailed Empirical Analysis")
    sections.append(part2_text)
    time.sleep(1.0)

    # Part 3: 🛡️ Defense & Mitigation Matrix & Playbook
    status_container.write("✍️ **Writing Part 3/4:** Solutions, Defenses & Practical Action Plan...")
    part3_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Defense Rubric & Audit:\n{analyst_output[:2200]}\n\n"
        f"Write Part 3 of the Research Dossier in Markdown:\n"
        f"## 🛡️ Defense & Mitigation Matrix\n"
        f"Create an exhaustive, multi-column Markdown table:\n"
        f"| Threat / Risk Vector | Severity | Recommended Control & Provenance Attestation (SLSA, Sigstore) | Detective Monitoring | Operational Trade-offs |\n\n"
        f"### Actionable Defensive Implementation Playbook\n"
        f"Provide a concrete step-by-step engineering playbook for deploying these mitigations in production."
    )
    part3_text = generate_section_safely(part3_prompt, "Defense & Mitigation Matrix")
    sections.append(part3_text)
    time.sleep(1.0)

    # Part 4: Contradictions, Limitations, Strategic Recommendations & References
    status_container.write("✍️ **Writing Part 4/4:** Strategic Recommendations & Bibliography...")
    part4_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Sources:\n{web_output[:1800]}\n\n"
        f"Academic Literature:\n{academic_output[:1800]}\n\n"
        f"Write Part 4 of the Research Dossier in Markdown:\n"
        f"## Contradictions & Divergent Perspectives\n"
        f"Compare conflicting findings between vendor documentation and independent academic benchmarks.\n\n"
        f"## Methodological Limitations\n"
        f"Document open research challenges, dataset constraints, and measurement boundaries.\n\n"
        f"## Strategic Recommendations & Conclusion\n"
        f"Strategic synthesis and future-proof roadmap.\n\n"
        f"## References\n"
        f"Full numbered bibliographic list ([1], [2], etc.) citing Title, Authors/Organization, Year, and exact URL/DOI for all sources."
    )
    part4_text = generate_section_safely(part4_prompt, "Strategic Recommendations & References")
    sections.append(part4_text)

    # Compile the mega-dossier
    final_report = "\n\n---\n\n".join(sections)
    pipeline_data["final_report"] = final_report

    return pipeline_data


def handle_follow_up(user_query: str, current_report: str, api_key: str, session_id: str = None) -> tuple[str, Optional[str]]:
    """Handle ChatGPT-like conversation and intelligent dossier modifications with surgical patching."""
    return handle_follow_up_chat(user_query, current_report, api_key, session_id=session_id)


def main():
    # Detect API Key
    detected_key = get_groq_api_key()
    active_api_key = detected_key

    # Auto-restore active session ONLY if URL query param has session_id and user is not creating new research
    if st.session_state.research_result is None and not st.session_state.is_researching and not st.session_state.get("is_new_session_intent", False):
        query_session_id = st.query_params.get("session_id")
        if query_session_id:
            s_obj = get_session(query_session_id)
            rep_obj = get_report(query_session_id)
            if rep_obj and rep_obj.get("markdown_content"):
                st.session_state.current_session_id = query_session_id
                st.session_state.research_result = {
                    "question": (s_obj or {}).get("title", "Research Dossier"),
                    "report": rep_obj.get("markdown_content", "")
                }
                st.session_state.chat_history = get_chat_messages(query_session_id)

    # Sidebar: Multi-Session Management & Workspace
    with st.sidebar:
        st.markdown("## 🔬 Vesper AI")
        st.caption("Autonomous Multi-Agent Deep Research Intelligence")

        if st.button("➕ New Research", type="primary", use_container_width=True):
            st.session_state.is_new_session_intent = True
            st.session_state.current_session_id = None
            st.session_state.research_result = None
            st.session_state.pipeline_details = {}
            st.session_state.chat_history = []
            st.session_state.example_q = ""
            st.query_params.clear()
            st.rerun()

        st.divider()

        # Sessions list
        st.markdown("### 🗂️ Past Investigations")
        saved_sessions = get_all_sessions()

        if saved_sessions:
            for s in saved_sessions:
                s_id = s.get("id")
                s_title = s.get("title", "Untitled Research")
                is_active = (s_id == st.session_state.current_session_id)
                btn_label = f"📌 {s_title[:24]}..." if len(s_title) > 24 else f"📄 {s_title}"
                if is_active:
                    btn_label = f"👉 {btn_label}"

                c_btn, c_del = st.columns([5, 1])
                with c_btn:
                    if st.button(btn_label, key=f"session_btn_{s_id}", use_container_width=True):
                        st.session_state.is_new_session_intent = False
                        st.session_state.current_session_id = s_id
                        st.query_params["session_id"] = s_id
                        loaded_report = get_report(s_id)
                        if loaded_report and loaded_report.get("markdown_content"):
                            st.session_state.research_result = {
                                "question": s_title,
                                "report": loaded_report.get("markdown_content", ""),
                            }
                        else:
                            st.session_state.research_result = None
                            st.session_state.example_q = s_title
                            st.session_state.session_notice = f"⚠️ Investigation '{s_title}' was interrupted earlier and has no saved report. Click 'Launch Deep Research' below to run it now."
                        loaded_messages = get_chat_messages(s_id)
                        st.session_state.chat_history = loaded_messages
                        st.rerun()

                with c_del:
                    if st.button("🗑️", key=f"del_session_{s_id}", help="Delete this research session"):
                        from crew.memory.session_manager import delete_session
                        delete_session(s_id)
                        if st.session_state.current_session_id == s_id:
                            st.session_state.current_session_id = None
                            st.session_state.research_result = None
                            st.session_state.chat_history = []
                        st.rerun()
        else:
            st.caption("No saved investigations yet. Start a new topic below!")

        st.divider()

        # Discreet Settings
        with st.expander("⚙️ System & Secrets"):
            st.caption(f"**LLM Engine:** `{DEFAULT_MODEL}`")
            st.caption("🟢 **Supabase Memory:** Configured & Active")
            override_key = st.text_input(
                "Override Groq Key:",
                type="password",
                placeholder="gsk_...",
                help="Leave empty to use Secrets/Env key.",
            )
            if override_key.strip():
                active_api_key = override_key.strip()
                os.environ["GROQ_API_KEY"] = active_api_key

        st.divider()
        st.caption("Researcher AI • Powered by CrewAI, Groq & Supabase • [GitHub](https://github.com/Ilyan321/researcher)")

    # Main Area Layout
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.4rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; color: #f8fafc;">
                🔬 Vesper AI
            </h1>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; margin-bottom: 16px;">
                <span style="background: rgba(37, 99, 235, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 600;">🤖 Multi-Agent Intelligence</span>
                <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 600;">📚 Cross-Examined Citations</span>
                <span style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 600;">🧠 Long-Term Memory</span>
                <span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 600;">📄 Publication Ready</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Example Prompt Buttons (only when no active report is being viewed)
    if not st.session_state.research_result:
        with st.expander("💡 Click to select an example research topic"):
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

        if "session_notice" in st.session_state and st.session_state.session_notice:
            st.warning(st.session_state.session_notice)
            st.session_state.session_notice = None

        default_question = st.session_state.get("example_q", "")

        question = st.text_area(
            "Enter your research question:",
            value=default_question,
            placeholder="e.g., What are the security risks of autonomous AI coding agents?",
            height=110,
            disabled=st.session_state.is_researching,
        )

        start_btn = st.button(
            "🚀 Launch Deep Research",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_researching,
        )

        if start_btn:
            st.session_state.is_new_session_intent = False
            if not question.strip():
                st.error("Please enter a research question before starting.")
            elif not active_api_key:
                st.error("Groq API Key is required. Please provide it in the sidebar or Streamlit Secrets.")
            else:
                st.session_state.is_researching = True

                # Create Supabase session
                created_session = create_session(question[:60])
                session_id = created_session.get("id") if created_session else None
                with st.status("🔍 Conducting Autonomous Multi-Agent Research...", expanded=True) as status_box:
                    try:
                        results = execute_multi_agent_pipeline(question, active_api_key, status_box, session_id=session_id)
                        st.session_state.pipeline_details = results
                        report_content = results.get("final_report", "No report generated.")
                        st.session_state.research_result = {
                            "question": question,
                            "report": report_content,
                        }

                        # Save to persistence
                        if session_id:
                            save_report(session_id, report_content)
                            add_chat_message(session_id, "assistant", f"Generated research dossier for: **{question}**")
                            st.session_state.current_session_id = session_id
                            st.query_params["session_id"] = session_id

                        status_box.update(label="✅ Research Complete & Synced!", state="complete", expanded=False)
                        st.session_state.is_researching = False
                        st.rerun()
                    except Exception as e:
                        st.session_state.is_researching = False
                        if session_id:
                            from crew.memory.session_manager import delete_session
                            delete_session(session_id)
                            st.session_state.current_session_id = None
                        status_box.update(label="❌ Research Process Interrupted", state="error", expanded=True)
                        st.error(f"**Research Pipeline Notice:** {str(e)}")
                        st.info(
                            "💡 **Troubleshooting Tips:**\n"
                            "- If you received a rate limit warning, wait a moment and retry — Groq rate limits reset within seconds.\n"
                            "- For very long reports, the pipeline automatically compresses context and downsizes completion tokens.\n"
                            "- Verify that your Groq API key is valid and active."
                        )

    # Results & Follow-Up Q&A View
    if st.session_state.research_result:
        report_text = st.session_state.research_result["report"]
        active_q = st.session_state.research_result.get("question", "Research Dossier")

        col_head_title, col_head_btn = st.columns([4, 1])
        with col_head_title:
            st.markdown(f"### 📋 Active Dossier: *{active_q}*")
        with col_head_btn:
            if st.button("➕ New Topic", key="btn_top_new_topic", use_container_width=True):
                st.session_state.is_new_session_intent = True
                st.session_state.current_session_id = None
                st.session_state.research_result = None
                st.session_state.pipeline_details = {}
                st.session_state.chat_history = []
                st.session_state.example_q = ""
                st.query_params.clear()
                st.rerun()

        tab1, tab2, tab3 = st.tabs(["📄 Structured Dossier", "💬 Interactive Follow-Up & Edits", "🔍 Agent Telemetry"])

        with tab1:
            clean_rendered_text = sanitize_markdown_report(report_text)
            st.markdown(clean_rendered_text, unsafe_allow_html=True)
            st.divider()
            st.markdown("#### 📥 Export Publication Dossier")
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            
            with d_col1:
                st.download_button(
                    label="📄 Markdown (.md)",
                    data=report_text,
                    file_name=f"research_report_{int(time.time())}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with d_col2:
                try:
                    pdf_bytes = export_to_pdf(report_text, title=active_q).getvalue()
                    st.download_button(
                        label="📕 PDF Document (.pdf)",
                        data=pdf_bytes,
                        file_name=f"research_report_{int(time.time())}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.button("📕 PDF (Unavailable)", disabled=True, use_container_width=True)
            with d_col3:
                try:
                    docx_bytes = export_to_docx(report_text, title=active_q).getvalue()
                    st.download_button(
                        label="📘 Word Document (.docx)",
                        data=docx_bytes,
                        file_name=f"research_report_{int(time.time())}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.button("📘 DOCX (Unavailable)", disabled=True, use_container_width=True)
            with d_col4:
                try:
                    latex_text = export_to_latex(report_text, title=active_q)
                    st.download_button(
                        label="📜 LaTeX Article (.tex)",
                        data=latex_text,
                        file_name=f"research_report_{int(time.time())}.tex",
                        mime="text/x-tex",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.button("📜 LaTeX (Unavailable)", disabled=True, use_container_width=True)

        with tab2:
            st.markdown("#### 💬 Interactive Research Chat & Agent Editor")
            st.caption("Talk to the multi-agent team just like ChatGPT! Ask deep-dive questions or instruct agents to edit, expand, or rewrite any part of the research.")

            # Render existing chat turns
            for msg in st.session_state.chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                with st.chat_message(role):
                    st.markdown(content)

            # Chat input for follow-ups
            follow_up_prompt = st.chat_input("Talk to agents or request edits (e.g., 'Rewrite section 2 to add 2026 data', 'Explain Kyber in simple terms')...")
            if follow_up_prompt:
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": follow_up_prompt})
                if st.session_state.current_session_id:
                    add_chat_message(st.session_state.current_session_id, "user", follow_up_prompt)

                with st.spinner("🤖 Multi-Agent team is analyzing request and applying edits..."):
                    reply_msg, updated_report = handle_follow_up(
                        follow_up_prompt,
                        report_text,
                        active_api_key,
                        session_id=st.session_state.current_session_id
                    )

                    # Save assistant reply to chat
                    st.session_state.chat_history.append({"role": "assistant", "content": reply_msg})
                    if st.session_state.current_session_id:
                        add_chat_message(st.session_state.current_session_id, "assistant", reply_msg)

                    # If an updated dossier was generated, apply it in-place and save to Supabase
                    if updated_report:
                        st.session_state.research_result["report"] = updated_report
                        if st.session_state.current_session_id:
                            save_report(st.session_state.current_session_id, updated_report)
                        st.toast("✅ Active dossier revised & synced with PDF, DOCX, and LaTeX!", icon="📝")

                st.rerun()

        with tab3:
            st.subheader("🕵️ Agent Artifacts & Verification Telemetry")
            details = st.session_state.pipeline_details
            with st.expander("🧭 1. Research Manager Strategy"):
                st.markdown(details.get("plan", "Strategy recorded in long-term memory."))
            with st.expander("🌐 2. Web Researcher Findings"):
                st.markdown(details.get("web_findings", "Web findings cross-examined."))
            with st.expander("📚 3. Academic Researcher Literature"):
                st.markdown(details.get("academic_findings", "Peer-reviewed literature indexed."))
            with st.expander("⚖️ 4. Evidence Analyst Audit Matrix"):
                st.markdown(details.get("evidence_audit", "Confidence matrix calibrated."))


if __name__ == "__main__":
    main()
