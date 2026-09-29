"""API and workflow data models."""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

PROJECT_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


class SummaryRequest(BaseModel):
    """Request a source inspection and reviewed documentation update."""

    project_id: str = Field(pattern=PROJECT_ID_PATTERN, examples=["deepseek-harness"])
    thread_id: str = Field(min_length=1, max_length=128, examples=["initial-summary"])
    instructions: str = Field(
        default="",
        max_length=4_000,
        examples=["Focus on runtime boundaries and deployment."],
    )


class ChatRequest(BaseModel):
    """Ask about merged documentation or request a documentation edit."""

    project_id: str = Field(pattern=PROJECT_ID_PATTERN, examples=["deepseek-harness"])
    thread_id: str = Field(min_length=1, max_length=128, examples=["team-question-1"])
    message: str = Field(
        min_length=1,
        max_length=20_000,
        examples=["How is the SDK runtime configured? Cite the relevant document."],
    )


class AgentResponse(BaseModel):
    """Completed DSH turn returned by the orchestrator."""

    thread_id: str
    agent_session_id: str
    answer: str
    finish_reason: str | None


class WorkflowState(TypedDict, total=False):
    """Raw durable state passed between LangGraph nodes."""

    action: Literal["summarize", "chat"]
    project_id: str
    thread_id: str
    message: str
    answer: str
    finish_reason: str | None
    agent_session_id: str
