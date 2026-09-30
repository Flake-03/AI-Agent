"""Application lifetime for DSH runtimes and LangGraph persistence."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver

from agents import AgentRuntime, DshAgentRunner
from config import Settings
from graph import build_graph
from prompts import (
    DOCUMENTER_SYSTEM_PROMPT,
    KNOWLEDGE_SYSTEM_PROMPT,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create durable graph state and exactly two DSH runtimes."""
    settings = Settings()

    agents = AgentRuntime(
        documenter=DshAgentRunner(
            "documenter",
            DOCUMENTER_SYSTEM_PROMPT,
            settings.dsh_document_home,
            settings,
        ),
        knowledge=DshAgentRunner(
            "knowledge",
            KNOWLEDGE_SYSTEM_PROMPT,
            settings.dsh_knowledge_home,
            settings,
        ),
    )
    await agents.start()
    app.state.agents = agents
    app.state.graph = build_graph(agents.documenter, agents.knowledge, InMemorySaver())
    try:
        yield
    finally:
        await agents.close()
        del app.state.graph
        del app.state.agents
