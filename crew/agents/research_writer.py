"""Research Writer Agent.

Transforms multi-agent research outputs (planning, web findings, academic papers,
and evidence audit matrices) into an authoritative, structured, and cited research report.
"""

from typing import Optional
from crewai import Agent
from config import get_llm


def create_research_writer(llm: Optional[object] = None) -> Agent:
    """Instantiate and return the Research Writer Agent."""
    writer_llm = llm or get_llm(temperature=0.2)

    return Agent(
        role="Senior Technical Research Writer",
        goal=(
            "Synthesize all planning, web discoveries, academic literature, and audited evidence "
            "into a comprehensive, balanced, and rigorously cited research report in Markdown."
        ),
        backstory=(
            "You are a master scientific communicator and technical author with extensive experience "
            "drafting high-impact research publications. You transform complex multi-source research "
            "into clear, beautifully formatted reports featuring executive summaries, detailed analyses, "
            "limitations, and numbered citations ([1], [2]). You strictly adhere to the Evidence Analyst's "
            "confidence calibrations, avoid sweeping generalizations, and never invent fake citations."
        ),
        llm=writer_llm,
        verbose=True,
        allow_delegation=False,
    )
