from typing import Any

from core.settings import settings
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from shared.types import EnvironmentType

from .middleware import OpenAPISecurityMiddleware


class OpenAPI:
    """
    OpenAPI configuration for the FastAPI application.
    """

    def __init__(
        self,
        docs_url: str = settings.OPENAPI_DOCS_URL,
        schema_path: str = settings.OPENAPI_JSON_SCHEMA_URL,
    ) -> None:
        self.docs_url = docs_url.rstrip("/")
        self.schema_url = f"{self.docs_url}{schema_path}"

    def setup(self, app: FastAPI) -> None:
        if settings.APP_ENVIRONMENT in [EnvironmentType.STAGING, EnvironmentType.PRODUCTION]:
            app.add_middleware(OpenAPISecurityMiddleware)

        @app.get(
            self.docs_url,
            include_in_schema=False,
            response_class=HTMLResponse,
        )
        async def get_swagger_documentation() -> HTMLResponse:
            return get_swagger_ui_html(
                openapi_url=self.schema_url,
                title=settings.APP_NAME,
            )

        @app.get(
            self.schema_url,
            include_in_schema=False,
        )
        async def openapi() -> dict[str, Any]:
            return get_openapi(
                title=settings.APP_NAME,
                description=settings.APP_DESCRIPTION,
                version=settings.APP_VERSION,
                routes=app.routes,
            )


openapi = OpenAPI()
