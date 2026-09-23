"""HTTP API for the LangGraph agent."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agent_orchestrator.config import Settings
from agent_orchestrator.runtime import create_runtime


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=20000)


class ChatResponse(BaseModel):
    thread_id: str
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    async with create_runtime(settings) as graph:
        app.state.graph = graph
        yield
        del app.state.graph


app = FastAPI(title="LangGraph MCP Orchestrator", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    if not hasattr(request.app.state, "graph"):
        raise HTTPException(status_code=503, detail="Agent is not ready")
    return {"status": "ready"}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="Agent is not ready")
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=payload.message)]},
        {"configurable": {"thread_id": payload.thread_id}, "recursion_limit": 20},
    )
    return ChatResponse(thread_id=payload.thread_id, answer=str(result["messages"][-1].content))
