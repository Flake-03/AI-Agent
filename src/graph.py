from langgraph.graph import END, START, StateGraph

from agents import DshAgent
from prompts import documenter_prompt, knowledge_prompt
from state import AgentName, State


def build_graph(agents: dict[AgentName, DshAgent]):
    def route(state: State) -> AgentName:
        return "documenter" if state["action"] == "summarize" else "knowledge"

    async def call(
        agent: AgentName, prompt: str, state: State
    ) -> dict[str, str | None]:
        result = await agents[agent].run(
            prompt, state["thread_id"], state["project_id"]
        )
        return {
            "answer": result.final_response,
            "finish_reason": result.finish_reason,
            "agent_session_id": result.session_id,
        }

    async def documenter(state: State) -> dict:
        return await call(
            "documenter",
            documenter_prompt(state["project_id"], state["message"]),
            state,
        )

    async def knowledge(state: State) -> dict:
        return await call(
            "knowledge",
            knowledge_prompt(state["project_id"], state["message"]),
            state,
        )

    builder = StateGraph(State)
    builder.add_node("documenter", documenter)
    builder.add_node("knowledge", knowledge)
    builder.add_conditional_edges(
        START, route, {"documenter": "documenter", "knowledge": "knowledge"}
    )
    builder.add_edge("documenter", END)
    builder.add_edge("knowledge", END)
    return builder.compile()
