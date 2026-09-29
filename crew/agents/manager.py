"""Research Manager Agent.

Responsible for analyzing user research questions, breaking them into investigative
subtopics, establishing required evidence criteria, and formulating the research strategy.
"""

from typing import Optional
from config import get_llm

from crew.tools.memory_tools import recall_past_research_tool

try:
    from crewai import Agent
except Exception:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


def create_manager(llm: Optional[object] = None) -> Agent:
    """Instantiate and return the Research Manager Agent."""
    manager_llm = llm or get_llm(temperature=0.2)

    return Agent(
        role="Lead Research Manager & Strategist",
        goal=(
            "Deconstruct the research question into structured subtopics, identify necessary "
            "empirical evidence, consult long-term memory for prior findings, and devise an optimal research strategy."
        ),
        backstory=(
            "You are a distinguished research director with extensive experience structuring "
            "scientific, technical, and academic inquiries. You excel at scoping investigations, "
            "recalling prior verified evidence from long-term memory to prevent redundant work, "
            "and guiding specialized research teams with precision."
        ),
        tools=[recall_past_research_tool],
        llm=manager_llm,
        verbose=True,
        allow_delegation=False,
    )
