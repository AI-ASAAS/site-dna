"""Foundation Smoke Agent and Crew execution for Site DNA."""

import json

from crewai import Agent, Crew, Process, Task

from site_dna.core.llm import get_llm
from site_dna.core.logging import get_logger
from site_dna.schemas.health import SmokeAgentOutput

logger = get_logger(__name__)


def create_foundation_agent(llm=None) -> Agent:
    """Create the Site DNA Foundation verification agent."""
    active_llm = llm if llm is not None else get_llm()

    return Agent(
        role="AI System Verification Specialist",
        goal="Verify that CrewAI can execute an Agent and Task using the project's configured Gemini model.",
        backstory=(
            "An internal ASAAS AI engineering agent responsible for validating the "
            "model integration and basic execution pipeline for the Site DNA platform."
        ),
        verbose=False,
        allow_delegation=False,
        memory=False,
        llm=active_llm,
    )


def create_smoke_task(agent: Agent) -> Task:
    """Create the verification task with structured Pydantic output expectation."""
    return Task(
        description=(
            "Verify the Site DNA AI foundation. Respond with exactly: "
            "project as 'Site DNA', status as 'operational', and "
            "message as 'CrewAI Gemini integration successful'."
        ),
        expected_output="Structured JSON with project, status, and message fields.",
        agent=agent,
        output_pydantic=SmokeAgentOutput,
    )


def run_smoke_crew(llm=None) -> SmokeAgentOutput:
    """Assemble and execute the Foundation verification Crew.

    Returns:
        Validated SmokeAgentOutput instance.
    """
    logger.info("Initializing Site DNA Foundation smoke crew")
    agent = create_foundation_agent(llm=llm)
    task = create_smoke_task(agent=agent)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )

    crew_output = crew.kickoff()

    # Extract structured output from CrewOutput
    if hasattr(crew_output, "pydantic") and isinstance(crew_output.pydantic, SmokeAgentOutput):
        return crew_output.pydantic

    raw_text = str(crew_output.raw if hasattr(crew_output, "raw") else crew_output).strip()

    # Normalize if raw JSON text was returned
    try:
        # Strip markdown fences if present
        cleaned = raw_text
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        data = json.loads(cleaned)
        return SmokeAgentOutput(**data)
    except Exception as exc:
        logger.debug("Failed to parse raw crew output as JSON: %s. Using text fallback parsing.", exc)
        # Attempt fallback matching for operational signals
        project = "Site DNA" if "Site DNA" in raw_text else "Unknown"
        status = "operational" if "operational" in raw_text.lower() else "unverified"
        return SmokeAgentOutput(
            project=project,
            status=status,
            message=raw_text[:200],
        )
