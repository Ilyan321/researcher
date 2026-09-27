"""Web Researcher Agent.

Searches the live web for recent developments, technical documentation,
industry reports, and real-world evidence, recording full source URLs and metadata.
"""

from typing import Optional, List
from crewai import Agent
from config import get_llm
from crew.tools.web_search import web_search_tool
from crew.tools.web_reader import web_reader_tool


def create_web_researcher(llm: Optional[object] = None, tools: Optional[List] = None) -> Agent:
    """Instantiate and return the Web Researcher Agent equipped with search and read tools."""
    researcher_llm = llm or get_llm(temperature=0.2)
    researcher_tools = tools or [web_search_tool, web_reader_tool]

    return Agent(
        role="Senior Web Research Specialist",
        goal=(
            "Discover, retrieve, and synthesize timely, credible web evidence and documentation "
            "with complete source attribution (titles, exact URLs, publication dates)."
        ),
        backstory=(
            "You are an expert digital research specialist who navigates online literature, "
            "technical documentation, and industry publications. You use your search and reader "
            "tools to inspect actual page contents, recording exact titles and URLs, and prioritizing "
            "primary sources over secondary summaries. You never invent fake links or URLs."
        ),
        tools=researcher_tools,
        llm=researcher_llm,
        verbose=True,
        allow_delegation=False,
    )
