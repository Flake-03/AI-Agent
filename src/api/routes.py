from fastapi import APIRouter, Request

from orchestration.state import Action

from .schemas import AgentRequest, AgentResponse, ChatRequest, SummaryRequest

router = APIRouter()


@router.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/summaries", response_model=AgentResponse, tags=["agents"])
async def summarize(payload: SummaryRequest, request: Request) -> AgentResponse:
    return await _invoke(request, "summarize", payload, payload.instructions)


@router.post("/v1/chat", response_model=AgentResponse, tags=["agents"])
async def chat(payload: ChatRequest, request: Request) -> AgentResponse:
    return await _invoke(request, "chat", payload, payload.message)


async def _invoke(request: Request, action: Action, payload: AgentRequest, message: str) -> AgentResponse:
    result = await request.app.state.graph.ainvoke(
        {
            "action": action,
            "project_id": payload.project_id,
            "thread_id": payload.thread_id,
            "message": message,
        }
    )
    return AgentResponse(
        thread_id=payload.thread_id,
        agent_session_id=result["agent_session_id"],
        answer=result["answer"],
        finish_reason=result.get("finish_reason"),
    )
