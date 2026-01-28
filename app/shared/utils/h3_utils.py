from dataclasses import dataclass
from typing import Any, Set, Tuple

import h3
from geoalchemy2.shape import from_shape, to_shape
from pydantic_extra_types.coordinate import Latitude, Longitude
from shapely.geometry import Point, Polygon
from shared.constants.property import PROPERTY_EDGE_SPECS


@dataclass
class H3Indexes:
    """
    Data class to hold H3 indexes at different resolutions.
    """

    h3_r7: int
    h3_r8: int
    h3_r9: int


class H3Utils:
    """
    Utility class for H3-related operations.
    """

    @staticmethod
    def _to_int(h3_value: int | str) -> int:
        """
        Convert H3 value to integer, handling both int and hex string formats.

        Args:
            h3_value: H3 index as either int or hex string

        Returns:
            int: H3 index as integer
        """
        if isinstance(h3_value, int):
            return h3_value
        return int(h3_value, 16)

    @staticmethod
    def calculate_h3_indexes(lat: Latitude | float, lng: Longitude | float) -> H3Indexes:
        """
        Calculate H3 indexes at multiple resolutions for a given lat/lng

        Args:
            lat (Latitude | float): Latitude (pydantic type or float)
            lng (Longitude | float): Longitude (pydantic type or float)

        Returns:
            H3Indexes: An instance of H3Indexes with h3_r7, h3_r8, h3_r9 as integers
        """
        lat_val = float(lat)
        lng_val = float(lng)

        h3_r7 = H3Utils._to_int(h3.latlng_to_cell(lat_val, lng_val, 7))
        h3_r8 = H3Utils._to_int(h3.latlng_to_cell(lat_val, lng_val, 8))
        h3_r9 = H3Utils._to_int(h3.latlng_to_cell(lat_val, lng_val, 9))

        return H3Indexes(h3_r7=h3_r7, h3_r8=h3_r8, h3_r9=h3_r9)

    @staticmethod
    def create_point_geometry(lat: Latitude | float, lng: Longitude | float) -> Any:
        """
        Create PostGIS Point geometry from coordinates

        Args:
            lat (Latitude | float): Latitude
            lng (Longitude | float): Longitude

        Returns:
            WKBElement: GeoAlchemy2 WKT element
        """

        lat_val = float(lat)
        lng_val = float(lng)

        point = Point(lng_val, lat_val)
        return from_shape(point, srid=4326)

    @staticmethod
    def extract_lat_lng_from_geometry(geometry: Any) -> Tuple[float, float]:
        """
        Extract lat/lng from PostGIS geometry

        Args:
            geometry (Any): GeoAlchemy2 geometry object

        Returns:
            Tuple of (lat, lng)
        """
        shape = to_shape(geometry)  # type: ignore[arg-type]
        return shape.y, shape.x  # type: ignore[attr-defined]

    @staticmethod
    def h3_to_geometry(h3_index: int) -> Tuple[Any, Any]:
        """
        Convert H3 index to PostGIS-compatible geometries

        Args:
            h3_index (int): H3 cell index as integer

        Returns:
            Tuple[WKBElement, WKBElement]: Tuple of (center_point_wkt, hexagon_boundary_wkt)
        """
        h3_str = h3.int_to_str(h3_index)
        lat, lng = h3.cell_to_latlng(h3_str)
        center_point = Point(lng, lat)

        boundary_coords = h3.cell_to_boundary(h3_str)
        polygon_coords = [(lng, lat) for lat, lng in boundary_coords]
        hexagon_polygon = Polygon(polygon_coords)

        center_wkt = from_shape(center_point, srid=4326)
        hexagon_wkt = from_shape(hexagon_polygon, srid=4326)

        return center_wkt, hexagon_wkt

    @staticmethod
    def get_parent_h3(h3_index: int, parent_resolution: int = 7) -> int:
        h3_str = h3.int_to_str(h3_index)
        parent_str = h3.cell_to_parent(h3_str, parent_resolution)
        return H3Utils._to_int(parent_str)

    @staticmethod
    def get_neighbor_h3s(h3_index: int, k: int = 1) -> Set[int]:
        """
        Get neighboring H3 cells within k-ring distance

        Args:
            h3_index: Center H3 cell
            k: Ring distance (1 = immediate neighbors, 2 = 2 rings, etc.)

        Returns:
            Set[int]: Set of H3 indexes including center
        """
        h3_str = h3.int_to_str(h3_index)
        neighbors = h3.grid_disk(h3_str, k)
        return {H3Utils._to_int(cell) for cell in neighbors}

    @staticmethod
    def get_h3_ring_for_radius(radius_km: float, resolution: int = 8) -> int:
        """
        Calculate k-ring size needed for given radius

        Args:
            radius_km (float): Desired search radius in kilometers
            resolution (int): H3 resolution level

        Returns:
            int: k value for grid_disk
        """

        edge_length_km = PROPERTY_EDGE_SPECS.get(resolution, PROPERTY_EDGE_SPECS[8])
        k = max(1, int(radius_km / (edge_length_km * 2)))
        return min(k, 5)

    @staticmethod
    def get_lat_lng_from_h3(h3_index: int | str) -> Tuple[float, float]:
        if isinstance(h3_index, str):
            h3_index = H3Utils._to_int(h3_index)
            return h3.cell_to_latlng(h3_index)
        else:
            h3_str = h3.int_to_str(h3_index)
            return h3.cell_to_latlng(h3_str)

    @staticmethod
    def h3_to_string(h3_index: int) -> str:
        return h3.int_to_str(h3_index)

    @staticmethod
    def string_to_h3(h3_string: str) -> int:
        return H3Utils._to_int(h3.str_to_int(h3_string))

    @staticmethod
    def validate_coordinates_in_bounds(
        lat: Latitude | float,
        lng: Longitude | float,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
    ) -> bool:
        lat_val = float(lat)
        lng_val = float(lng)

        return min_lat <= lat_val <= max_lat and min_lng <= lng_val <= max_lng
