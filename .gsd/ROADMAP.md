# PROJECT ROADMAP — Researcher AI

## Phase Overview

- [x] **Phase 0: Audit & Cleanup** — Audit existing files, git state, and verify folder architecture alignment.
- [x] **Phase 1: Dependency & Configuration Foundation** — Set up `requirements.txt`, `config.py`, `.gitignore` with verified packages (CrewAI, Streamlit, Groq LLM setup) and secrets handling.
- [x] **Phase 2: LLM Configuration & Smoke Testing** — Configure `openai/gpt-oss-120b` via Groq using current CrewAI LLM standards.
- [x] **Phase 3: Streamlit Frontend Skeleton** — Build initial `app.py` structure supporting API key detection and research input.
- [x] **Phase 4: Agent 1 - Research Manager & Planning Task** — Implement `crew/agents/manager.py`, `crew/tasks/planning_task.py`, and YAML configs.
- [x] **Phase 5: Agent 2 - Web Researcher & Tools** — Implement `crew/tools/web_search.py`, `crew/tools/web_reader.py`, `crew/agents/web_researcher.py`, and `crew/tasks/web_research_task.py`.
- [x] **Phase 6: Agent 3 - Academic Researcher & Tools** — Implement `crew/tools/academic_search.py` (arXiv/OpenAlex/Crossref), `crew/agents/academic_researcher.py`, and `crew/tasks/academic_task.py`.
- [x] **Phase 7: Agent 4 - Evidence Analyst & Task** — Implement `crew/agents/evidence_analyst.py` and `crew/tasks/evidence_task.py` for fact-checking and contradiction detection.
- [x] **Phase 8: Agent 5 - Research Writer & Task** — Implement `crew/agents/research_writer.py` and `crew/tasks/writing_task.py` for structured report compilation.
- [x] **Phase 9: Crew Orchestration & Pipeline Assembly** — Implement `crew/crew.py` assembling all 5 agents and tasks into a cohesive multi-agent flow.
- [ ] **Phase 10: Streamlit UI Integration & Live Progress Tracking** — Wire Streamlit UI with the Crew pipeline, progress feedback, structured report renderer, and source viewer.
- [ ] **Phase 11: Deployment Readiness & Final Documentation** — Build comprehensive `README.md`, verify zero local runtime assumptions, validate syntax/imports, ensure GitHub & Streamlit Cloud deployment readiness.
