"""FastAPI routes for Swagger-driven orchestration."""

import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request

from models import AgentResponse, ChatRequest, SummaryRequest
from runtime import lifespan

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the HTTP application with one owned runtime lifespan."""
    application = FastAPI(
        title="Project Agent Orchestrator",
        summary="Two DeepSeek Harness agents coordinated by LangGraph.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.get("/health", tags=["operations"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/ready", tags=["operations"])
    async def ready(request: Request) -> dict[str, str]:
        agents = getattr(request.app.state, "agents", None)
        if agents is None or not agents.ready:
            raise HTTPException(status_code=503, detail="agent runtimes are not ready")
        return {"status": "ready"}

    @application.post("/v1/summaries", response_model=AgentResponse, tags=["agents"])
    async def summarize(payload: SummaryRequest, request: Request) -> AgentResponse:
        return await invoke(
            request,
            action="summarize",
            project_id=payload.project_id,
            thread_id=payload.thread_id,
            message=payload.instructions,
        )

    @application.post("/v1/chat", response_model=AgentResponse, tags=["agents"])
    async def chat(payload: ChatRequest, request: Request) -> AgentResponse:
        return await invoke(
            request,
            action="chat",
            project_id=payload.project_id,
            thread_id=payload.thread_id,
            message=payload.message,
        )

    return application


async def invoke(
    request: Request,
    *,
    action: Literal["summarize", "chat"],
    project_id: str,
    thread_id: str,
    message: str,
) -> AgentResponse:
    """Invoke one graph run and normalize its completed state."""
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="orchestrator is not ready")
    try:
        result = await graph.ainvoke(
            {
                "action": action,
                "project_id": project_id,
                "thread_id": thread_id,
                "message": message,
            },
            {"configurable": {"thread_id": f"{action}:{project_id}:{thread_id}"}},
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("agent runtime failed")
        raise HTTPException(status_code=502, detail="agent runtime failed") from error
    return AgentResponse(
        thread_id=thread_id,
        agent_session_id=result["agent_session_id"],
        answer=result["answer"],
        finish_reason=result.get("finish_reason"),
    )


app = create_app()
