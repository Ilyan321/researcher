# RESEARCHER AI — Specification

**Status: FINALIZED**

## Multi-Agent Research Team
### Master Build Specification for AGY

The application is a research-focused multi-agent system built with:
* CrewAI
* Groq
* `openai/gpt-oss-120b`
* Streamlit
* GitHub
* Streamlit Community Cloud

The developer does NOT want to run the application locally.

The intended workflow is:
```text
ChatGPT / Developer
   ↓
GitHub
   ↓
Streamlit Community Cloud
   ↓
Live Streamlit Application
```

Ubuntu is being used only for Git/file management and terminal commands, not as the application's runtime environment.

---

# 1. PRIMARY OBJECTIVE

Build a modular AI research team that accepts a research question from a Streamlit frontend and performs structured research using multiple specialized agents.

The system should:
1. Accept a research question.
2. Create a research plan.
3. Conduct web research.
4. Conduct academic research.
5. Analyze and verify evidence.
6. Identify weak or unsupported claims.
7. Synthesize the findings.
8. Produce a structured research report.
9. Include source information/citations wherever possible.
10. Show the research process clearly in the Streamlit UI.

This must be a genuine multi-agent system:
- Agents must have distinct responsibilities.
- Agents must use tools where appropriate.
- Do not simply call the same LLM five times without role separation.

---

# 2. IMPORTANT DEVELOPMENT RULE

Before writing or changing code involving:
* CrewAI
* CrewAI tools
* Groq
* GPT-OSS
* Streamlit
* Streamlit deployment
* tool calling
* LLM configuration

CHECK THE CURRENT OFFICIAL DOCUMENTATION FIRST.
Do NOT rely on old tutorials or remembered APIs.
Official documentation should be preferred over blogs, random GitHub repositories, or old Stack Overflow answers.

---

# 3. CURRENT VERIFIED MODEL

The primary model is:
`openai/gpt-oss-120b` through Groq.

Groq currently documents GPT-OSS 120B as supporting:
* Tool use
* Browser search
* Code execution
* JSON object mode
* JSON schema mode
* Reasoning
* 131,072-token context window

The implementation must use the CURRENT supported CrewAI/Groq integration.

---

# 4. PROJECT ARCHITECTURE

The project must use this structure:
```text
researcher/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
│
└── crew/
    ├── __init__.py
    ├── crew.py
    │
    ├── agents/
    │   ├── __init__.py
    │   ├── manager.py
    │   ├── web_researcher.py
    │   ├── academic_researcher.py
    │   ├── evidence_analyst.py
    │   └── research_writer.py
    │
    ├── tasks/
    │   ├── __init__.py
    │   ├── planning_task.py
    │   ├── web_research_task.py
    │   ├── academic_task.py
    │   ├── evidence_task.py
    │   └── writing_task.py
    │
    └── tools/
        ├── __init__.py
        ├── web_search.py
        ├── web_reader.py
        └── academic_search.py
```

Only the `crew/` architecture should be used. No duplicate structures.

---

# 5. AGENT TEAM

Use FIVE primary agents:
1. **Research Manager** (`crew/agents/manager.py`): Understands question, breaks into research areas, plans strategy, coordinates workflow.
2. **Web Researcher** (`crew/agents/web_researcher.py`): Searches web, finds recent/relevant sources, reads pages, records metadata/URLs/dates.
3. **Academic Researcher** (`crew/agents/academic_researcher.py`): Searches arXiv/Crossref/Semantic Scholar/OpenAlex, extracts abstracts, distinguishes academic evidence.
4. **Evidence Analyst** (`crew/agents/evidence_analyst.py`): Analyzes findings, verifies claims vs sources, flags contradictions/weak sources/uncertainty.
5. **Research Writer** (`crew/agents/research_writer.py`): Organizes verified research, writes structured final report with references & citations.

---

# 6. TOOLS

Modular tools:
1. `crew/tools/web_search.py`: Structured web search with fallback/error handling.
2. `crew/tools/web_reader.py`: Retrieve and clean page content safely.
3. `crew/tools/academic_search.py`: Free academic API search (e.g. arXiv / OpenAlex / Crossref) without required paid keys.

---

# 7. TASK FLOW & CREW ORCHESTRATION

```text
User question
      ↓
Research Manager (planning_task.py)
      ↓
Research Plan
      ↓
 ┌───────────────┐
 │               │
 ▼               ▼
Web Research   Academic Research
(web_task.py)  (academic_task.py)
 │               │
 └───────┬───────┘
         ▼
  Evidence Analyst (evidence_task.py)
         ↓
  Research Writer (writing_task.py)
         ↓
   Final Report
```

---

# 8. CONFIGURATION & SECRETS

- Centralized in `config.py`.
- Never commit `GROQ_API_KEY`.
- Use `st.secrets` in Streamlit and `os.environ` fallback.
- Support `config/agents.yaml` and `config/tasks.yaml`.

---

# 9. FRONTEND & DEPLOYMENT

- Streamlit UI in `app.py`.
- Simple, reliable, shows progress of agents and outputs final structured report with citations.
- Deployment target: GitHub → Streamlit Community Cloud (Python 3.12 default).
- Minimal and clean `requirements.txt`.
