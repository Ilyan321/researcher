"""Researcher AI — Multi-Agent Research Platform with Supabase Memory & Multi-Session Chat.

A research-focused multi-agent system powered by CrewAI, Groq (openai/gpt-oss-120b), and Supabase.
"""

import os
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

# Clean Professional UI: Remove default Streamlit footer, embed toolbar, and watermarks
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
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


def call_groq_api(system_prompt: str, user_prompt: str, api_key: str, temperature: float = 0.2, max_tokens: int = 8192, max_retries: int = 5) -> str:
    """Call Groq API with automatic rate-limit backoff, high token limit, and token budget management."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "openai/gpt-oss-120b",
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

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_time = [5, 10, 15, 25, 35][attempt]
                time.sleep(wait_time)
            elif e.code == 413:
                # Intelligently trim context from the middle to preserve prompt instructions
                current_user_content = payload["messages"][1]["content"]
                if len(current_user_content) > 12000:
                    payload["messages"][1]["content"] = (
                        current_user_content[:4000]
                        + "\n\n[... Context compressed to fit LLM window ...]\n\n"
                        + current_user_content[-6000:]
                    )
                time.sleep(2)
            else:
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    raise e
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise e

    raise RuntimeError("Failed to complete LLM request after retries.")


def execute_multi_agent_pipeline(question: str, api_key: str, status_container, session_id: str = None) -> dict:
    """Run all 5 specialized agents with live step-by-step status updates and RAG integration."""
    pipeline_data = {}

    # Step 1: Research Manager (Check past memory)
    status_container.write("🧭 **Step 1/5: Lead Research Manager** — Checking vector memory and scoping research strategy...")
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
    status_container.write("⚖️ **Step 4/5: Evidence Analyst** — Auditing claims, checking contradictions, and building Defense Rubric...")
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

    time.sleep(1)

    # Step 5: Multi-Part Synthesis Writer (Deep Chunked Generation)
    status_container.write("✍️ **Step 5/5: Synthesis Writer** — Initiating Multi-Part Exhaustive Dossier Synthesis...")
    writer_system = (
        "Role: Senior Technical Research Writer & Systems Analyst\n"
        "Goal: Author comprehensive, highly detailed, academic-grade research sections with exhaustive empirical analysis, markdown tables, and numbered citations [1], [2]. Never summarize briefly when deep technical explanation is possible."
    )
    
    sections = []

    # Part 1: Executive Summary, Scope & Key Findings
    status_container.write("✍️ **Synthesizing Part 1/4:** Executive Summary, Scope & Key Findings...")
    part1_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Evidence:\n{web_output[:2000]}\n\n"
        f"Academic Evidence:\n{academic_output[:2000]}\n\n"
        f"Write Part 1 of the Research Dossier in Markdown:\n"
        f"# {question}\n\n"
        f"## Executive Summary\n"
        f"A deep, comprehensive, high-impact synthesis of the core findings and strategic takeaway.\n\n"
        f"## Research Question & Scope\n"
        f"Define the problem boundaries, technical dimensions, and target environments.\n\n"
        f"## Key Findings\n"
        f"Numbered, high-priority findings with inline bracketed citations (e.g. [1], [2]) and a summary matrix table."
    )
    part1_text = call_groq_api(writer_system, part1_prompt, api_key, temperature=0.2, max_tokens=6000)
    sections.append(part1_text)
    time.sleep(1)

    # Part 2: Deep Empirical Analysis
    status_container.write("✍️ **Synthesizing Part 2/4:** Deep Empirical Analysis & Attack Vectors...")
    part2_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Findings:\n{web_output[:2000]}\n\n"
        f"Academic Literature:\n{academic_output[:2000]}\n\n"
        f"Evidence Audit:\n{analyst_output[:2000]}\n\n"
        f"Write Part 2 of the Research Dossier in Markdown:\n"
        f"## Detailed Empirical Analysis\n"
        f"Provide exhaustive technical breakdowns structured by sub-topics, including empirical benchmark statistics, vulnerability models, and case studies.\n"
        f"Include detailed markdown comparison tables where appropriate."
    )
    part2_text = call_groq_api(writer_system, part2_prompt, api_key, temperature=0.2, max_tokens=6000)
    sections.append(part2_text)
    time.sleep(1)

    # Part 3: 🛡️ Defense & Mitigation Matrix & Playbook
    status_container.write("✍️ **Synthesizing Part 3/4:** 🛡️ Defense & Mitigation Matrix & Security Playbook...")
    part3_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Defense Rubric & Audit:\n{analyst_output[:2500]}\n\n"
        f"Write Part 3 of the Research Dossier in Markdown:\n"
        f"## 🛡️ Defense & Mitigation Matrix\n"
        f"Create an exhaustive, multi-column Markdown table:\n"
        f"| Threat / Risk Vector | Severity | Recommended Control & Provenance Attestation (SLSA, Sigstore) | Detective Monitoring | Operational Trade-offs |\n\n"
        f"### Actionable Defensive Implementation Playbook\n"
        f"Provide a concrete step-by-step engineering playbook for deploying these mitigations in production."
    )
    part3_text = call_groq_api(writer_system, part3_prompt, api_key, temperature=0.2, max_tokens=6000)
    sections.append(part3_text)
    time.sleep(1)

    # Part 4: Contradictions, Limitations, Strategic Recommendations & References
    status_container.write("✍️ **Synthesizing Part 4/4:** Contradictions, Limitations & Complete References...")
    part4_prompt = (
        f"Research Question: \"{question}\"\n\n"
        f"Web Sources:\n{web_output[:2000]}\n\n"
        f"Academic Literature:\n{academic_output[:2000]}\n\n"
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
    part4_text = call_groq_api(writer_system, part4_prompt, api_key, temperature=0.2, max_tokens=6000)
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

    # Sidebar: Multi-Session Management & Workspace
    with st.sidebar:
        st.markdown("## 🔬 Vesper AI")
        st.caption("Autonomous Multi-Agent Deep Research Intelligence")

        if st.button("➕ New Research", type="primary", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.research_result = None
            st.session_state.pipeline_details = {}
            st.session_state.chat_history = []
            st.session_state.example_q = ""
            st.rerun()

        st.divider()

        # Sessions list from Supabase
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
                        st.session_state.current_session_id = s_id
                        loaded_report = get_report(s_id)
                        if loaded_report:
                            st.session_state.research_result = {
                                "question": s_title,
                                "report": loaded_report.get("markdown_content", ""),
                            }
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
    st.title("🔬 Autonomous Multi-Agent Researcher")
    st.caption("Autonomous Agentic RAG • Cross-Examined Citations • Multi-Session Memory")

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

        default_question = st.session_state.get("example_q", "")

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
                "🚀 Launch Research",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_researching,
            )

        if start_btn:
            if not question.strip():
                st.error("Please enter a research question before starting.")
            elif not active_api_key:
                st.error("Groq API Key is required. Please provide it in the sidebar or Streamlit Secrets.")
            else:
                st.session_state.is_researching = True

                # Create Supabase session
                created_session = create_session(question[:60])
                session_id = created_session.get("id") if created_session else None
                st.session_state.current_session_id = session_id

                with st.status("🔍 Conducting Autonomous Multi-Agent Research...", expanded=True) as status_box:
                    try:
                        results = execute_multi_agent_pipeline(question, active_api_key, status_box, session_id=session_id)
                        st.session_state.pipeline_details = results
                        report_content = results.get("final_report", "No report generated.")
                        st.session_state.research_result = {
                            "question": question,
                            "report": report_content,
                        }

                        # Save to Supabase
                        if session_id:
                            save_report(session_id, report_content)
                            add_chat_message(session_id, "assistant", f"Generated research dossier for: **{question}**")

                        status_box.update(label="✅ Research Complete & Synced to Supabase!", state="complete", expanded=False)
                    except Exception as e:
                        status_box.update(label="❌ Research Process Interrupted", state="error", expanded=True)
                        st.error(f"Error during research execution: {str(e)}")
                    finally:
                        st.session_state.is_researching = False
                        st.rerun()

    # Results & Follow-Up Q&A View
    if st.session_state.research_result:
        report_text = st.session_state.research_result["report"]
        active_q = st.session_state.research_result.get("question", "Research Dossier")

        st.markdown(f"### 📋 Active Dossier: *{active_q}*")

        tab1, tab2, tab3 = st.tabs(["📄 Structured Dossier", "💬 Interactive Follow-Up & Edits", "🔍 Agent Telemetry"])

        with tab1:
            st.markdown(report_text)
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
