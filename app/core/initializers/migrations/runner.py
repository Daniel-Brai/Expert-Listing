from core.logging import get_logger
from core.settings import settings

from .alembic import run_migrations as _run_migrations

logger = get_logger(__name__)


def run_migrations() -> None:
    """
    Run alembic migrations if needed.

    This is a synchronous function that should be called before starting the async app.
    """

    if not settings.APP_RUN_MIGRATIONS:
        logger.info("Migrations disabled via settings (APP_RUN_MIGRATIONS=False)")
        return

    try:
        logger.info("Checking and running migrations if needed...")
        upgraded = _run_migrations()
        if upgraded:
            logger.info("Migrations were applied successfully.")
        else:
            logger.info("No migrations needed.")
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to run migrations: {str(exc)}")
        raise exc
