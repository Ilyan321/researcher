"""Writing Task for the Research Writer Agent.

Directs the Research Writer to synthesize all prior agent outputs into a publication-grade,
structured, and numbered-citation research report in GitHub-flavored Markdown.
"""

from typing import Optional, List
from crewai import Task, Agent


def create_writing_task(
    agent: Agent,
    research_question: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the report generation task for the Research Writer agent."""
    description = (
        f"Synthesize the full research portfolio into a master, publication-grade Research Report for:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your inputs include:\n"
        f"- The strategic breakdown from the Research Manager\n"
        f"- Live findings & URLs from the Web Researcher\n"
        f"- Peer-reviewed literature & abstracts from the Academic Researcher\n"
        f"- The Evidence Audit Matrix & calibration directives from the Evidence Analyst\n\n"
        f"Format the final report using the following clean Markdown structure:\n"
        f"# [Comprehensive Report Title]\n\n"
        f"## Executive Summary\n"
        f"A concise, high-impact synthesis of the core findings and strategic takeaway.\n\n"
        f"## Research Question & Scope\n"
        f"Define the problem boundaries and investigative dimensions.\n\n"
        f"## Key Findings\n"
        f"Numbered, high-priority findings with inline bracketed citations (e.g. [1], [2]).\n\n"
        f"## Detailed Empirical Analysis\n"
        f"Deep technical examination structured by sub-topics, incorporating data, metrics, and case studies.\n\n"
        f"## Contradictions & Divergent Perspectives\n"
        f"Balanced breakdown of conflicting vendor vs academic data as audited by the Evidence Analyst.\n\n"
        f"## Methodological Limitations\n"
        f"Acknowledged limitations of current benchmarks, sample sizes, and open research questions.\n\n"
        f"## Strategic Recommendations & Conclusion\n"
        f"Actionable guidance for practitioners and final synthesis.\n\n"
        f"## References\n"
        f"Numbered bibliographic list ([1], [2], etc.) citing Title, Authors/Organization, Year/Date, and exact URL/DOI.\n\n"
        f"Important Writing Rules:\n"
        f"- Maintain objective, third-person scholarly tone (never say 'As an AI' or 'I think').\n"
        f"- Every key factual claim MUST have an inline citation marker corresponding to the References section.\n"
        f"- Only cite sources that were actually provided by the upstream research agents."
    )

    expected_output = (
        "A complete, authoritative, and professionally structured Research Report in Markdown "
        "featuring all required sections, inline numbered citations ([1], [2]), and a full References list."
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks if context_tasks else None,
    )
