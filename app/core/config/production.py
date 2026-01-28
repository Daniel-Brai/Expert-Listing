from shared.types import EnvironmentType

from .base import Settings as BaseSettings


class Settings(BaseSettings):
    """
    Production configuration settings.
    """

    APP_ENVIRONMENT: EnvironmentType = EnvironmentType.PRODUCTION
