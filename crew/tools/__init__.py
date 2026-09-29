"""Tools package for Researcher AI."""

from crew.tools.web_search import web_search_tool, perform_web_search
from crew.tools.web_reader import web_reader_tool, read_url_content
from crew.tools.academic_search import academic_search_tool, perform_academic_search
from crew.tools.memory_tools import recall_past_research_tool, store_verified_evidence_tool

from crew.tools.humanizer_tool import (
    humanize_research_dossier,
    calculate_burstiness,
    clean_ai_cliches,
)

__all__ = [
    "web_search_tool",
    "perform_web_search",
    "web_reader_tool",
    "read_url_content",
    "academic_search_tool",
    "perform_academic_search",
    "recall_past_research_tool",
    "store_verified_evidence_tool",
    "humanize_research_dossier",
    "calculate_burstiness",
    "clean_ai_cliches",
]
