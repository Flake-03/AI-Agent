"""Explicit LangGraph routing between the two DSH agents."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from agents import AgentRunner
from models import WorkflowState
from prompts import knowledge_prompt, summary_prompt


def build_graph(documenter: AgentRunner, knowledge: AgentRunner, checkpointer=None):
    """Compile the durable orchestration graph around injected agent capabilities."""

    def route(state: WorkflowState) -> Literal["documenter", "knowledge"]:
        return "documenter" if state["action"] == "summarize" else "knowledge"

    async def run_documenter(state: WorkflowState) -> WorkflowState:
        result = await documenter.run(
            summary_prompt(state["project_id"], state.get("message", "")),
            state["thread_id"],
            state["project_id"],
        )
        return {
            "answer": result.answer,
            "finish_reason": result.finish_reason,
            "agent_session_id": result.session_id,
        }

    async def run_knowledge(state: WorkflowState) -> WorkflowState:
        result = await knowledge.run(
            knowledge_prompt(state["project_id"], state["message"]),
            state["thread_id"],
            state["project_id"],
        )
        return {
            "answer": result.answer,
            "finish_reason": result.finish_reason,
            "agent_session_id": result.session_id,
        }

    builder = StateGraph(WorkflowState)
    builder.add_node("documenter", run_documenter)
    builder.add_node("knowledge", run_knowledge)
    builder.add_conditional_edges(
        START, route, {"documenter": "documenter", "knowledge": "knowledge"}
    )
    builder.add_edge("documenter", END)
    builder.add_edge("knowledge", END)
    return builder.compile(checkpointer=checkpointer)
