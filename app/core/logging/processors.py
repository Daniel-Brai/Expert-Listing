import os
import socket
from typing import Any

import structlog
from asgi_correlation_id import correlation_id


def add_correlation(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:

    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id

    return event_dict


def add_process_metadata(
    _: Any,
    __: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:

    event_dict["process_id"] = os.getpid()
    event_dict["hostname"] = socket.gethostname()
    return event_dict


def drop_healthcheck_logs(
    _: Any,
    __: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:

    path: str | None = event_dict.get("path")

    if path is None:
        return event_dict

    is_healthcheck = path.endswith("/health")

    if is_healthcheck:
        raise structlog.DropEvent
    return event_dict
