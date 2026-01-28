from uuid import UUID, uuid4

import inflection
from database.types.ulid import ULIDType
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, SQLModel
from ulid import ULID


class BaseIDMixin(SQLModel):
    """
    A base mixin for models with a primary key.
    """

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # type: ignore
        return inflection.pluralize(inflection.underscore(cls.__name__))


class IntegerIDMixin(BaseIDMixin):
    """
    A mixin for models with an integer primary key.

    Attributes:
        id (int): The primary key field.
    """

    id: int = Field(index=True, primary_key=True)


class UUIDMixin(BaseIDMixin):
    """
    A mixin for models with a UUID primary key.

    Attributes:
        id (str): The primary key field.
    """

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class ULIDMixin(BaseIDMixin):
    """
    A mixin for models with a ULID primary key.

    Attributes:
        id (ULID): The primary key field.
    """

    id: str = Field(
        default_factory=lambda: str(ULID()),
        sa_type=ULIDType(),  # type: ignore[assignment]
        primary_key=True,
        index=True,
        nullable=False,
    )
