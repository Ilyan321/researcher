"""Academic Researcher Agent.

Queries scholarly databases (arXiv, OpenAlex, Crossref) for peer-reviewed papers,
technical publications, and scientific preprints, extracting abstracts, methodologies,
and stated research limitations.
"""

from typing import Optional, List
from config import get_llm
from crew.tools.academic_search import academic_search_tool

try:
    from crewai import Agent
except ImportError:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


def create_academic_researcher(llm: Optional[object] = None, tools: Optional[List] = None) -> Agent:
    """Instantiate and return the Academic Researcher Agent equipped with scholarly search tools."""
    academic_llm = llm or get_llm(temperature=0.2)
    academic_tools = tools or [academic_search_tool]

    return Agent(
        role="Principal Academic Literature Specialist",
        goal=(
            "Query academic repositories (arXiv, OpenAlex, Crossref) to discover scientific "
            "publications, extracting key findings, authors, publication years, abstracts, and DOIs."
        ),
        backstory=(
            "You are a seasoned academic researcher with extensive experience surveying scholarly "
            "literature across computer science, software engineering, and artificial intelligence. "
            "You extract abstracts, record complete author citations and DOIs/arXiv links, and clearly "
            "distinguish peer-reviewed empirical evidence from general web claims. You never fabricate citations."
        ),
        tools=academic_tools,
        llm=academic_llm,
        verbose=True,
        allow_delegation=False,
    )
