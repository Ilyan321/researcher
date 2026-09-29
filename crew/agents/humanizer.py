"""Humanizer & Anti-AI Detection Specialist Agent.

Performs tone de-sterilization, cadence disruption, and vocabulary humanization
on raw research synthesis drafts to achieve 0% AI detection probability.
"""

from typing import Optional
from config import get_llm

try:
    from crewai import Agent
except Exception:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


def create_humanizer_agent(llm: Optional[object] = None) -> Agent:
    """Instantiate and return the Anti-AI Humanizer Agent."""
    humanizer_llm = llm or get_llm(temperature=0.65)

    return Agent(
        role="Principal Technical Editor & Anti-AI Humanization Specialist",
        goal=(
            "De-sterilize raw research drafts and transform them into publication-grade, "
            "authoritative human prose that achieves 0% AI detection score across Turnitin, "
            "GPTZero, and Originality.ai while strictly preserving all technical facts, metrics, and citations."
        ),
        backstory=(
            "You are a distinguished technical essayist, seasoned principal engineer, and master editor. "
            "You despise robotic LLM clichés, passive textbook phrasing, and formulaic paragraph rhythms. "
            "You rewrite technical dossiers with authentic burstiness—mixing punchy, sharp assertions with deep, "
            "nuanced technical clauses. You ruthlessly purge signature AI words like 'delve', 'tapestry', 'testament', "
            "and 'furthermore', replacing them with pragmatic, real-world engineering insights."
        ),
        llm=humanizer_llm,
        verbose=True,
        allow_delegation=False,
    )
