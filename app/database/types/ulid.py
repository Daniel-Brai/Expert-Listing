from typing import Any

from sqlalchemy import CHAR, TypeDecorator
from ulid import ULID


class ULIDType(TypeDecorator):
    """
    SQLAlchemy type decorator for ULID stored as CHAR(26).
    """

    impl = CHAR(26)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """
        Convert Python ULID to database string.
        """

        if value is None:
            return None
        if isinstance(value, ULID):
            return str(value)
        if isinstance(value, str):
            return str(ULID.from_str(value))

        raise ValueError(f"Cannot convert {type(value)} to ULID string")

    def process_result_value(self, value: str | None, dialect: Any) -> str | None:
        """
        Convert database string to Python ULID string.
        """

        if value is None:
            return None

        try:
            ulid = ULID.from_str(value)
            return str(ulid)
        except Exception as e:
            raise ValueError(f"Cannot convert database value to ULID: {e}")

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(26))

    def copy(self, **kw):
        return ULIDType()
