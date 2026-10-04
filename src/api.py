import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from agents import DshAgent
from config import Settings
from graph import build_graph
from prompts import SYSTEM_PROMPTS
from state import Action, AgentName

logger = logging.getLogger(__name__)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    agents: dict[AgentName, DshAgent] = {
        name: DshAgent(name, prompt, settings)
        for name, prompt in SYSTEM_PROMPTS.items()
    }
    try:
        async with asyncio.TaskGroup() as tasks:
            for agent in agents.values():
                tasks.create_task(agent.start())
        app.state.graph = build_graph(agents)
        yield
    finally:
        await asyncio.gather(
            *(agent.close() for agent in agents.values()), return_exceptions=True
        )


app = FastAPI(
    title="Project Agent Orchestrator",
    summary="Project documentation agents routed by LangGraph.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/summaries", response_model=AgentResponse, tags=["agents"])
async def summarize(payload: SummaryRequest, request: Request) -> AgentResponse:
    return await invoke(request, "summarize", payload, payload.instructions)


@app.post("/v1/chat", response_model=AgentResponse, tags=["agents"])
async def chat(payload: ChatRequest, request: Request) -> AgentResponse:
    return await invoke(request, "chat", payload, payload.message)


async def invoke(
    request: Request,
    action: Action,
    payload: AgentRequest,
    message: str,
) -> AgentResponse:
    try:
        result = await request.app.state.graph.ainvoke(
            {
                "action": action,
                "project_id": payload.project_id,
                "thread_id": payload.thread_id,
                "message": message,
            }
        )
    except Exception as error:
        logger.exception("agent runtime failed")
        raise HTTPException(status_code=502, detail="agent runtime failed") from error
    return AgentResponse(
        thread_id=payload.thread_id,
        agent_session_id=result["agent_session_id"],
        answer=result["answer"],
        finish_reason=result.get("finish_reason"),
    )
