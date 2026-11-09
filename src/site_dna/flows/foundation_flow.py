"""Foundation CrewAI Flow for Site DNA execution orchestration."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.agents.smoke_agent import run_smoke_crew
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.health import SmokeAgentOutput

logger = get_logger(__name__)


class FoundationFlowState(BaseModel):
    """Structured Pydantic state maintained across Flow execution steps."""

    project_name: str = Field(default="Site DNA", description="Name of the project")
    run_id: str = Field(default="", description="Unique execution run identifier")
    execution_status: str = Field(default="pending", description="Status: pending, running, completed, failed")
    model_name: str = Field(default="", description="Target Gemini model identifier")
    agent_output: Optional[SmokeAgentOutput] = Field(default=None, description="Output from smoke agent")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp of flow start")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp of flow completion")
    error_message: Optional[str] = Field(default=None, description="Error details if flow fails")


class FoundationFlow(Flow[FoundationFlowState]):
    """Foundational CrewAI Flow orchestrating initialization and smoke agent execution."""

    def __init__(self, llm=None, settings: Optional[Settings] = None):
        super().__init__()
        self._llm = llm
        self._settings = settings or get_settings()

    @start()
    def initialize_workflow(self) -> str:
        """Step 1: Initialize workflow state, generate run_id, and record timestamps."""
        self.state.run_id = f"flow-{uuid.uuid4().hex[:8]}"
        self.state.model_name = self._settings.gemini_model
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "Flow initialized: run_id=%s, model=%s",
            self.state.run_id,
            self.state.model_name,
        )
        return self.state.run_id

    @listen(initialize_workflow)
    def execute_foundation_agent(self, run_id: str) -> FoundationFlowState:
        """Step 2: Execute foundation agent and update flow state with results."""
        self.state.execution_status = "running"
        logger.info("Executing foundation agent step for run_id=%s", self.state.run_id)

        try:
            output = run_smoke_crew(llm=self._llm)
            self.state.agent_output = output
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info("Foundation agent step completed successfully for run_id=%s", self.state.run_id)
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error(
                "Foundation agent execution failed in flow run_id=%s: %s",
                self.state.run_id,
                self.state.error_message,
            )
            # Re-raise so callers/flows know execution failed
            raise

        return self.state
