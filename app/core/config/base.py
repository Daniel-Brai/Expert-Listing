from pathlib import Path
from typing import Annotated, Literal, Self

from dotenv import load_dotenv
from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.types import EnvironmentType
from shared.utils import validate_bool, validate_list

load_dotenv()


class Settings(BaseSettings):
    """
    Base configuration settings for the Expert Listing application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="forbid",
    )

    APP_DIR: str = str(Path(__file__).resolve().parents[3])
    APP_NAME: str = "Expert Listing"
    APP_DESCRIPTION: str = "Expert Listing API Backend"
    APP_VERSION: str = "0.1.0"
    APP_DOMAIN: str = "localhost"
    APP_DOMAIN_IS_SECURE: Annotated[bool, BeforeValidator(validate_bool())] = False
    APP_PORT: int = 8000
    APP_ENVIRONMENT: EnvironmentType = EnvironmentType.LOCAL
    APP_RUN_SEEDS: Annotated[bool, BeforeValidator(validate_bool())] = True
    APP_RUN_MIGRATIONS: Annotated[bool, BeforeValidator(validate_bool())] = False
    APP_CORS_ORIGINS: Annotated[list[AnyUrl | str], BeforeValidator(validate_list())] = []
    APP_LOG_LEVEL: Literal[
        "FATAL",
        "WARN",
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG",
    ] = "INFO"
    APP_METRICS_URL: str = "/metrics"

    OPENAPI_USERNAME: str = "Administrator"
    OPENAPI_PASSWORD: str = "Password@123"
    OPENAPI_DOCS_URL: str = "/docs"
    OPENAPI_JSON_SCHEMA_URL: str = "/openapi.json"
    V1_STR: str = "v1"

    SENTRY_DSN: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_WORKERS_COUNT(self) -> int:
        if self.APP_ENVIRONMENT == EnvironmentType.LOCAL:
            return 1
        return 4

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_SERVER_URL(self) -> str:
        scheme = "https" if self.APP_DOMAIN_IS_SECURE else "http"

        if self.APP_DOMAIN.startswith("http") or self.APP_DOMAIN.startswith("https"):
            return self.APP_DOMAIN

        if self.APP_ENVIRONMENT == EnvironmentType.LOCAL:
            return f"{scheme}://{self.APP_DOMAIN}:{self.APP_PORT}"

        return f"{scheme}://{self.APP_DOMAIN}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_V1_STR(self) -> str:
        return f"/api/{self.V1_STR}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def APP_SERVER_PORT(self) -> int:
        if self.APP_ENVIRONMENT == EnvironmentType.LOCAL:
            return int(self.APP_PORT)

        return 443 if self.APP_ENVIRONMENT == EnvironmentType.PRODUCTION else 80

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int | None = None
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_QUERY: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
            query=self.POSTGRES_QUERY,
        )

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("OPENAPI_PASSWORD", self.OPENAPI_PASSWORD)

        return self

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "Password123":
            message = (
                f'The value of {var_name} is "Password123", '
                "for security, please change it, at least for deployments."
            )
            if self.APP_ENVIRONMENT in [
                EnvironmentType.PRODUCTION,
                EnvironmentType.STAGING,
            ]:
                raise ValueError(message)
