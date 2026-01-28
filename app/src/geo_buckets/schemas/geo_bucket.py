from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from shared.utils import optional

if TYPE_CHECKING:
    from src.geo_buckets.models.geo_bucket import GeoBucket


class GeoBucketBase(BaseModel):
    """
    Base schema for GeoBucket.
    """

    h3_index: int = Field(..., description="H3 index of the geo bucket")
    h3_resolution: int = Field(..., description="H3 resolution level of the geo bucket")
    parent_h3: int | None = Field(default=None, description="Parent H3 index of the geo bucket")
    canonical_name: str | None = Field(default=None, description="Human readable canonical name")
    canonical_name_normalized: str | None = Field(default=None, description="Normalized name for fuzzy matching")
    center_point: str | None = Field(default=None, description="WKT POINT of the bucket centroid")
    hexagon_boundary: str | None = Field(default=None, description="WKT POLYGON of the H3 cell")
    property_count: int = Field(default=0, description="Number of properties in this bucket")


class GeoBucketCreate(GeoBucketBase):
    """Schema used when creating a GeoBucket (all base fields allowed)."""


@optional
class GeoBucketUpdate(GeoBucketCreate):
    """
    Optional fields for updating a GeoBucket
    """

    pass


class GeoBucketRead(GeoBucketBase):
    """
    Schema returned by API for a single GeoBucket
    """

    id: int = Field(..., description="Identifier for the geo bucket")
    created_datetime: str = Field(..., description="Creation timestamp (ISO format)")
    updated_datetime: str | None = Field(default=None, description="Last update timestamp (ISO format)")

    @classmethod
    def from_model(cls, model: "GeoBucket") -> "GeoBucketRead":
        """
        Create a read-schema from a `GeoBucket` SQLModel instance.
        """

        return cls(
            id=int(model.id),
            h3_index=int(model.h3_index),
            h3_resolution=int(model.h3_resolution),
            parent_h3=int(model.parent_h3) if model.parent_h3 is not None else None,
            canonical_name=model.canonical_name,
            canonical_name_normalized=model.canonical_name_normalized,
            center_point=(str(model.center_point) if model.center_point is not None else None),
            hexagon_boundary=(str(model.hexagon_boundary) if model.hexagon_boundary is not None else None),
            property_count=int(model.property_count or 0),
            created_datetime=model.created_datetime.isoformat(),
            updated_datetime=(model.updated_datetime.isoformat() if model.updated_datetime else None),
        )


class GeoBucketDistribution(BaseModel):
    """
    Schema for the distribution of properties across buckets

    Attributes:
        bucket_id (int): The ID of the geo bucket
        h3_index (str): The H3 index of the geo bucket
        canonical_name (str): The canonical name of the geo bucket
        property_count (int): Number of properties in the bucket
        center_lat (float): Latitude of the bucket's center point
        center_lng (float): Longitude of the bucket's center point
    """

    bucket_id: int = Field(..., description="The ID of the geo bucket")
    h3_index: str = Field(..., description="The H3 index of the geo bucket")
    canonical_name: str = Field(..., description="The canonical name of the geo bucket")
    property_count: int = Field(..., description="Number of properties in the bucket")
    center_lat: float = Field(..., description="Latitude of the bucket's center point")
    center_lng: float = Field(..., description="Longitude of the bucket's center point")


class GeoBucketResolutions(BaseModel):
    """
    Schema for the statistics for a specific H3 resolution

    Attributes:
        resolution (int): The H3 resolution level
        bucket_count (int): Number of buckets at this resolution
        avg_properties_per_bucket (float): Average number of properties per bucket
        max_properties_in_bucket (int): Maximum properties in any bucket at this resolution
        min_properties_in_bucket (int): Minimum properties in any bucket at this resolution
        total_properties (int): Total number of properties across all buckets at this resolution
    """

    resolution: int = Field(..., description="The H3 resolution level")
    bucket_count: int = Field(..., description="Number of buckets at this resolution")
    avg_properties_per_bucket: float = Field(..., description="Average number of properties per bucket")
    max_properties_in_bucket: int = Field(..., description="Maximum properties in any bucket at this resolution")
    min_properties_in_bucket: int = Field(..., description="Minimum properties in any bucket at this resolution")
    total_properties: int = Field(..., description="Total number of properties across all buckets at this resolution")


class GeoBucketCoverage(BaseModel):
    """
    Schema for GeoBucket coverage metrics.

    Attributes:
        total_area_km2 (float | None): Total area covered by geo buckets in square kilometers
        bounding_box (dict[str, float] | None): Bounding box with min_lat, max_lat, min_lng, max_lng
        unique_locations (int): Number of unique location names covered
        avg_bucket_density (float): Average bucket density (properties per km2)
    """

    total_area_km2: float | None = Field(
        default=None, description="Total area covered by geo buckets in square kilometers"
    )
    bounding_box: dict[str, float] | None = Field(
        default=None, description="Bounding box with min_lat, max_lat, min_lng, max_lng"
    )
    unique_locations: int = Field(default=0, description="Number of unique location names covered")
    avg_bucket_density: float = Field(..., description="Average bucket density (properties per km2)")


class GeoBucketStats(BaseModel):
    """
    Schema for GeoBucket statistics and coverage metrics.

    Attributes:
        total_buckets (int): Total number of geo buckets.
        total_properties (int): Total number of properties across all buckets.
        top_buckets (list[GeoBucketDistribution]): Top 10 buckets by property count.
        resolution_stats (list[GeoBucketResolutions]): Statistics per H3 resolution.
        coverage (GeoBucketCoverage): Coverage metrics for geo buckets.
        empty_buckets (int): Number of buckets with no properties.
    """

    total_buckets: int = Field(..., description="Total number of geo buckets")
    total_properties: int = Field(..., description="Total number of properties across all buckets")
    top_buckets: list[GeoBucketDistribution] = Field(
        default_factory=list, description="Top 10 buckets by property count"
    )
    empty_buckets: int = Field(..., description="Number of buckets with no properties")
    coverage: GeoBucketCoverage = Field(..., description="Coverage metrics for geo buckets")
    resolution_stats: list[GeoBucketResolutions] = Field(
        default_factory=list, description="Statistics per H3 resolution"
    )
