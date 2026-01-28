from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from core.logging import get_logger
from core.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

logger = get_logger(__name__)


def _get_alembic_config() -> Config:
    alembic_ini = Path(__file__).resolve().parents[3] / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))
    return cfg


def _get_db_current_revision(sync_connection) -> Optional[str]:
    mc = MigrationContext.configure(sync_connection)
    return mc.get_current_revision()


def _get_head_revisions(cfg: Config) -> set:
    script = ScriptDirectory.from_config(cfg)
    return set(script.get_heads())


def run_migrations() -> bool:
    """
    Checks DB revision and runs `alembic upgrade head` when the database is behind the latest migrations.

    Returns True when an upgrade was executed, False when DB was already up-to-date.

    This function should be called synchronously, not from within an async context.
    """

    cfg = _get_alembic_config()

    heads = _get_head_revisions(cfg)
    logger.debug(f"Local alembic heads: {heads}")

    sync_engine = create_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        pool_pre_ping=True,
        poolclass=NullPool,
        echo=False,
    )

    try:
        logger.info("Attempting to connect to database...")
        with sync_engine.connect() as conn:
            current = _get_db_current_revision(conn)

        logger.debug(f"DB current revision: {current}")

        if current is None or current not in heads:
            logger.info(f"Database migrations are outdated (current={current}, heads={heads}). Upgrading...")
            command.upgrade(cfg, "head")
            logger.info("Database migrations upgraded to head")
            return True

        logger.info(f"Database migrations already up-to-date (current={current}).")
        return False
    except Exception as e:
        logger.error(f"Migration connection/execution error: {str(e)}")
        raise
    finally:
        sync_engine.dispose()
        logger.debug("Migration engine disposed")
