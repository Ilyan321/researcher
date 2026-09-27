"""Academic Research Task for the Academic Researcher Agent.

Directs the Academic Researcher to query scholarly databases, extract paper abstracts,
document methodologies, authors, dates, and identify research limitations.
"""

from typing import Optional, List
from crewai import Task, Agent


def create_academic_task(
    agent: Agent,
    research_question: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the academic literature review task for the Academic Researcher agent."""
    description = (
        f"Conduct a rigorous academic literature review for the research question:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your objectives:\n"
        f"1. Review the scholarly topics and keywords outlined in the Research Plan (if available).\n"
        f"2. Use the 'academic_search' tool with scholarly keywords (e.g., 'code generation LLM vulnerability', 'autonomous agent security evaluation').\n"
        f"3. For each relevant academic paper or preprint retrieved:\n"
        f"   - Paper Title\n"
        f"   - Primary Authors\n"
        f"   - Publication Year / Date\n"
        f"   - Journal / Conference / Repository (e.g. arXiv, IEEE, ACM, OpenAlex)\n"
        f"   - Direct DOI or arXiv URL\n"
        f"   - Abstract Summary & Core Empirical Findings\n"
        f"   - Stated Methodological Limitations / Scope\n\n"
        f"Important: Do NOT fabricate academic papers, fake authors, or fake DOIs. Only report actual papers retrieved."
    )

    expected_output = (
        "A structured collection of Academic Literature Findings containing:\n"
        "- Detailed catalog of scholarly papers with Title, Authors, Year, DOI/arXiv URL\n"
        "- Abstract summaries of empirical experiments and security benchmark evaluations\n"
        "- Methodological strengths, sample sizes, and acknowledged limitations"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks if context_tasks else None,
    )
