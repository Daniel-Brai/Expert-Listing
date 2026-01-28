class BadRequestException(Exception):
    """
    Bad request error
    """

    def __init__(self, message: str = "Invalid request."):
        self.message = message
        self.error_type = "bad_request"

        super().__init__(self.message)


class ResourceNotFoundException(Exception):
    """
    Resource not found
    """

    def __init__(self, resource_name: str | None = None):
        self.message = f"{resource_name} not found." if resource_name else "Resource not found."
        self.error_type = "resource_not_found"

        super().__init__(self.message)


class AppException(Exception):
    """
    Generic application exception to used for service related errors
    """

    def __init__(self, message: str):
        self.message = message
        self.error_type = "app_error"

        super().__init__(self.message)
