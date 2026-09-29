"""Humanization & Anti-AI Detection Task.

Directs the Anti-AI Humanization Specialist agent to de-sterilize the draft research report,
inject authentic human burstiness, and purge robotic AI clichés to achieve 0% AI detection.
"""

from typing import Optional, List

try:
    from crewai import Task, Agent
except ImportError:
    class Task:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    Agent = object


def create_humanization_task(
    agent: Agent,
    research_question: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the Anti-AI Humanization task that polishes the research report draft."""
    description = (
        f"Take the raw research draft produced by the Research Writer for:\n\n"
        f"\"{research_question}\"\n\n"
        f"Transform and polish the entire dossier to achieve ABSOLUTE 0% AI DETECTION across Turnitin, "
        f"GPTZero, and Originality.ai while preserving all technical facts, metrics, markdown tables, and citations.\n\n"
        f"Core Directives:\n"
        f"1. **Burstiness & Dynamic Cadence:** Radically vary sentence lengths. Mix 3–7 word staccato sentences "
        f"with 35–45 word intricate technical clauses. Eliminate formulaic tripartite bullet lists.\n"
        f"2. **Strict Cliché Purge:** Ban and replace signature AI words ('delve', 'tapestry', 'testament', "
        f"'beacon', 'pivotal', 'crucial', 'multifaceted', 'furthermore', 'moreover', 'in conclusion', 'seamless').\n"
        f"3. **Pragmatic Voice:** Write with the authoritative, first-principles tone of a seasoned principal engineer.\n"
        f"4. **Exact Preservation:** Retain every citation marker ([1], [2]), header structure, CVE, benchmark metric, "
        f"and the Defense & Mitigation Matrix table exactly.\n"
    )

    expected_output = (
        "A publication-ready, deeply humanized research dossier in Markdown that passes all AI detection "
        "filters at 0% AI probability, featuring erratic cadence, rich technical depth, and clean numbered citations."
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks if context_tasks else None,
    )
