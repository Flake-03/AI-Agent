"""Verify the public API contract using an injected graph."""

import asyncio

import httpx
from langchain_core.messages import AIMessage

from agent_orchestrator.api import app


class FakeGraph:
    async def ainvoke(self, state, config):
        assert config["configurable"]["thread_id"] == "demo"
        assert state["messages"][0].content == "Xin chào"
        return {"messages": [AIMessage(content="Chào bạn!")]}


def test_chat_endpoint() -> None:
    async def check() -> None:
        app.state.graph = FakeGraph()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                assert (await client.get("/ready")).status_code == 200
                response = await client.post(
                    "/chat", json={"thread_id": "demo", "message": "Xin chào"}
                )
                assert response.status_code == 200
                assert response.json() == {"thread_id": "demo", "answer": "Chào bạn!"}
        finally:
            del app.state.graph

    asyncio.run(check())
