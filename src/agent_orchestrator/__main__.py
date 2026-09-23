"""Run the HTTP API with Uvicorn."""

import uvicorn

from agent_orchestrator.config import Settings


if __name__ == "__main__":
    settings = Settings.from_env()
    uvicorn.run("agent_orchestrator.api:app", host=settings.host, port=settings.port)
