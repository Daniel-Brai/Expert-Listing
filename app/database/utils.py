import logging

from sqlmodel import text

from .session import db_session_manager

logger = logging.getLogger(__name__)


async def check_db_connection() -> bool:
    """
    Performs a simple database connectivity check by running `SELECT 1`.

    Returns:
        True if the database responded to the query, False otherwise.
    """

    try:
        async with db_session_manager() as session:
            query = await session.exec(text("SELECT 1"))  # type: ignore
            _ = query.one()
            return True

    except Exception as exc:
        logger.debug(f"Database connection check failed: {str(exc)}")
        return False
