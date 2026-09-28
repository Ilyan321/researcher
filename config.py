"""Central configuration and LLM initialization for Researcher AI."""

import os
from typing import Optional

# Default model configuration for Groq
DEFAULT_MODEL = "groq/openai/gpt-oss-120b"
DEFAULT_TEMPERATURE = 0.2

# Tool and HTTP configurations
REQUEST_TIMEOUT = 15  # seconds
USER_AGENT = "ResearcherAI/1.0 (Educational AI Research Assistant; mailto:contact@example.com)"

# Supabase configuration
DEFAULT_SUPABASE_URL = "https://nsedecdyjuzukaatobig.supabase.co"
DEFAULT_SUPABASE_KEY = "sb_publishable_df_nmctIrA7xEA5nLwbfAw_oVn_67f8"


def get_supabase_credentials() -> tuple[Optional[str], Optional[str]]:
    """Retrieve Supabase URL and Key from environment or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    key = os.getenv("SUPABASE_KEY", DEFAULT_SUPABASE_KEY)

    try:
        import streamlit as st
        if "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
        if "SUPABASE_KEY" in st.secrets:
            key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

    return url, key


def get_groq_api_key() -> Optional[str]:
    """Retrieve Groq API key from environment variable or Streamlit secrets."""
    # 1. Check direct environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return api_key

    # 2. Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
            # Set into os.environ so downstream LiteLLM/CrewAI calls find it
            os.environ["GROQ_API_KEY"] = api_key
            return api_key
    except Exception:
        pass

    return None


def get_llm(model: Optional[str] = None, temperature: float = DEFAULT_TEMPERATURE):
    """Factory function returning a configured CrewAI LLM instance.

    Uses the verified model: groq/openai/gpt-oss-120b
    """
    from crewai import LLM

    # Ensure API key is loaded into environment
    api_key = get_groq_api_key()
    selected_model = model or DEFAULT_MODEL

    return LLM(
        model=selected_model,
        temperature=temperature,
        api_key=api_key if api_key else None,
    )
