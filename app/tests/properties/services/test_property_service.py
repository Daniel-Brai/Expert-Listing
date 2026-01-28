from unittest.mock import patch

from core.pagination import CursorParams
from pydantic_extra_types.coordinate import Latitude, Longitude
from shared.exceptions import AppException, DatabaseException
from shared.utils import H3Utils, LocationUtils
from src.properties.schemas.property import PropertyCreateRequest, PropertyQueryParams
from src.properties.services.property_service import PropertyService
from tests.geo_buckets.factory import GeoBucketFactory
from tests.properties.factory import PropertyFactory
from tests.testutils import AsyncCustomDBTestCase


class CreatePropertyTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.h3_utils = H3Utils()
        self.location_utils = LocationUtils()

        self.lat = 6.5244
        self.lng = 3.3792
        self.location_name = "Lagos"

        self.geo_bucket = GeoBucketFactory.create(
            canonical_name=self.location_name,
            canonical_name_normalized=self.location_utils.normalize(self.location_name),
        )

    async def test_create_property__successful(self):
        """Test successful property creation."""
        payload = PropertyCreateRequest(
            title="Beautiful 3-bedroom apartment",
            location_name=self.location_name,
            lat=Latitude(self.lat),
            lng=Longitude(self.lng),
            attributes={
                "price": 150000,
                "bedrooms": 3,
                "bathrooms": 2,
            },
        )

        service = PropertyService(session=self.async_db_session)
        property_read = await service.create_property(payload=payload)

        self.assertIsNotNone(property_read)
        self.assertEqual(property_read.title, payload.title)
        self.assertEqual(property_read.location_name, payload.location_name)
        self.assertIsNotNone(property_read.id)

    async def test_create_property__creates_new_bucket(self):
        new_location = "Abuja"
        new_lat = 9.0765
        new_lng = 7.3986

        payload = PropertyCreateRequest(
            title="Modern office space",
            location_name=new_location,
            lat=Latitude(new_lat),
            lng=Longitude(new_lng),
            attributes={"price": 500000, "area_sqm": 200},
        )

        service = PropertyService(session=self.async_db_session)
        property_read = await service.create_property(payload=payload)

        self.assertIsNotNone(property_read)
        self.assertEqual(property_read.location_name, new_location)

    async def test_create_property__database_exception(self):
        payload = PropertyCreateRequest(
            title="Test property",
            location_name=self.location_name,
            lat=Latitude(self.lat),
            lng=Longitude(self.lng),
            attributes={},
        )

        service = PropertyService(session=self.async_db_session)

        with patch.object(
            service.property_repository,
            "create",
            side_effect=DatabaseException("Database error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.create_property(payload=payload)

            self.assertIn("Failed to create property listing", str(context.exception))

    async def test_create_property__unexpected_exception(self):
        payload = PropertyCreateRequest(
            title="Test property",
            location_name=self.location_name,
            lat=Latitude(self.lat),
            lng=Longitude(self.lng),
            attributes={},
        )

        service = PropertyService(session=self.async_db_session)

        with patch.object(
            service.h3_utils,
            "calculate_h3_indexes",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.create_property(payload=payload)

            self.assertIn("unexpected error", str(context.exception).lower())


class CreatePropertyIfNotExistsTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.h3_utils = H3Utils()
        self.location_utils = LocationUtils()

        self.lat = 6.5244
        self.lng = 3.3792
        self.location_name = "Lagos"

        self.geo_bucket = GeoBucketFactory.create(
            canonical_name=self.location_name,
            canonical_name_normalized=self.location_utils.normalize(self.location_name),
        )

    async def test_create_property_if_not_exists__new_property(self):
        """Test creating a property when it doesn't exist."""
        payload = PropertyCreateRequest(
            title="Unique property listing",
            location_name=self.location_name,
            lat=Latitude(self.lat),
            lng=Longitude(self.lng),
            attributes={"price": 200000},
        )

        service = PropertyService(session=self.async_db_session)
        property_read = await service.create_property_if_not_exists(payload=payload)

        self.assertIsNotNone(property_read)
        self.assertEqual(property_read.title, payload.title)

    async def test_create_property_if_not_exists__existing_property(self):
        """Test that existing property is returned without creating duplicate."""
        existing_property = PropertyFactory.create(
            title="Existing property",
            geo_bucket=self.geo_bucket,
        )

        payload = PropertyCreateRequest(
            title="Existing property",
            location_name=self.location_name,
            lat=Latitude(self.lat),
            lng=Longitude(self.lng),
            attributes={},
        )

        service = PropertyService(session=self.async_db_session)
        property_read = await service.create_property_if_not_exists(payload=payload)

        self.assertEqual(property_read.id, existing_property.id)
        self.assertEqual(property_read.title, existing_property.title)


class ListPropertiesTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.h3_utils = H3Utils()
        self.location_utils = LocationUtils()

        self.geo_bucket = GeoBucketFactory.create()

        # Create test properties
        self.properties = [PropertyFactory.create(geo_bucket=self.geo_bucket) for _ in range(5)]

    async def test_list_properties__successful_without_filters(self):
        pagination = CursorParams(size=10)
        service = PropertyService(session=self.async_db_session)

        data, metadata = await service.list_properties(pagination=pagination, query_params=None)

        self.assertIsNotNone(data)
        self.assertIsNotNone(metadata)
        self.assertEqual(len(data), 5)

    async def test_list_properties__with_pagination(self):
        pagination = CursorParams(size=2)
        service = PropertyService(session=self.async_db_session)

        data, metadata = await service.list_properties(pagination=pagination, query_params=None)

        self.assertEqual(len(data), 2)
        self.assertEqual(metadata.total, 5)
        self.assertIsNotNone(metadata.next_page)

    async def test_list_properties__with_location_filter(self):
        location_name = "Test Location"
        filtered_geo_bucket = GeoBucketFactory.create(
            canonical_name=location_name,
            canonical_name_normalized=self.location_utils.normalize(location_name),
        )
        filtered_property = PropertyFactory.create(
            location_name=location_name,
            location_name_normalized=self.location_utils.normalize(location_name),
            geo_bucket=filtered_geo_bucket,
        )

        pagination = CursorParams(size=10)
        query_params = PropertyQueryParams(location=location_name)
        service = PropertyService(session=self.async_db_session)

        data, metadata = await service.list_properties(pagination=pagination, query_params=query_params)

        self.assertGreaterEqual(len(data), 1)
        property_ids = [prop.id for prop in data]
        self.assertIn(filtered_property.id, property_ids)

    async def test_list_properties__database_exception(self):

        pagination = CursorParams(size=10)
        service = PropertyService(session=self.async_db_session)

        with patch.object(
            service.property_repository,
            "paginate",
            side_effect=DatabaseException("Database error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.list_properties(pagination=pagination, query_params=None)

            self.assertIn("Failed to retrieve property listings", str(context.exception))

    async def test_list_properties__unexpected_exception(self):
        pagination = CursorParams(size=10)
        service = PropertyService(session=self.async_db_session)

        with patch.object(
            service.property_repository,
            "paginate",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.list_properties(pagination=pagination, query_params=None)

            self.assertIn("unexpected error occurred", str(context.exception))

    async def test_list_properties__cursor_pagination(self):
        pagination = CursorParams(size=2)
        service = PropertyService(session=self.async_db_session)

        first_page, first_metadata = await service.list_properties(pagination=pagination, query_params=None)

        self.assertEqual(len(first_page), 2)
        self.assertIsNotNone(first_metadata.next_page)

        second_pagination = CursorParams(size=2, cursor=first_metadata.next_page)
        second_page, _ = await service.list_properties(pagination=second_pagination, query_params=None)

        self.assertEqual(len(second_page), 2)
        first_ids = {prop.id for prop in first_page}
        second_ids = {prop.id for prop in second_page}
        self.assertEqual(len(first_ids.intersection(second_ids)), 0)
