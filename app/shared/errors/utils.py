from typing import Callable

from core.logging import get_logger
from fastapi import Request, status
from fastapi_problem.error import Problem
from shared.utils import get_obj_or_type_value

logger = get_logger(__name__)


def create_problem_handler(status_code: int, title: str, detail_message: str | None = None) -> Callable:
    """
    Factory function to create standard problem handlers.

    Args:
        status_code (int): HTTP status code
        title (str): Error title
        detail_message (str | None): Optional detail message

    Returns:
        A callable problem handler function.
    """

    def handler(_eh, request: Request, exc: type[Exception]) -> Problem:
        if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(
                "Unhandled generic exception caught",
                exc_info=(exc.__class__, exc, get_obj_or_type_value(exc, "__traceback__", None)),
            )
            detail = "An unexpected error occurred while trying to process your request. Please try again later."
            error_type = "internal_server_error"
            headers = {}

            return Problem(
                title=title,
                type_=error_type,
                status=status_code,
                detail=detail,
                instance=str(request.url.path),
            )

        detail = detail_message or get_obj_or_type_value(exc, "message") or str(exc)
        error_type = get_obj_or_type_value(exc, "error_type") or "internal_error"
        headers = get_obj_or_type_value(exc, "headers") or {}

        return Problem(
            title=title,
            type_=error_type,
            status=status_code,
            detail=detail,
            instance=str(request.url.path),
            headers=headers,  # type: ignore
        )

    return handler
