from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlmodel import Field


class SearchableMixin:
    """
    Mixin for models that support full-text search.

    Attributes:
        search_vector (str | None): The search vector for full-text search.
    """

    search_vector: str | None = Field(
        sa_type=TSVECTOR(),  # type: ignore[assignment]
        default=None,
        nullable=True,
    )
