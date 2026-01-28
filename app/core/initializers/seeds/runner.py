from core.logging import get_logger
from core.settings import settings
from database.session import db_session_manager

from .property import run as property_seed

logger = get_logger(__name__)


async def run_seeds() -> None:
    """
    Run all seeds inside a DB session.
    """

    if not settings.APP_RUN_SEEDS:
        logger.info("Seeding disabled via settings (APP_RUN_SEEDS=False)")
        return

    try:
        logger.info("Starting seeding process...")
        async with db_session_manager() as session:
            logger.info("Seeding properties and geo-buckets...")
            await property_seed(session)

        logger.info("Seeding finished successfully")
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        raise e
