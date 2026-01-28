import base64

from core.logging import get_logger
from core.settings import settings
from fastapi import Request
from shared.exceptions import InvalidAuthenticationFormatException, InvalidCredentialsException, InvalidSessionException
from starlette.types import ASGIApp

logger = get_logger(__name__)


class OpenAPISecurityMiddleware:
    """
    ASGI-style middleware to secure OpenAPI documentation endpoints with basic authentication.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        username: str = settings.OPENAPI_USERNAME,
        password: str = settings.OPENAPI_PASSWORD,
    ) -> None:
        self.app = app

        self.username = username
        self.password = password

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "http":
            request = Request(scope, receive=receive)
            if request.url.path in [
                settings.OPENAPI_DOCS_URL,
                settings.OPENAPI_JSON_SCHEMA_URL,
            ]:
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    raise InvalidSessionException(headers={"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'})

                try:
                    auth_type, auth_value = auth_header.split()
                    if auth_type.lower() != "basic":
                        raise InvalidAuthenticationFormatException(
                            headers={"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'}
                        )

                    decoded = base64.b64decode(auth_value).decode()
                    username, password = decoded.split(":")

                    if username != self.username or password != self.password:
                        raise InvalidCredentialsException(
                            headers={"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'}
                        )

                except Exception:
                    raise InvalidCredentialsException(
                        headers={"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'}
                    )

        await self.app(scope, receive, send)
