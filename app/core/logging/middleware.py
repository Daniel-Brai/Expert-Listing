import time
from typing import Any

from core.logging.context import bind_log_context, clear_log_context
from starlette.types import ASGIApp, Message


class LoggingMiddleware:
    """
    ASGI-style middleware that binds logging context for each request

    It also adds an `X-Process-Time` header containing the request duration.
    """

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        path = scope.get("path", None)
        method = scope.get("method", None)

        logging_context: dict[str, Any] = {}

        if path is not None:
            logging_context["path"] = path
        if method is not None:
            logging_context["method"] = method

        bind_log_context(
            **logging_context,
        )

        async def send_wrapper(message: Message) -> None:
            if message.get("type") == "http.response.start":
                duration = time.time() - start_time
                headers = list(message.get("headers", []))
                headers.append((b"X-Process-Time", str(duration).encode()))
                message["headers"] = headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            clear_log_context()
