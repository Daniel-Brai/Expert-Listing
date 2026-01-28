from typing import Callable, Self

from core.settings import settings
from fastapi_problem.cors import CorsConfiguration
from fastapi_problem.handler import new_exception_handler
from shared.errors.handlers import (
    app_exception_handler,
    authentication_handler,
    bad_request_handler,
    base_error_handler,
    invalid_auth_format_handler,
    invalid_credentials_handler,
    missing_token_handler,
    resource_not_found_handler,
)
from shared.exceptions import (
    AppException,
    AuthenticationException,
    BadRequestException,
    InvalidAuthenticationFormatException,
    InvalidCredentialsException,
    InvalidSessionException,
    ResourceNotFoundException,
)


class ExceptionHandlerRegistry:
    """
    Registry for exception handlers to be applied to a FastAPI app.
    """

    def __init__(self):
        self._handlers: dict[type[Exception], Callable] = {}

    def register(self, exception_class: type[Exception], handler: Callable) -> Self:
        self._handlers[exception_class] = handler
        return self

    def register_many(self, handlers: dict[type[Exception], Callable]) -> Self:
        self._handlers.update(handlers)
        return self

    @property
    def handlers(self) -> dict[type[Exception], Callable]:
        return self._handlers.copy()


exception_registry = ExceptionHandlerRegistry()


exception_registry.register_many(
    {
        AppException: app_exception_handler,
        BadRequestException: bad_request_handler,
        ResourceNotFoundException: resource_not_found_handler,
        AuthenticationException: authentication_handler,
        InvalidAuthenticationFormatException: invalid_auth_format_handler,
        InvalidCredentialsException: invalid_credentials_handler,
        InvalidSessionException: missing_token_handler,
        # The generic exception handler should be the last resort
        Exception: base_error_handler,
    }
)

eh = new_exception_handler(
    cors=CorsConfiguration(
        allow_origins=[str(origin).strip("/") for origin in settings.APP_CORS_ORIGINS],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    ),
    handlers=exception_registry.handlers,
)
