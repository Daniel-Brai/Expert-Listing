class AuthenticationException(Exception):
    """
    Base auth exception
    """

    def __init__(
        self,
        message: str = "Authentication error",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message
        self.error_type = "authentication_error"
        self.headers = headers or {}

        super().__init__(self.message)


class InvalidAuthenticationFormatException(AuthenticationException):
    """
    Invalid authentication format
    """

    def __init__(
        self,
        message: str = "Invalid authentication format",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message, headers)


class InvalidCredentialsException(AuthenticationException):
    """
    Invalid login credentials
    """

    def __init__(
        self,
        message: str = "Invalid email or password",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message, headers)


class InvalidSessionException(AuthenticationException):
    """
    Missing authentication token
    """

    def __init__(
        self,
        message: str = "Invalid or missing authentication token",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message, headers)
