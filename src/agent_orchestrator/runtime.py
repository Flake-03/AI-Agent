"""Own model, MCP connection, and checkpoint lifetime."""

from contextlib import AsyncExitStack, asynccontextmanager

from langchain.mcp import MCPAdapter
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent_orchestrator.config import Settings
from agent_orchestrator.graph import build_graph


@asynccontextmanager
async def create_runtime(settings: Settings):
    async with AsyncExitStack() as stack:
        adapter = await stack.enter_async_context(MCPAdapter(settings.mcp_url))
        tools = await adapter.list_tools()
        if not tools:
            raise RuntimeError("MCP server did not expose any tools")

        if settings.database_url:
            checkpointer = await stack.enter_async_context(
                AsyncPostgresSaver.from_conn_string(settings.database_url)
            )
            await checkpointer.setup()
        else:
            checkpointer = InMemorySaver()

        model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
        yield build_graph(model, tools, checkpointer)
