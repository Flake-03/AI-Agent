from collections.abc import Callable, Mapping

from agents import Agent, AgentName, document_analyst, knowledge_assistant

from .state import Action, AgentResult, State

_ACTIONS: dict[Action, tuple[AgentName, Callable[[str, str], str]]] = {
    "summarize": (document_analyst.NAME, document_analyst.build_prompt),
    "chat": (knowledge_assistant.NAME, knowledge_assistant.build_prompt),
}


class AgentExecutor:
    """Execute graph actions with the agent assigned to each role."""

    def __init__(self, agents: Mapping[AgentName, Agent]) -> None:
        self._agents = agents

    async def __call__(self, state: State) -> AgentResult:
        agent_name, build_prompt = _ACTIONS[state["action"]]
        prompt = build_prompt(state["project_id"], state["message"])
        result = await self._agents[agent_name].run(prompt, state["thread_id"], state["project_id"])
        return {
            "answer": result.final_response,
            "finish_reason": result.finish_reason,
            "agent_session_id": result.session_id,
        }
