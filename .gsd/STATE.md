# PROJECT STATE — Researcher AI

**Current Phase:** Phase 0 (Planning & Audit)
**Last Updated:** 2026-09-27

## System Status
- Specification saved in `.gsd/SPEC.md` (Status: FINALIZED)
- Roadmap created in `.gsd/ROADMAP.md`
- Target Model: `openai/gpt-oss-120b` via Groq
- Framework: CrewAI + Streamlit
- Deployment: GitHub → Streamlit Community Cloud

## Decisions & Constraints
- No local runtime required from developer. Static code checks and clean dependency definitions only.
- Strict architecture in `crew/` (no duplicate `research_crew.py` or root-level agent directories).
- Secrets handled via `st.secrets` with fallback to `os.environ`. No hardcoded API keys.
- Real tools for web and academic search with resilient error handling.
