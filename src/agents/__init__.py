from config import Settings

from . import document_analyst, knowledge_assistant
from .base import Agent, AgentName


def create_agents(settings: Settings) -> dict[AgentName, Agent]:
    return {
        document_analyst.NAME: document_analyst.create(settings),
        knowledge_assistant.NAME: knowledge_assistant.create(settings),
    }
