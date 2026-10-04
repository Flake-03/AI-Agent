import uvicorn

from api import app
from config import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
