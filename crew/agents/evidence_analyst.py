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
        role="Chief Evidence Analyst & Security Strategist",
        goal=(
            "Critically audit gathered research, cross-examine claims against sources, detect contradictions, "
            "calibrate claim certainty, construct structured defense & mitigation matrices for security topics, "
            "and index verified findings in long-term memory."
        ),
        backstory=(
            "You are a meticulous epistemologist, defensive security architect, and peer reviewer. "
            "You scrutinize findings, cross-examining citations against source excerpts. "
            "When analyzing systems vulnerabilities, AI security, or threat vectors, you rigorously evaluate "
            "root causes, provenance attestation (e.g. SLSA, Sigstore cryptographic signing), runtime sandboxing, "
            "and construct comprehensive Preventative, Detective, and Responsive mitigation rubrics."
        ),
        tools=[store_verified_evidence_tool],
        llm=analyst_llm,
        verbose=True,
        allow_delegation=False,
    )
