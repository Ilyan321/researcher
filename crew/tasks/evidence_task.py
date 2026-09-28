"""Evidence Analysis Task for the Evidence Analyst Agent.

Directs the Evidence Analyst to cross-examine web and academic research findings,
flag contradictions, calibrate claim strengths, and produce an Evidence Audit Matrix.
"""

from typing import Optional, List

try:
    from crewai import Task, Agent
except ImportError:
    class Task:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    Agent = object


def create_evidence_task(
    agent: Agent,
    research_question: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the evidence audit task for the Evidence Analyst agent."""
    description = (
        f"Perform a comprehensive evidence audit, fact-check, and defensive risk evaluation for the research question:\n\n"
        f"\"{research_question}\"\n\n"
        f"Your objectives:\n"
        f"1. Scrutinize all web findings and academic literature provided by the research team.\n"
        f"2. Audit every major claim: Is the claim directly supported by the cited URL/DOI?\n"
        f"3. Identify Contradictions: Do web sources and academic benchmarks disagree on risk severity or effectiveness?\n"
        f"4. Calibrate Certainty: Restrict sweeping generalizations (e.g. 'Model X is 100% secure' -> 'Benchmark Y showed 0 exploits under conditions Z').\n"
        f"5. Categorize Evidence Strength (Strong, Moderate, Contested, Weak).\n"
        f"6. Construct Defense & Mitigation Rubric (for security/systems topics):\n"
        f"   - Identify root causes and threat/exploit vectors.\n"
        f"   - Evaluate provenance attestation (e.g., SLSA provenance, Sigstore/Cosign cryptographic signing, SBOM).\n"
        f"   - Classify mitigations into: Preventative Controls, Detective Monitoring, and Incident Playbooks.\n\n"
        f"Important: Do NOT invent new sources. Evaluate only the evidence presented by the upstream agents."
    )

    expected_output = (
        "A rigorous Evidence Audit Matrix containing:\n"
        "- Fact-Check Breakdown: Claims vs Supporting Evidence\n"
        "- Contradictions & Divergent Perspectives identified\n"
        "- Confidence Calibration (Strong, Moderate, Contested, Weak)\n"
        "- Structured Defense & Mitigation Rubric (Threat Vectors, Provenance Attestation, Preventative/Detective Controls)\n"
        "- Specific Guidance for the Research Writer on what can be asserted with high confidence vs caution"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks if context_tasks else None,
    )
