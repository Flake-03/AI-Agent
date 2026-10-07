from langgraph.graph import END, START, StateGraph

from agents import Agent, AgentName

from .executor import AgentExecutor
from .state import State


def build_graph(agents: dict[AgentName, Agent]):
    """Build the graph that routes API actions to their executors."""

    builder = StateGraph(State)

    builder.add_node("execute", AgentExecutor(agents))

    builder.add_edge(START, "execute")
    builder.add_edge("execute", END)

    return builder.compile()
