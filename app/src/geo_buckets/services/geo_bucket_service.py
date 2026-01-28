import h3
from core.logging import get_logger
from geoalchemy2 import Geography
from shared.exceptions import AppException, DatabaseException
from shared.utils import H3Utils
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.geo_buckets.models.geo_bucket import GeoBucket
from src.geo_buckets.repositories.geo_bucket_repository import GeoBucketRepository
from src.geo_buckets.schemas.geo_bucket import (
    GeoBucketCoverage,
    GeoBucketDistribution,
    GeoBucketRead,
    GeoBucketResolutions,
    GeoBucketStats,
)
from src.properties.models.property import Property

logger = get_logger(__name__)


class GeoBucketService:
    """
    Service class for GeoBucket-related operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.geo_bucket_repository = GeoBucketRepository(session=self.session)
        self.h3_utils = H3Utils()

    async def find_or_create_bucket(
        self,
        *,
        h3_index_r8: int,
        location_name: str,
        normalized_name: str,
        parent_h3: int,
    ) -> GeoBucketRead:
        """
        Find an existing GeoBucket by H3 index or create a new one.

        Args:
            h3_index_r8 (int): H3 index at resolution 8.
            location_name (str): Human readable name for the location.
            normalized_name (str): Normalized name for fuzzy matching.
            parent_h3 (int): Parent H3 index.

        Returns:
            GeoBucketRead: The found or newly created GeoBucket.
        """

        try:
            bucket = await self.geo_bucket_repository.find_one_by_and_none(
                h3_index=h3_index_r8,
            )

            if bucket:
                return GeoBucketRead.from_model(bucket)

            neighbors = list(self.h3_utils.get_neighbor_h3s(h3_index_r8, k=1))

            bucket_query = await self.geo_bucket_repository.execute_raw(
                select(GeoBucket).where(
                    col(GeoBucket.h3_index).in_(neighbors),
                    func.similarity(GeoBucket.canonical_name_normalized, normalized_name) > 0.7,
                )
            )

            bucket = bucket_query.first()

            if bucket:
                return GeoBucketRead.from_model(bucket)

            center_wkt, hexagon_wkt = self.h3_utils.h3_to_geometry(h3_index_r8)

            bucket = await self.geo_bucket_repository.create(
                schema={
                    "h3_index": h3_index_r8,
                    "h3_resolution": 8,
                    "canonical_name": location_name,
                    "canonical_name_normalized": normalized_name,
                    "center_point": center_wkt,
                    "hexagon_boundary": hexagon_wkt,
                    "parent_h3": parent_h3,
                    "property_count": 0,
                }
            )

            return GeoBucketRead.from_model(bucket)
        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `find_or_create_bucket`: {str(db_exc)}")
            raise AppException(
                message="Failed to find or create geo bucket",
            ) from db_exc
        except Exception as exc:
            logger.error(f"Exception in `find_or_create_bucket`: {str(exc)}")
            raise AppException(
                message="An unexpected error occurred while trying find the geobucket.",
            ) from exc

    async def increment_property_count(self, geo_bucket_id: int) -> None:
        """
        Increment the property count for a given GeoBucket.

        Args:
            geo_bucket_id (int): The ID of the GeoBucket to update.
        """
        try:
            geo_bucket = await self.geo_bucket_repository.find_one_by_and_none(id=geo_bucket_id)

            if not geo_bucket:
                raise AppException(message="GeoBucket not found for incrementing property count.")

            geo_bucket.property_count += 1

            self.session.add(geo_bucket)

            await self.geo_bucket_repository.save_changes(geo_bucket)

        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `increment_property_count`: {str(db_exc)}")
            raise AppException(
                message="Failed to increment property count",
            ) from db_exc
        except Exception as exc:
            logger.error(f"Exception in `increment_property_count`: {str(exc)}")
            raise AppException(
                message="An unexpected error occurred while incrementing the property count.",
            ) from exc

    async def get_fuzzy_buckets(self, *, normalized_location: str, limit: int = 10) -> list[GeoBucketRead]:
        """
        Retrieve GeoBuckets that fuzzy match the given normalized name.

        Args:
            normalized_name (str): The normalized name to match against.
            limit (int): Maximum number of results to return.

        Returns:
            list[GeoBucketRead]: List of matching GeoBuckets.
        """
        try:
            buckets_query = await self.geo_bucket_repository.execute_raw(
                select(GeoBucket)
                .where(func.similarity(GeoBucket.canonical_name_normalized, normalized_location) > 0.3)
                .order_by(func.similarity(GeoBucket.canonical_name_normalized, normalized_location).desc())
                .limit(limit)
            )

            buckets = buckets_query.all()

            return [GeoBucketRead.from_model(bucket) for bucket in buckets]

        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `get_fuzzy_buckets`: {str(db_exc)}")
            raise AppException(
                message="Failed to retrieve fuzzy buckets",
            ) from db_exc
        except Exception as exc:
            logger.error(f"Exception in `get_fuzzy_buckets`: {str(exc)}")
            raise AppException(
                message="An unexpected error occurred while retrieving fuzzy geo buckets.",
            ) from exc

    async def get_stats(self) -> GeoBucketStats:
        """
        Retrieve statistics about GeoBuckets.

        Returns:
            GeoBucketStats: Statistics about GeoBuckets.
        """
        try:
            total_properties = await self._get_total_properties()

            basic_stats = await self._get_basic_stats()

            top_buckets = await self._get_top_buckets(limit=10)

            coverage = await self._get_coverage_stats(total_properties)

            resolution_stats = await self._get_resolution_stats()

            return GeoBucketStats(
                total_buckets=basic_stats["total_buckets"],
                total_properties=total_properties,
                top_buckets=top_buckets,
                empty_buckets=basic_stats["empty_buckets"],
                coverage=coverage,
                resolution_stats=resolution_stats,
            )

        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `get_stats`: {str(db_exc)}")
            raise AppException(
                message="Failed to retrieve geo bucket stats",
            ) from db_exc
        except Exception as exc:
            logger.error(f"Exception in `get_stats`: {str(exc)}")
            raise AppException(
                message="An unexpected error occurred while retrieving geo bucket statistics.",
            ) from exc

    async def _get_basic_stats(self) -> dict[str, int]:
        total_buckets_query = await self.geo_bucket_repository.execute_raw(select(func.count(col(GeoBucket.id))))

        total_buckets = total_buckets_query.one() or 0

        empty_buckets_query = await self.geo_bucket_repository.execute_raw(
            select(func.count(col(GeoBucket.id))).where(GeoBucket.property_count == 0)
        )

        empty_buckets = empty_buckets_query.one() or 0

        return {
            "total_buckets": total_buckets or 0,
            "empty_buckets": empty_buckets or 0,
        }

    async def _get_top_buckets(self, limit: int = 10) -> list[GeoBucketDistribution]:
        buckets_query = await self.geo_bucket_repository.execute_raw(
            select(GeoBucket)
            .where(GeoBucket.property_count > 0)
            .order_by(col(GeoBucket.property_count).desc())
            .limit(limit)
        )

        buckets = buckets_query.all()

        result = []
        for bucket in buckets:
            if bucket.center_point:
                lat, lng = self.h3_utils.extract_lat_lng_from_geometry(bucket.center_point)
            else:
                lat, lng = h3.cell_to_latlng(bucket.h3_index)

            result.append(
                GeoBucketDistribution(
                    bucket_id=bucket.id,
                    h3_index=self.h3_utils.h3_to_string(bucket.h3_index),
                    canonical_name=bucket.canonical_name,
                    property_count=bucket.property_count,
                    center_lat=lat,
                    center_lng=lng,
                )
            )

        return result

    async def _get_coverage_stats(self, total_properties: int) -> GeoBucketCoverage:

        bbox_query = await self.geo_bucket_repository.execute_raw(
            select(
                func.ST_XMin(func.ST_Extent(GeoBucket.center_point)).label("min_lng"),
                func.ST_XMax(func.ST_Extent(GeoBucket.center_point)).label("max_lng"),
                func.ST_YMin(func.ST_Extent(GeoBucket.center_point)).label("min_lat"),
                func.ST_YMax(func.ST_Extent(GeoBucket.center_point)).label("max_lat"),
            )
        )

        bbox = bbox_query.first()

        bounding_box = None
        total_area_km2 = None

        if bbox and all([bbox.min_lat, bbox.max_lat, bbox.min_lng, bbox.max_lng]):
            bounding_box = {
                "min_lat": float(bbox.min_lat),
                "max_lat": float(bbox.max_lat),
                "min_lng": float(bbox.min_lng),
                "max_lng": float(bbox.max_lng),
            }

            total_area_km2 = await self._calculate_bbox_area(
                min_lat=bbox.min_lat,
                max_lat=bbox.max_lat,
                min_lng=bbox.min_lng,
                max_lng=bbox.max_lng,
            )

        unique_locations_query = await self.geo_bucket_repository.execute_raw(
            select(func.count(func.distinct(GeoBucket.canonical_name_normalized)))
        )

        unique_locations = unique_locations_query.one() or 0

        avg_density = (total_properties / total_area_km2) if total_area_km2 and total_area_km2 > 0 else 0.0

        return GeoBucketCoverage(
            total_area_km2=total_area_km2,
            bounding_box=bounding_box,
            unique_locations=unique_locations,
            avg_bucket_density=avg_density,
        )

    async def _get_resolution_stats(self) -> list[GeoBucketResolutions]:

        stats_query = await self.geo_bucket_repository.execute_raw(
            query=(
                select(  # type: ignore
                    col(GeoBucket.h3_resolution),
                    func.count(col(GeoBucket.id)).label("bucket_count"),
                    func.avg(col(GeoBucket.property_count)).label("avg_properties"),
                    func.max(col(GeoBucket.property_count)).label("max_properties"),
                    func.min(col(GeoBucket.property_count)).label("min_properties"),
                    func.sum(col(GeoBucket.property_count)).label("total_properties"),
                )
                .group_by(col(GeoBucket.h3_resolution))
                .order_by(col(GeoBucket.h3_resolution))
            )
        )

        stats = stats_query.all()

        result = []
        for row in stats:
            result.append(
                GeoBucketResolutions(
                    resolution=row.h3_resolution,
                    bucket_count=row.bucket_count,
                    avg_properties_per_bucket=float(row.avg_properties or 0),
                    max_properties_in_bucket=row.max_properties or 0,
                    min_properties_in_bucket=row.min_properties or 0,
                    total_properties=row.total_properties or 0,
                )
            )

        return result

    async def _get_total_properties(self) -> int:
        total_props_query = await self.session.exec(select(func.count(col(Property.id))))
        total_props = total_props_query.one() or 0
        return total_props

    async def _calculate_bbox_area(self, *, min_lat: float, max_lat: float, min_lng: float, max_lng: float) -> float:

        area_query = await self.session.exec(
            select(
                func.ST_Area(func.ST_MakeEnvelope(min_lng, min_lat, max_lng, max_lat, 4326).cast(Geography)).label(
                    "area_m2"
                )
            )
        )

        area = area_query.first()

        if area is not None:
            return float(area) / 1_000_000

        return 0.0
