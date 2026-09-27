# 🔬 Researcher AI

### Autonomous Multi-Agent Research Platform

**Researcher AI** is a production-ready, research-focused multi-agent system powered by **CrewAI**, **Groq** (`openai/gpt-oss-120b`), and **Streamlit**. It accepts any complex research question, coordinates five specialized AI agents, searches both the live web and academic databases (arXiv & OpenAlex), performs rigorous evidence fact-checking, and generates a structured, publication-grade research report with complete citations.

---

## 🏗️ Architecture & Workflow

```text
                        ┌───────────────────────────────┐
                        │    User Research Question     │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   🧭 Agent 1: Research Manager │
                        │  (Deconstruction & Strategy)  │
                        └───────┬───────────────┬───────┘
                                │               │
                ┌───────────────┘               └───────────────┐
                ▼                                               ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│  🌐 Agent 2: Web Researcher   │               │ 📚 Agent 3: Academic Researcher│
│   (Live Search & Web Reader)  │               │   (arXiv & OpenAlex Queries)  │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │                                               │
                └───────────────┐               ┌───────────────┘
                                ▼               ▼
                        ┌───────────────────────────────┐
                        │  ⚖️ Agent 4: Evidence Analyst  │
                        │  (Fact-Checking & Audit Matrix)│
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │  ✍️ Agent 5: Research Writer   │
                        │ (Master Cited Markdown Report)│
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │    Live Streamlit Frontend    │
                        │  (Report, Telemetry & Export) │
                        └───────────────────────────────┘
```

---

## 👥 The Multi-Agent Research Team

| Agent | Role | Key Responsibilities | Primary Tools |
|---|---|---|---|
| **1. Research Manager** | Lead Research Manager & Strategist | Analyzes the core problem, breaks it into investigative sub-questions, and creates targeted directives for web and academic researchers. | Strategic Planning Prompt |
| **2. Web Researcher** | Senior Web Research Specialist | Queries the live web for industry reports, official documentation, and technical articles; reads full URLs and extracts evidence. | `web_search_tool`, `web_reader_tool` |
| **3. Academic Researcher** | Principal Academic Literature Specialist | Queries scholarly databases (arXiv, OpenAlex) for peer-reviewed papers, extracts abstracts, methodologies, and limitations. | `academic_search_tool` (arXiv / OpenAlex) |
| **4. Evidence Analyst** | Chief Evidence Analyst & Fact-Checker | Audits all findings, detects contradictions between marketing and peer-reviewed benchmarks, and calibrates certainty tiers. | Evidence Audit Matrix |
| **5. Research Writer** | Senior Technical Research Writer | Synthesizes verified evidence into a cohesive, publication-grade Markdown report with inline numbered citations (`[1]`, `[2]`). | Report Compilation Engine |

---

## 🧰 Modular Research Tools

- **`web_search_tool`** (`crew/tools/web_search.py`): Live keyword search with structured JSON output (title, URL, snippet).
- **`web_reader_tool`** (`crew/tools/web_reader.py`): HTML scraper and cleaner that strips scripts/CSS and extracts readable text with safe character capping.
- **`academic_search_tool`** (`crew/tools/academic_search.py`): Free, open-access scholarly search across **arXiv API** (Atom/XML) and **OpenAlex API** with zero paid key requirements.

---

## 🚀 Cloud Deployment (Streamlit Community Cloud)

Researcher AI is designed to run directly on **Streamlit Community Cloud** with zero local setup requirements.

### Step-by-Step Deployment:

1. **Fork or Push** this repository to your GitHub account:
   ```text
   https://github.com/Ilyan321/researcher
   ```

2. **Open Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
   - Click **"Create app"**.

3. **Configure App Settings**:
   - **Repository:** `your-username/researcher`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **Python version:** `3.12` (Default)

4. **Add Secrets (Advanced Settings)**:
   - Click **Advanced Settings** $\rightarrow$ **Secrets**.
   - Enter your Groq API key:
     ```toml
     GROQ_API_KEY = "gsk_your_groq_api_key_here"
     ```
   - Click **Save**.

