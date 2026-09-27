"""Researcher AI — Streamlit Frontend Application.

A research-focused multi-agent system powered by CrewAI and Groq.
"""

import os
import streamlit as st
from config import get_groq_api_key, DEFAULT_MODEL

# Set page configuration
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
if "research_history" not in st.session_state:
    st.session_state.research_history = []


def main():
    # Sidebar - Settings & API Key Status
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown(f"**Model:** `{DEFAULT_MODEL}`")
        
        api_key = get_groq_api_key()
        user_key = st.text_input(
            "Groq API Key (optional if set in secrets):",
            type="password",
            value=api_key if api_key else "",
            help="Your key is used in-memory for requests and never saved or logged.",
        )
        
        if user_key:
            os.environ["GROQ_API_KEY"] = user_key
            st.success("API Key detected / configured.")
        else:
            st.warning("Please provide a GROQ_API_KEY or configure it in Streamlit Secrets.")

        st.divider()
        st.markdown("### 👥 Agent Team")
        st.markdown("- 🧭 **Research Manager** (Planning)")
        st.markdown("- 🌐 **Web Researcher** (Live Web)")
        st.markdown("- 📚 **Academic Researcher** (arXiv/OpenAlex)")
        st.markdown("- ⚖️ **Evidence Analyst** (Verification)")
        st.markdown("- ✍️ **Research Writer** (Synthesis)")

    # Main Header
    st.title("🔬 Researcher AI")
    st.caption("Your Autonomous Multi-Agent Research Team")

    # Research Input Section
    question = st.text_area(
        "Enter your research question:",
        placeholder="e.g., What are the security risks of autonomous AI coding agents?",
        height=120,
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
            if st.button("🔄 Reset", use_container_width=False):
                st.session_state.research_result = None
                st.rerun()

    # Research Execution Handler (Skeleton / Phase 3 Smoke Test)
    if start_btn:
        if not question.strip():
            st.error("Please enter a research question before starting.")
        elif not os.environ.get("GROQ_API_KEY") and not get_groq_api_key():
            st.error("Groq API Key is required. Please set it in the sidebar or Streamlit Secrets.")
        else:
            st.session_state.is_researching = True
            
            with st.status("🔍 Conducting Research with Multi-Agent Team...", expanded=True) as status:
                st.write("🧭 Research Manager: Analyzing question and building strategy...")
                st.write("🌐 Web Researcher: Gathering recent web publications...")
                st.write("📚 Academic Researcher: Querying academic databases...")
                st.write("⚖️ Evidence Analyst: Verifying claims against sources...")
                st.write("✍️ Research Writer: Synthesizing final structured report...")
                status.update(label="✅ Research Complete!", state="complete", expanded=False)

            # Placeholder result for Phase 3 smoke test
            st.session_state.research_result = {
                "question": question,
                "summary": f"Research completed for: {question}",
                "report": f"### Research Report: {question}\n\n*Phase 3 UI skeleton verified. Full multi-agent pipeline connects in Phase 9.*",
            }
            st.session_state.is_researching = False
            st.rerun()

    # Display Report Section
    if st.session_state.research_result:
        st.divider()
        st.subheader("📋 Research Report")
        st.markdown(st.session_state.research_result["report"])


if __name__ == "__main__":
    main()
