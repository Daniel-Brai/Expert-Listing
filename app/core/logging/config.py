import logging
import sys

import structlog
from core.logging.processors import add_correlation, add_process_metadata, drop_healthcheck_logs
from core.settings import settings
from structlog.contextvars import merge_contextvars

LOG_LEVEL_NAME = settings.APP_LOG_LEVEL
LOG_LEVEL_VALUE = logging.getLevelNamesMapping().get(LOG_LEVEL_NAME, "INFO")

if not isinstance(LOG_LEVEL_VALUE, int):
    raise ValueError(f"Invalid LOG_LEVEL: {settings.APP_LOG_LEVEL}")


def configure_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL_VALUE,
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL_VALUE),  # type: ignore
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        processors=[
            add_correlation,
            merge_contextvars,
            drop_healthcheck_logs,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
            add_process_metadata,  # type: ignore
            structlog.processors.dict_tracebacks,
            structlog.processors.EventRenamer("msg"),
            structlog.processors.JSONRenderer(),
        ],
    )
