import uuid
from contextlib import asynccontextmanager

from anyio import to_thread
from core.settings import settings
from fastapi import FastAPI
from fastapi_pagination import add_pagination as setup_pagination
from shared.errors import setup_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Lifespan context manager for FastAPI application.
    """

    from core.initializers.seeds import run_seeds

    to_thread.current_default_thread_limiter().total_tokens = 60

    # Startup actions
    await run_seeds()

    yield


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS settings.
    """

    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.APP_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_openapi(app: FastAPI) -> None:
    """
    Setup OpenAPI configuration.
    """

    from core.openapi import openapi

    openapi.setup(app)


def setup_middlewares(app: FastAPI) -> None:
    """
    Setup middlewares for the FastAPI application.
    """

    from asgi_correlation_id import CorrelationIdMiddleware
    from core.logging.middleware import LoggingMiddleware
    from core.middlewares.request_ip import RequestIPMiddleware
    from fastapi.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware, compresslevel=5, minimum_size=1000)
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
        update_request_header=True,
        generator=lambda: uuid.uuid4().hex,
    )
    app.add_middleware(RequestIPMiddleware)
    app.add_middleware(LoggingMiddleware)


def setup_routes(app: FastAPI) -> None:
    """
    Setup application routes.
    """

    from src.geo_buckets.api import geo_buckets_v1_router
    from src.properties.api import properties_v1_router

    # V1 Routes
    app.include_router(
        properties_v1_router,
        prefix=f"{settings.APP_V1_STR}/properties",
        tags=["Properties"],
    )
    app.include_router(
        geo_buckets_v1_router,
        prefix=f"{settings.APP_V1_STR}/geo-buckets",
        tags=["Geo Buckets"],
    )


def setup_root_path(app: FastAPI) -> None:
    """
    Setup root path redirection to docs.
    """

    from fastapi.responses import RedirectResponse

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")


def setup_health_check(app: FastAPI) -> None:
    """
    Add health check endpoint.
    """

    from database.utils import check_db_connection

    @app.get("/health", include_in_schema=False)
    async def health_check():
        is_systems_operational = {
            "database": await check_db_connection(),
        }

        if not all(is_systems_operational.values()):
            return {
                "status": "unhealthy",
            }

        return {
            "status": "healthy",
        }


def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    setup_exception_handler(app)

    setup_pagination(app)

    setup_cors(app)

    setup_middlewares(app)

    setup_root_path(app)

    setup_routes(app)

    setup_health_check(app)

    setup_openapi(app)

    return app
