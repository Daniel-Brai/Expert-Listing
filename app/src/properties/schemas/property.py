from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, Field, StringConstraints
from pydantic_extra_types.coordinate import Latitude, Longitude
from shared.utils import optional

if TYPE_CHECKING:
    from shared.utils.h3_utils import H3Utils
    from src.properties.models.property import Property


class PropertyCreate(BaseModel):
    """
    Schema for creating a property

    Attributes:
        title (str): Title of the property listing
        location_name (str): Name of the property's location
        location_name_normalized (str): Normalized name of the property's location for fuzzy matching
        coordinates (str | None): Geographical coordinates of the property in WKT format
        h3_index_r8 (int): H3 index at resolution 8 (~461m)
        h3_index_r9 (int): H3 index at resolution 9 (~174m)
        attributes (dict[str, Any] | None): Additional attributes of the property
        geo_bucket_id (int | None): Foreign key referencing the associated geo bucket
    """

    title: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ..., min_length=1, max_length=2000, description="Title of the property listing"
    )
    location_name: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Name of the property's location",
    )
    location_name_normalized: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Normalized name of the property's location for fuzzy matching",
    )
    coordinates: str | None = Field(
        default=None,
        description="Geographical coordinates of the property in WKT format",
    )
    h3_index_r8: int = Field(..., description="H3 index at resolution 8 (~461m)")
    h3_index_r9: int = Field(..., description="H3 index at resolution 9 (~174m)")
    attributes: dict[str, Any] | None = Field(default=None, description="Additional attributes of the property")
    geo_bucket_id: int | None = Field(default=None, description="Foreign key referencing the associated geo bucket")


@optional
class PropertyUpdate(PropertyCreate):
    """
    Schema for updating a property
    """

    pass


class PropertyCreateRequest(BaseModel):
    """
    Schema for creating a property

    Attributes:
        title (str): Title of the property listing
        location_name (str): Name of the property's location
        lat (Latitude): Latitude of the property's location
        lng (Longitude): Longitude of the property's location
        attributes (dict[str, Any] | None): Additional attributes of the property
    """

    title: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ..., min_length=1, max_length=2000, description="Title of the property listing"
    )
    location_name: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Name of the property's location",
    )
    lat: Latitude = Field(..., description="Latitude of the property's location")
    lng: Longitude = Field(..., description="Longitude of the property's location")
    attributes: dict[str, Any] | None = Field(default=None, description="Additional attributes of the property")


class PropertyQueryParams(BaseModel):
    """
    Query parameters for filtering property listings

    Attributes:
        location (str | None): Filter by location name
    """

    location: Annotated[str, StringConstraints(strip_whitespace=True)] | None = Field(
        default=None, description="Filter by location name"
    )


class PropertyRead(BaseModel):
    """
    Schema for reading a property in its basic form

    Attributes:
        id (str): Unique identifier for the property
        title (str): Title of the property listing
        location_name (str): Name of the property's location
        latitude (Latitude): Latitude of the property's location
        longitude (Longitude): Longitude of the property's location
        attributes (dict[str, Any] | None): Additional attributes of the property
        created_datetime (str): Timestamp when the property was created
        updated_datetime (str | None): Timestamp when the property was last updated
    """

    id: str = Field(..., description="Unique identifier for the property")
    title: str = Field(..., description="Title of the property listing")
    location_name: str = Field(..., description="Name of the property's location")
    latitude: Latitude = Field(..., description="Latitude of the property's location")
    longitude: Longitude = Field(..., description="Longitude of the property's location")
    attributes: dict[str, Any] | None = Field(default=None, description="Additional attributes of the property")
    created_datetime: str = Field(..., description="Timestamp when the property was created")
    updated_datetime: str | None = Field(default=None, description="Timestamp when the property was last updated")

    @classmethod
    def from_values(cls, model: "Property", h3: "H3Utils") -> "PropertyRead":
        """
        Converts a Property model instance to a PropertyRead schema instance.

        Args:
            model (Property): The Property model instance.
            h3 (H3Utils): An instance of H3Utils for coordinate extraction.

        Returns:
            PropertyRead: The corresponding PropertyRead schema instance.
        """

        try:
            lat, lng = h3.extract_lat_lng_from_geometry(model.coordinates)
        except Exception:
            lat = lng = None

        if not (isinstance(lat, float) and isinstance(lng, float) and -90 <= lat <= 90 and -180 <= lng <= 180):
            try:
                h3_index = getattr(model, "h3_index_r9", None) or getattr(model, "h3_index_r8", None)
                if h3_index is not None:
                    lat, lng = h3.get_lat_lng_from_h3(h3_index)
            except Exception:
                raise ValueError("Failed to determine valid latitude/longitude for property")

        if lat is None or lng is None:
            raise ValueError("Failed to determine valid latitude/longitude for property")

        return PropertyRead(
            id=str(model.id),
            title=model.title,
            location_name=model.location_name,
            latitude=Latitude(lat),
            longitude=Longitude(lng),
            attributes=model.attributes,
            created_datetime=model.created_datetime.isoformat(),
            updated_datetime=(model.updated_datetime.isoformat() if model.updated_datetime else None),
        )
