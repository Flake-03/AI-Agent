import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agents import create_agents
from config import Settings
from orchestration.graph import build_graph

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    agents = create_agents(Settings())

    try:
        await asyncio.gather(*(agent.start() for agent in agents.values()))
        app.state.graph = build_graph(agents)
        yield
    finally:
        await asyncio.gather(*(agent.close() for agent in agents.values()), return_exceptions=True)


app = FastAPI(lifespan=lifespan)
app.include_router(router)