5. **Deploy**:
   - Click **"Deploy!"**. Streamlit will automatically install dependencies from `requirements.txt` and launch your live application.

---

## 🔒 Security & Best Practices

- **Zero Hardcoded Secrets**: `GROQ_API_KEY` is loaded dynamically from `st.secrets` in the cloud or `os.environ` in local CI/CD.
- **Git Protection**: `.gitignore` strictly blocks `.env`, `.streamlit/secrets.toml`, and cache directories.
- **Anti-Hallucination Discipline**: Agents are strictly instructed to report only verified URLs and scholarly DOIs returned by real search tools.

---

## 🧪 Testing & Verification

Comprehensive test harnesses are included in the `scripts/` directory:

```bash
# 1. Test LLM connectivity and agent setup
python3 scripts/test_llm_smoke.py

# 2. Test live Research Manager planning
GROQ_API_KEY="gsk_..." python3 scripts/live_manager_test.py

# 3. Test Web Search and URL Reader tools
python3 scripts/test_web_researcher.py

# 4. Test Academic Search (arXiv / OpenAlex)
python3 scripts/test_academic_search.py

# 5. Test Full 5-Agent End-to-End Pipeline
GROQ_API_KEY="gsk_..." python3 scripts/live_full_crew_test.py
```

---

## 📁 Repository Structure

```text
researcher/
│
├── app.py                     # Streamlit Frontend & Live Status Dashboard
├── config.py                  # Centralized LLM & Secret Configuration
├── requirements.txt           # Minimal, Cloud-Compatible Dependencies
├── PLAN.md                    # Master Phase Matrix & Implementation Plan
├── README.md                  # Comprehensive Documentation & Architecture Guide
├── .gitignore                 # Secrets and Cache Exclusions
│
├── config/
│   ├── agents.yaml            # Declarative Agent Roles, Goals & Backstories
│   └── tasks.yaml             # Declarative Task Descriptions & Expected Outputs
│
├── crew/
│   ├── __init__.py            # Package Exporter
│   ├── crew.py                # ResearcherCrew Master Pipeline Orchestrator
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── manager.py         # Agent 1: Research Manager
│   │   ├── web_researcher.py  # Agent 2: Web Researcher
│   │   ├── academic_researcher.py # Agent 3: Academic Researcher
│   │   ├── evidence_analyst.py # Agent 4: Evidence Analyst
│   │   └── research_writer.py # Agent 5: Research Writer
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── planning_task.py   # Planning Task
│   │   ├── web_research_task.py # Web Research Task
│   │   ├── academic_task.py   # Academic Literature Review Task
│   │   ├── evidence_task.py   # Evidence Audit Matrix Task
│   │   └── writing_task.py    # Master Report Writing Task
│   │
│   └── tools/
│       ├── __init__.py
│       ├── web_search.py      # DuckDuckGo / OpenSearch Tool
│       ├── web_reader.py      # Resilient HTML Parser & Cleaner
│       └── academic_search.py # arXiv & OpenAlex Free API Search
│
└── scripts/
    ├── test_llm_smoke.py      # LLM Smoke Test
    ├── test_web_researcher.py # Web Tools Verification
    ├── test_academic_search.py# Scholarly Search Verification
    ├── test_streamlit_flow.py # Streamlit Pipeline Test
    ├── live_manager_test.py   # Live Manager User Test
    ├── live_web_researcher_test.py # Live Web Researcher User Test
    ├── live_academic_researcher_test.py # Live Academic Researcher User Test
    ├── live_evidence_analyst_test.py # Live Evidence Analyst User Test
    ├── live_writer_test.py    # Live Research Writer User Test
    └── live_full_crew_test.py # Live 5-Agent End-to-End User Test
```

---

## 📜 License
MIT License. Built for rigorous, autonomous academic and technical research.
