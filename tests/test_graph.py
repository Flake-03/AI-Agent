"""Verify model/tool routing without a paid model or external MCP server."""

import asyncio

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from agent_orchestrator.graph import build_graph


@tool
def greet(name: str) -> str:
    """Greet a person."""
    return f"Xin chào, {name}!"


class FakeModel:
    def bind_tools(self, tools):
        assert [item.name for item in tools] == ["greet"]
        return self

    async def ainvoke(self, messages):
        if any(isinstance(message, ToolMessage) for message in messages):
            return AIMessage(content="Đã dùng MCP tool để chào An.")
        return AIMessage(
            content="",
            tool_calls=[{"name": "greet", "args": {"name": "An"}, "id": "call_1"}],
        )


def test_graph_routes_to_tool_and_back() -> None:
    async def check() -> None:
        graph = build_graph(FakeModel(), [greet], InMemorySaver())
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Hãy chào An")]},
            {"configurable": {"thread_id": "test-thread"}},
        )
        assert any(
            isinstance(message, ToolMessage) and message.content == "Xin chào, An!"
            for message in result["messages"]
        )
        assert result["messages"][-1].content == "Đã dùng MCP tool để chào An."

    asyncio.run(check())
