from core.logging import bind_log_context
from fastapi import Request
from shared.constants import PROXY_COUNT, PROXY_HEADERS
from shared.utils import get_request_info
from starlette.types import ASGIApp


class RequestIPMiddleware:
    """
    ASGI-style middleware for extracting and logging request IP.

    This attaches the computed client IP to `scope['state']` so downstream
    request handlers and other middleware can read `request.state.client_ip`.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        trusted_proxies: list[str] | None = None,
        proxy_count: int | None = None,
        proxy_headers: list[str] | None = None,
    ) -> None:
        self.app = app
        self.trusted_proxies = trusted_proxies or []
        self.proxy_count = proxy_count or PROXY_COUNT
        self.proxy_headers = proxy_headers or PROXY_HEADERS

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        client_ip = get_request_info(request, keys=["ip_address"]).ip_address or "Unknown"

        request.state.client_ip = client_ip

        bind_log_context(
            request_ip=client_ip,
        )

        await self.app(scope, receive, send)
