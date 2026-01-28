from typing import Any


class DatabaseException(Exception):
    """
    Base exception for database-related errors.
    """

    def __init__(self, message: str = "An error occurred with the database operation.", metadata: Any = None):
        self.message = message
        self.metadata = metadata

        super().__init__(self.message)
