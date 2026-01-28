from bootstrap import create_app
from core.initializers import run_migrations
from core.logging import configure_logging
from core.settings import settings
from shared.types import EnvironmentType

configure_logging()

run_migrations()

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        loop="uvloop",
        host="0.0.0.0",
        port=settings.APP_PORT,
        log_level=settings.APP_LOG_LEVEL.lower(),
        reload=True if settings.APP_ENVIRONMENT == EnvironmentType.LOCAL else False,
        log_config=None,
        proxy_headers=True,
    )
