"""Researcher AI Crew Package."""


def __getattr__(name):
    if name in ("ResearcherCrew", "run_research"):
        from crew.crew import ResearcherCrew, run_research
        if name == "ResearcherCrew":
            return ResearcherCrew
        return run_research
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "ResearcherCrew",
    "run_research",
]
