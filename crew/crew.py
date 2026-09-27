"""Researcher AI — Master Crew Orchestration.

Assembles and executes the 5-agent research pipeline:
1. Research Manager -> Creates research plan & focus areas
2. Web Researcher -> Investigates live web & inspects key links
3. Academic Researcher -> Queries scholarly databases (arXiv, OpenAlex)
4. Evidence Analyst -> Fact-checks, audits claims & calibrates confidence
5. Research Writer -> Compiles final structured Markdown report with citations
"""

from typing import Optional, Dict, Any, List
from config import get_llm, DEFAULT_MODEL
from crew.agents.manager import create_manager
from crew.agents.web_researcher import create_web_researcher
from crew.agents.academic_researcher import create_academic_researcher
from crew.agents.evidence_analyst import create_evidence_analyst
from crew.agents.research_writer import create_research_writer

from crew.tasks.planning_task import create_planning_task
from crew.tasks.web_research_task import create_web_research_task
from crew.tasks.academic_task import create_academic_task
from crew.tasks.evidence_task import create_evidence_task
from crew.tasks.writing_task import create_writing_task


class ResearcherCrew:
    """Master multi-agent orchestrator for Researcher AI."""

    def __init__(
        self,
        model: Optional[str] = None,
        verbose: bool = True,
    ):
        self.model = model or DEFAULT_MODEL
        self.verbose = verbose
        self.llm = get_llm(model=self.model)

        # Initialize all 5 specialized agents
        self.manager = create_manager(llm=self.llm)
        self.web_researcher = create_web_researcher(llm=self.llm)
        self.academic_researcher = create_academic_researcher(llm=self.llm)
        self.evidence_analyst = create_evidence_analyst(llm=self.llm)
        self.research_writer = create_research_writer(llm=self.llm)

    def build_tasks(self, research_question: str) -> List[Any]:
        """Construct all 5 research tasks with inter-task context dependencies."""
        # 1. Planning Task (Manager)
        task_planning = create_planning_task(
            agent=self.manager,
            research_question=research_question,
        )

        # 2. Web Research Task (Web Researcher) - depends on plan
        task_web = create_web_research_task(
            agent=self.web_researcher,
            research_question=research_question,
            context_tasks=[task_planning],
        )

        # 3. Academic Research Task (Academic Researcher) - depends on plan
        task_academic = create_academic_task(
            agent=self.academic_researcher,
            research_question=research_question,
            context_tasks=[task_planning],
        )

        # 4. Evidence Audit Task (Evidence Analyst) - receives web & academic findings
        task_evidence = create_evidence_task(
            agent=self.evidence_analyst,
            research_question=research_question,
            context_tasks=[task_web, task_academic],
        )

        # 5. Writing Task (Research Writer) - receives all prior context
        task_writing = create_writing_task(
            agent=self.research_writer,
            research_question=research_question,
            context_tasks=[task_planning, task_web, task_academic, task_evidence],
        )

        return [task_planning, task_web, task_academic, task_evidence, task_writing]

    def kickoff(self, research_question: str) -> str:
        """Execute the entire multi-agent research workflow."""
        try:
            from crewai import Crew, Process
        except ImportError:
            raise ImportError(
                "crewai is required to run kickoff(). Ensure dependencies are installed."
            )

        tasks = self.build_tasks(research_question)
        agents = [
            self.manager,
            self.web_researcher,
            self.academic_researcher,
            self.evidence_analyst,
            self.research_writer,
        ]

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return str(result)


def run_research(research_question: str, model: Optional[str] = None) -> str:
    """Convenience function to run a complete research inquiry."""
    crew_instance = ResearcherCrew(model=model)
    return crew_instance.kickoff(research_question)
