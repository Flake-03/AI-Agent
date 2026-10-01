"""Run the orchestrator API."""

import uvicorn

from api import app
from config import Settings


def main() -> None:
    """Load validated settings and start Uvicorn."""
    settings = Settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
