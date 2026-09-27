# Researcher AI — Project Plan & Phase Breakdown

## Project Overview
Researcher AI is an autonomous multi-agent research team powered by CrewAI, Groq (`openai/gpt-oss-120b`), and Streamlit, designed for cloud deployment on Streamlit Community Cloud.

---

## Phase Matrix

| Phase | Title | Scope & Objectives | Status | GitHub Issue |
|---|---|---|---|---|
| **Phase 0** | Audit & Workspace Architecture | Audit repository, ensure clean `crew/` folder structure, verify Git configuration | **Completed** | #1 |
| **Phase 1** | Dependency & Config Foundation | Setup `requirements.txt`, `config.py` (dual-source secrets for Streamlit Cloud & local env), `.gitignore` | **Completed** | #2 |
| **Phase 2** | LLM Configuration & Smoke Testing | Configure `groq/openai/gpt-oss-120b`, create single-agent smoke test harness | **Completed** | #3 |
| **Phase 3** | Streamlit Frontend Skeleton | Build initial `app.py` with session state, dynamic sidebar API key config, input validation, and reset | **Completed** | #4 |
| **Phase 4** | Agent 1: Research Manager & Planning Task | Implement `crew/agents/manager.py`, `crew/tasks/planning_task.py`, and YAML configs | **Completed** | #5 |
| **Phase 5** | Agent 2: Web Researcher & Tools | Implement `crew/tools/web_search.py`, `crew/tools/web_reader.py`, `crew/agents/web_researcher.py`, `crew/tasks/web_research_task.py` | Pending | #6 |
| **Phase 6** | Agent 3: Academic Researcher & Tools | Implement `crew/tools/academic_search.py` (arXiv/OpenAlex/Crossref), `crew/agents/academic_researcher.py`, `crew/tasks/academic_task.py` | Pending | #7 |
| **Phase 7** | Agent 4: Evidence Analyst & Task | Implement `crew/agents/evidence_analyst.py`, `crew/tasks/evidence_task.py` for fact-checking & contradiction detection | Pending | #8 |
| **Phase 8** | Agent 5: Research Writer & Task | Implement `crew/agents/research_writer.py`, `crew/tasks/writing_task.py` for structured Markdown reports | Pending | #9 |
| **Phase 9** | Full Crew Pipeline Orchestration | Implement `crew/crew.py` assembling all 5 agents and inter-task dependencies into a single cohesive pipeline | Pending | #10 |
| **Phase 10** | Streamlit UI Integration & Live Tracking | Connect Streamlit UI in `app.py` to live Crew execution with progress indicators and source viewer | Pending | #11 |
| **Phase 11** | Deployment Readiness & Final Documentation | Build comprehensive `README.md`, verify zero local runtime assumptions, prepare for Streamlit Community Cloud launch | Pending | #12 |

---

## Agent Responsibilities
1. **Research Manager** (`crew/agents/manager.py`): Scopes research question, extracts subquestions, creates multi-agent research roadmap.
2. **Web Researcher** (`crew/agents/web_researcher.py`): Searches live web, scrapes key pages, records title, URL, publication dates.
3. **Academic Researcher** (`crew/agents/academic_researcher.py`): Queries free academic databases (arXiv, OpenAlex, Crossref), extracts abstracts and citations.
4. **Evidence Analyst** (`crew/agents/evidence_analyst.py`): Cross-verifies claims, identifies weak or conflicting evidence, checks citations.
5. **Research Writer** (`crew/agents/research_writer.py`): Compiles structured final report with executive summary, key findings, and references.
