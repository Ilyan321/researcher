"""Evidence Analyst Agent.

Audits and fact-checks research findings gathered by the Web and Academic Researchers.
Detects unsupported claims, identifies contradictions, filters weak sources,
and calibrates the confidence level of all factual assertions.
"""

from typing import Optional
from config import get_llm

from crew.tools.memory_tools import store_verified_evidence_tool

try:
    from crewai import Agent
except ImportError:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


def create_evidence_analyst(llm: Optional[object] = None) -> Agent:
    """Instantiate and return the Evidence Analyst Agent."""
    analyst_llm = llm or get_llm(temperature=0.1)

    return Agent(
        role="Chief Evidence Analyst & Fact-Checker",
        goal=(
            "Critically audit gathered web and academic research, cross-examine claims against "
            "sources, detect contradictions and weak evidence, calibrate claim certainty, and index verified findings in long-term memory."
        ),
        backstory=(
            "You are a meticulous epistemologist, scientific peer reviewer, and rigorous fact-checker. "
            "You scrutinize every finding made by researchers, cross-examining citations against source excerpts. "
            "You flag over-generalized conclusions, detect conflicting findings, distinguish documented empirical "
            "data from vendor marketing, and index high-confidence findings into long-term cloud memory."
        ),
        tools=[store_verified_evidence_tool],
        llm=analyst_llm,
        verbose=True,
        allow_delegation=False,
    )
