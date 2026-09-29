"""Web Research Task for the Web Researcher Agent.

Directs the Web Researcher to query the web, inspect authoritative links,
and return structured findings with full URLs, dates, and evidence quotes.
"""

from typing import Optional, List

try:
    from crewai import Task, Agent
except Exception:
    class Task:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    Agent = object


def create_web_research_task(
    agent: Agent,
    research_question: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the web research task for the Web Researcher agent."""
    description = (
        f"Execute thorough web research for the research question:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your objectives:\n"
        f"1. Review the Research Plan provided by the Research Manager (if available).\n"
        f"2. Use the 'web_search' tool with focused search queries to discover relevant web sources.\n"
        f"3. Use the 'web_reader' tool to inspect the full content of high-value URLs.\n"
        f"4. For each distinct finding, record:\n"
        f"   - Source Title\n"
        f"   - Exact URL\n"
        f"   - Publication / Access Date (if available)\n"
        f"   - Source Type (Official Docs, Vendor Whitepaper, Industry Report, Journalism)\n"
        f"   - Key Factual Claim & Empirical Evidence Extracted\n\n"
        f"Important: Do NOT hallucinate or guess URLs. Only report URLs actually returned by the tools."
    )

    expected_output = (
        "A structured collection of Web Research Findings organized by subtopics, containing:\n"
        "- List of inspected sources with Title, exact URL, and Date\n"
        "- Extracted factual evidence, technical data, and case studies\n"
        "- Distinction between primary documentation and secondary opinion"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks if context_tasks else None,
    )
