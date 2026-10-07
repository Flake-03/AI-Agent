from typing import Literal, NotRequired, TypedDict

Action = Literal["summarize", "chat"]


class State(TypedDict):
    action: Action
    project_id: str
    thread_id: str
    message: str
    answer: NotRequired[str]
    finish_reason: NotRequired[str | None]
    agent_session_id: NotRequired[str]


class AgentResult(TypedDict):
    answer: str
    finish_reason: str | None
    agent_session_id: str
