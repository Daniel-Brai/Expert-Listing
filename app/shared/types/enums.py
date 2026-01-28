from enum import StrEnum


class EnvironmentType(StrEnum):
    """
    Enumeration for different application environments.

    Attributes:
        LOCAL (str): Local development environment.
        STAGING (str): Staging environment for testing.
        PRODUCTION (str): Production environment.
    """

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
