"""Planning Task for the Research Manager.

Defines the planning step where the manager decomposes the research question
and outlines investigative avenues for the web and academic researchers.
"""

try:
    from crewai import Task, Agent
except Exception:
    class Task:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    Agent = object


def create_planning_task(agent: Agent, research_question: str) -> Task:
    """Create the research planning task for the Research Manager."""
    description = (
        f"Analyze the research question:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your task as Research Manager is to:\n"
        f"1. Deconstruct this inquiry into core dimensions, technical concepts, and key sub-questions.\n"
        f"2. Identify what empirical evidence, metrics, and documentation are required.\n"
        f"3. Provide targeted search queries and high-priority focus areas for the Web Researcher.\n"
        f"4. Provide targeted academic topics, keywords, and methodological areas for the Academic Researcher.\n"
        f"5. Outline the evidence verification criteria that the Evidence Analyst should check.\n\n"
        f"Do NOT conduct the web or academic search yourself. Focus strictly on creating a comprehensive "
        f"and structured research roadmap."
    )

    expected_output = (
        "A structured Research Plan containing:\n"
        "- Primary Research Objective & Scope\n"
        "- Key Investigative Sub-Questions\n"
        "- Web Research Priorities & Recommended Search Terms\n"
        "- Academic Literature Priorities & Scholarly Keywords\n"
        "- Critical Evidence Verification Criteria"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )
