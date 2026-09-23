"""The model -> MCP tools -> model orchestration graph."""

from collections.abc import Sequence

from langchain.tools import ToolNode
from langchain.tools.tool_node import tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, MessagesState, StateGraph


SYSTEM_PROMPT = (
    "Bạn là AI agent điều phối. Dùng các tool MCP khi chúng giúp trả lời yêu cầu. "
    "Không tự nhận đã gọi tool nếu chưa gọi. Trả lời rõ ràng bằng tiếng Việt."
)


def build_graph(model, tools: Sequence[BaseTool], checkpointer=None):
    """Build a LangGraph workflow with explicit model and tool nodes."""
    bound_model = model.bind_tools(list(tools))

    async def call_model(state: MessagesState) -> dict:
        response = await bound_model.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(list(tools)))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)
