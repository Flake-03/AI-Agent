"""Application lifetime for DSH runtimes and LangGraph persistence."""

from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

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

    async with AsyncExitStack() as stack:
        database_url = (
            settings.database_url.get_secret_value() if settings.database_url else None
        )
        if database_url:
            checkpointer = await stack.enter_async_context(
                AsyncPostgresSaver.from_conn_string(database_url)
            )
            await checkpointer.setup()
        else:
            checkpointer = InMemorySaver()

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
        app.state.graph = build_graph(agents.documenter, agents.knowledge, checkpointer)
        try:
            yield
        finally:
            await agents.close()
            del app.state.graph
            del app.state.agents
