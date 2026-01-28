from functools import lru_cache

from core.config import BaseSettings, LocalSettings, ProductionSettings, StagingSettings
from shared.types import EnvironmentType


@lru_cache(maxsize=1)
def _get_settings() -> BaseSettings:
    """
    Returns the appropriate settings based on the environment.

    Returns:
        BaseSettings: The settings for the specified environment

    Raises:
        ValueError: If an invalid environment is specified
    """

    environment = EnvironmentType(BaseSettings().APP_ENVIRONMENT.lower())  # type: ignore

    settings_map = {
        EnvironmentType.LOCAL: LocalSettings,
        EnvironmentType.STAGING: StagingSettings,
        EnvironmentType.PRODUCTION: ProductionSettings,
    }

    if environment not in settings_map:
        raise ValueError(
            f"Invalid environment: {environment.value}. "
            f"Must be one of {', '.join(env.value for env in EnvironmentType)}"
        )

    return settings_map[environment]()  # type: ignore


settings = _get_settings()
