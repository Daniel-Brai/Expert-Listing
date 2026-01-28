from core.logging import get_logger
from core.pagination import CursorPaginationMetadata, CursorParams
from database import transactional
from fastapi.exceptions import RequestValidationError
from shared.exceptions import AppException, DatabaseException
from shared.utils import H3Utils, LocationUtils
from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.geo_buckets.services.geo_bucket_service import GeoBucketService
from src.properties.models.property import Property
from src.properties.repositories.property_repository import PropertyRepository
from src.properties.schemas.property import PropertyCreateRequest, PropertyQueryParams, PropertyRead

logger = get_logger(__name__)


class PropertyService:
    """
    Service for managing properties.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.property_repository = PropertyRepository(session=self.session)
        self.geo_bucket_service = GeoBucketService(session=self.session)
        self.h3_utils = H3Utils()
        self.location_utils = LocationUtils()

    @transactional
    async def create_property(self, *, payload: PropertyCreateRequest):
        """
        Create a new property and associate it with the appropriate geo-bucket.

        Args:
            payload (PropertyCreateRequest): The property creation request data.

        Returns:
            PropertyRead: The created property data.
        """
        try:
            h3_indexes = self.h3_utils.calculate_h3_indexes(payload.lat, payload.lng)

            normalized_name = self.location_utils.normalize(payload.location_name)

            point_wkt = self.h3_utils.create_point_geometry(payload.lat, payload.lng)

            bucket = await self.geo_bucket_service.find_or_create_bucket(
                h3_index_r8=h3_indexes.h3_r8,
                location_name=payload.location_name,
                normalized_name=normalized_name,
                parent_h3=h3_indexes.h3_r7,
            )

            property = await self.property_repository.create(
                schema={
                    "title": payload.title,
                    "location_name": payload.location_name,
                    "location_name_normalized": normalized_name,
                    "coordinates": point_wkt,
                    "h3_index_r8": h3_indexes.h3_r8,
                    "h3_index_r9": h3_indexes.h3_r9,
                    "geo_bucket_id": bucket.id,
                    "attributes": payload.attributes,
                }
            )

            await self.geo_bucket_service.increment_property_count(geo_bucket_id=bucket.id)

            return PropertyRead.from_values(model=property, h3=self.h3_utils)
        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `create_property`: {str(db_exc)}")
            raise AppException(message="Failed to create property listing.") from db_exc
        except (AppException, RequestValidationError):
            raise
        except Exception as exc:
            logger.error(f"Exception in `create_property`: {str(exc)}")
            raise AppException(message="An unexpected error occurred while creating the property listing.") from exc

    @transactional
    async def create_property_if_not_exists(self, *, payload: PropertyCreateRequest):
        """
        Create a new property and associate it with the appropriate geo-bucket.

        Args:
            payload (PropertyCreateRequest): The property creation request data.

        Returns:
            PropertyRead: The created property data.
        """
        try:
            existing_property = await self.property_repository.find_one_by_and_none(title=payload.title)

            if existing_property:
                return PropertyRead.from_values(model=existing_property, h3=self.h3_utils)

            h3_indexes = self.h3_utils.calculate_h3_indexes(payload.lat, payload.lng)

            normalized_name = self.location_utils.normalize(payload.location_name)

            point_wkt = self.h3_utils.create_point_geometry(payload.lat, payload.lng)

            bucket = await self.geo_bucket_service.find_or_create_bucket(
                h3_index_r8=h3_indexes.h3_r8,
                location_name=payload.location_name,
                normalized_name=normalized_name,
                parent_h3=h3_indexes.h3_r7,
            )

            property = await self.property_repository.create(
                schema={
                    "title": payload.title,
                    "location_name": payload.location_name,
                    "location_name_normalized": normalized_name,
                    "coordinates": point_wkt,
                    "h3_index_r8": h3_indexes.h3_r8,
                    "h3_index_r9": h3_indexes.h3_r9,
                    "geo_bucket_id": bucket.id,
                    "attributes": payload.attributes,
                },
            )

            await self.geo_bucket_service.increment_property_count(geo_bucket_id=bucket.id)

            return PropertyRead.from_values(model=property, h3=self.h3_utils)
        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `create_property`: {str(db_exc)}")
            raise AppException(message="Failed to create property listing.") from db_exc
        except (AppException, RequestValidationError):
            raise
        except Exception as exc:
            logger.error(f"Exception in `create_property`: {str(exc)}")
            raise AppException(message="An unexpected error occurred while creating the property listing.") from exc

    async def list_properties(
        self, *, pagination: CursorParams, query_params: PropertyQueryParams | None
    ) -> tuple[list[PropertyRead], CursorPaginationMetadata]:
        """
        List properties with pagination and optional filtering.

        Args:
            pagination (CursorParams): Pagination parameters.
            query_params (PropertyQueryParams | None): Optional filtering parameters.

        Returns:
            tuple[list[PropertyRead], CursorPaginationMetadata]: List of properties and pagination metadata.
        """

        try:

            base_query = select(Property)
            count_query = select(func.count()).select_from(Property)
            transformer = lambda properties: [
                PropertyRead.from_values(model=prop, h3=self.h3_utils) for prop in properties
            ]

            if query_params is not None and query_params.location is not None:
                bucket_ids = set()

                normalized_location = self.location_utils.normalize(query_params.location)

                fuzzy_buckets = await self.geo_bucket_service.get_fuzzy_buckets(
                    normalized_location=normalized_location, limit=50
                )

                bucket_ids.update(b.id for b in fuzzy_buckets)

                if not bucket_ids:
                    return [], CursorPaginationMetadata(
                        total=0,
                        previous_page=None,
                        next_page=None,
                        current_page=None,
                        current_page_backwards=None,
                    )

                base_query = base_query.where(col(Property.geo_bucket_id).in_(bucket_ids))

                count_query = count_query.where(col(Property.geo_bucket_id).in_(bucket_ids))

            base_query = base_query.order_by(col(Property.id).desc())

            paginated_result = await self.property_repository.paginate(
                query=base_query,
                count_query=count_query,
                filters=None,
                cursor_params=pagination,
                transformer=transformer,
                page_schema=PropertyRead,
            )

            data = [PropertyRead.model_validate(prop, from_attributes=True) for prop in paginated_result.items]

            metadata = CursorPaginationMetadata.model_validate(paginated_result, from_attributes=True)

            return data, metadata
        except DatabaseException as db_exc:
            logger.error(f"DatabaseException in `list_properties`: {str(db_exc)}")
            raise AppException(message="Failed to retrieve property listings.") from db_exc
        except (AppException, RequestValidationError):
            raise
        except Exception as exc:
            logger.error(f"Exception in `list_properties`: {str(exc)}")
            raise AppException(message="An unexpected error occurred while retrieving property listings.") from exc
