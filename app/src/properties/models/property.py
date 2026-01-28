from typing import TYPE_CHECKING, Any, Optional

from database import TimestampMixin, ULIDMixin
from geoalchemy2 import Geometry
from sqlalchemy import TEXT, BigInteger, Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from src.geo_buckets.models.geo_bucket import GeoBucket


class Property(ULIDMixin, TimestampMixin, table=True):
    """
    Model representing a property listing.

    Attributes:
        id (ULID): Unique identifier for the property.
        title (str): Title of the property listing.
        location_name (str): Name of the property's location.
        location_name_normalized (str): Normalized location name for fuzzy matching.
        coordinates (str | None): Geographical coordinates of the property in WKT format.
        h3_index_r8 (int): H3 index at resolution 8 (~461m).
        h3_index_r9 (int): H3 index at resolution 9 (~174m).
        geo_bucket_id (int | None): Foreign key referencing the associated geo bucket.
    """

    __table_args__ = (
        Index("idx_properties_h3_r8", "h3_index_r8"),
        Index("idx_properties_h3_r9", "h3_index_r9"),
        Index("idx_properties_bucket", "geo_bucket_id"),
        Index(
            "idx_properties_name_trgm",
            "location_name_normalized",
            postgresql_using="gin",
            postgresql_ops={"location_name_normalized": "gin_trgm_ops"},
        ),
    )

    title: str = Field(sa_column=Column(TEXT(), nullable=False))
    location_name: str = Field(sa_column=Column(TEXT(), nullable=False))
    location_name_normalized: str = Field(sa_column=Column(TEXT(), nullable=False))

    coordinates: str = Field(
        sa_type=Geometry(geometry_type="POINT", srid=4326, spatial_index=True, nullable=False),  # type: ignore[arg-type]
    )

    h3_index_r8: int = Field(
        sa_column=Column(BigInteger(), nullable=False, index=True), description="H3 index at resolution 8 (~461m)"
    )

    h3_index_r9: int = Field(
        sa_column=Column(BigInteger, nullable=False, index=True), description="H3 index at resolution 9 (~174m)"
    )

    attributes: dict[str, Any] | None = Field(
        sa_column=Column(
            JSONB(),
            nullable=True,
            default=None,
        )
    )

    geo_bucket_id: int | None = Field(default=None, foreign_key="geo_buckets.id", ondelete="SET NULL")
    geo_bucket: Optional["GeoBucket"] = Relationship(back_populates="properties")
