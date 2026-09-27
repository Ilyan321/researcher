#!/usr/bin/env bash
set -e

REPO="Ilyan321/researcher"

echo "Creating GitHub issues for Researcher AI phases..."

gh issue create --repo "$REPO" --title "Phase 1: Dependency & Configuration Foundation" --body "Setup requirements.txt, config.py (dual-source secrets for Streamlit Cloud & local env), and .gitignore."
gh issue create --repo "$REPO" --title "Phase 2: LLM Configuration & Smoke Testing" --body "Configure openai/gpt-oss-120b via Groq, create single-agent smoke test harness."
gh issue create --repo "$REPO" --title "Phase 3: Streamlit Frontend Skeleton" --body "Build initial app.py with session state, dynamic sidebar API key config, input validation, and reset."
gh issue create --repo "$REPO" --title "Phase 4: Agent 1 - Research Manager & Planning Task" --body "Implement crew/agents/manager.py, crew/tasks/planning_task.py, and YAML configs."
gh issue create --repo "$REPO" --title "Phase 5: Agent 2 - Web Researcher & Web Tools" --body "Implement crew/tools/web_search.py, crew/tools/web_reader.py, crew/agents/web_researcher.py, and crew/tasks/web_research_task.py."
gh issue create --repo "$REPO" --title "Phase 6: Agent 3 - Academic Researcher & Scholarly Tools" --body "Implement crew/tools/academic_search.py (arXiv/OpenAlex/Crossref), crew/agents/academic_researcher.py, and crew/tasks/academic_task.py."
gh issue create --repo "$REPO" --title "Phase 7: Agent 4 - Evidence Analyst & Verification Task" --body "Implement crew/agents/evidence_analyst.py and crew/tasks/evidence_task.py for fact-checking & contradiction detection."
gh issue create --repo "$REPO" --title "Phase 8: Agent 5 - Research Writer & Report Task" --body "Implement crew/agents/research_writer.py and crew/tasks/writing_task.py for structured Markdown report compilation."
gh issue create --repo "$REPO" --title "Phase 9: Full Crew Pipeline Orchestration" --body "Implement crew/crew.py assembling all 5 agents and inter-task dependencies into a single cohesive pipeline."
gh issue create --repo "$REPO" --title "Phase 10: Streamlit UI Integration & Live Progress Tracking" --body "Connect Streamlit UI in app.py to live Crew execution with progress indicators and source viewer."
gh issue create --repo "$REPO" --title "Phase 11: Deployment Readiness & Final Documentation" --body "Build comprehensive README.md, verify zero local runtime assumptions, prepare for Streamlit Community Cloud launch."

echo "All GitHub issues created successfully!"
