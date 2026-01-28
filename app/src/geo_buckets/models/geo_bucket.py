from typing import TYPE_CHECKING

from database import IntegerIDMixin, TimestampMixin
from geoalchemy2 import Geometry
from sqlalchemy import TEXT, BigInteger, Column, Index
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from src.properties.models.property import Property


class GeoBucket(
    IntegerIDMixin,
    TimestampMixin,
    table=True,
):
    """
    Model representing a geographical bucket.

    Attributes:
        id (int): Unique identifier for the geo bucket.
        created_datetime (datetime): Timestamp when the geo bucket was created.
        updated_datetime (datetime | None): Timestamp when the geo bucket was last updated.
    """

    __table_args__ = (
        Index("idx_geo_buckets_h3", "h3_index"),
        Index("idx_geo_buckets_resolution", "h3_resolution"),
        Index("idx_geo_buckets_parent", "parent_h3"),
        Index(
            "idx_geo_buckets_name_trgm",
            "canonical_name_normalized",
            postgresql_using="gin",
            postgresql_ops={"canonical_name_normalized": "gin_trgm_ops"},
        ),
    )

    h3_index: int = Field(
        sa_column=Column(BigInteger, unique=True, index=True, nullable=False),
    )
    h3_resolution: int = Field(default=8, nullable=False)

    parent_h3: int | None = Field(
        sa_column=Column(BigInteger, nullable=True, index=True),
    )

    canonical_name: str = Field(sa_column=Column(TEXT(), nullable=True))
    canonical_name_normalized: str = Field(sa_column=Column(TEXT(), nullable=True))

    center_point: str | None = Field(
        sa_type=Geometry(geometry_type="POINT", srid=4326, spatial_index=True, nullable=True),  # type: ignore[arg-type]
    )

    hexagon_boundary: str | None = Field(
        sa_type=Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True, nullable=True),  # type: ignore[arg-type]
    )

    property_count: int = Field(default=0, nullable=False)

    properties: list["Property"] = Relationship(back_populates="geo_bucket")
