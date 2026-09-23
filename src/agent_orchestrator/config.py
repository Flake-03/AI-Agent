"""Read required settings from the environment at startup."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    mcp_url: str
    database_url: str | None
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "replace_me":
            raise ValueError("OPENAI_API_KEY must be set")
        mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
        if not mcp_url.startswith(("http://", "https://")):
            raise ValueError("MCP_URL must be an HTTP(S) URL")
        port = int(os.getenv("AGENT_PORT", "8080"))
        if not 1 <= port <= 65535:
            raise ValueError("AGENT_PORT must be between 1 and 65535")
        return cls(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            mcp_url=mcp_url,
            database_url=os.getenv("DATABASE_URL") or None,
            host=os.getenv("AGENT_HOST", "127.0.0.1"),
            port=port,
        )
