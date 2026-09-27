"""Research Manager Agent.

Responsible for analyzing user research questions, breaking them into investigative
subtopics, establishing required evidence criteria, and formulating the research strategy.
"""

from typing import Optional
from crewai import Agent
from config import get_llm


def create_manager(llm: Optional[object] = None) -> Agent:
    """Instantiate and return the Research Manager Agent."""
    manager_llm = llm or get_llm(temperature=0.2)

    return Agent(
        role="Lead Research Manager & Strategist",
        goal=(
            "Deconstruct the research question into structured subtopics, identify necessary "
            "empirical evidence, and devise an optimal multi-agent research strategy."
        ),
        backstory=(
            "You are a distinguished research director with extensive experience structuring "
            "scientific, technical, and academic inquiries. You excel at scoping investigations, "
            "establishing clear sub-questions, and guiding specialized research teams without "
            "duplicating search efforts or performing search tasks yourself."
        ),
        llm=manager_llm,
        verbose=True,
        allow_delegation=False,
    )
