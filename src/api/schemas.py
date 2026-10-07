from pydantic import BaseModel, ConfigDict, Field

PROJECT_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


class AgentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(pattern=PROJECT_ID_PATTERN)
    thread_id: str = Field(min_length=1, max_length=128)


class SummaryRequest(AgentRequest):
    instructions: str = Field(default="", max_length=4_000)


class ChatRequest(AgentRequest):
    message: str = Field(min_length=1, max_length=20_000)


class AgentResponse(BaseModel):
    thread_id: str
    agent_session_id: str
    answer: str
    finish_reason: str | None = None
