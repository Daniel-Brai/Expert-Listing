from unittest.mock import patch

from shared.exceptions import AppException, DatabaseException
from shared.utils import H3Utils, LocationUtils
from src.geo_buckets.services.geo_bucket_service import GeoBucketService
from tests.geo_buckets.factory import GeoBucketFactory
from tests.properties.factory import PropertyFactory
from tests.testutils import AsyncCustomDBTestCase


class FindOrCreateBucketTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.h3_utils = H3Utils()
        self.location_utils = LocationUtils()

        self.lat = 6.5244
        self.lng = 3.3792
        self.location_name = "Lagos"
        self.h3_indexes = self.h3_utils.calculate_h3_indexes(self.lat, self.lng)
        self.normalized_name = self.location_utils.normalize(self.location_name)

    async def test_find_or_create_bucket__find_existing(self):
        existing_bucket = GeoBucketFactory.create(
            h3_index=self.h3_indexes.h3_r8,
            canonical_name=self.location_name,
            canonical_name_normalized=self.normalized_name,
            parent_h3=self.h3_indexes.h3_r7,
        )

        service = GeoBucketService(session=self.async_db_session)
        bucket = await service.find_or_create_bucket(
            h3_index_r8=self.h3_indexes.h3_r8,
            location_name=self.location_name,
            normalized_name=self.normalized_name,
            parent_h3=self.h3_indexes.h3_r7,
        )

        self.assertEqual(bucket.id, existing_bucket.id)
        self.assertEqual(bucket.h3_index, self.h3_indexes.h3_r8)
        self.assertEqual(bucket.canonical_name, self.location_name)

    async def test_find_or_create_bucket__create_new(self):
        service = GeoBucketService(session=self.async_db_session)
        bucket = await service.find_or_create_bucket(
            h3_index_r8=self.h3_indexes.h3_r8,
            location_name=self.location_name,
            normalized_name=self.normalized_name,
            parent_h3=self.h3_indexes.h3_r7,
        )

        self.assertIsNotNone(bucket)
        self.assertIsNotNone(bucket.id)
        self.assertEqual(bucket.h3_index, self.h3_indexes.h3_r8)
        self.assertEqual(bucket.canonical_name, self.location_name)
        self.assertEqual(bucket.canonical_name_normalized, self.normalized_name)
        self.assertEqual(bucket.parent_h3, self.h3_indexes.h3_r7)

    async def test_find_or_create_bucket__database_exception(self):
        service = GeoBucketService(session=self.async_db_session)

        with patch.object(
            service.geo_bucket_repository,
            "find_one_by_and_none",
            side_effect=DatabaseException("Database error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.find_or_create_bucket(
                    h3_index_r8=self.h3_indexes.h3_r8,
                    location_name=self.location_name,
                    normalized_name=self.normalized_name,
                    parent_h3=self.h3_indexes.h3_r7,
                )

            self.assertIn("Failed to find or create geo bucket", str(context.exception))

    async def test_find_or_create_bucket__unexpected_exception(self):
        service = GeoBucketService(session=self.async_db_session)

        with patch.object(
            service.h3_utils,
            "h3_to_geometry",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.find_or_create_bucket(
                    h3_index_r8=self.h3_indexes.h3_r8,
                    location_name=self.location_name,
                    normalized_name=self.normalized_name,
                    parent_h3=self.h3_indexes.h3_r7,
                )

            self.assertIn("unexpected error occurred", str(context.exception))


class IncrementPropertyCountTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.geo_bucket = GeoBucketFactory.create(property_count=5)

    async def test_increment_property_count__successful(self):
        initial_count = self.geo_bucket.property_count

        service = GeoBucketService(session=self.async_db_session)
        await service.increment_property_count(geo_bucket_id=self.geo_bucket.id)

        self.geo_bucket = await self.async_db_session.merge(self.geo_bucket)
        await self.async_db_session.refresh(self.geo_bucket)
        self.assertEqual(self.geo_bucket.property_count, initial_count + 1)

    async def test_increment_property_count__multiple_increments(self):
        initial_count = self.geo_bucket.property_count

        service = GeoBucketService(session=self.async_db_session)

        for _ in range(3):
            await service.increment_property_count(geo_bucket_id=self.geo_bucket.id)

        self.geo_bucket = await self.async_db_session.merge(self.geo_bucket)
        await self.async_db_session.refresh(self.geo_bucket)
        self.assertEqual(self.geo_bucket.property_count, initial_count + 3)

    async def test_increment_property_count__unexpected_exception(self):
        service = GeoBucketService(session=self.async_db_session)

        with patch.object(
            self.async_db_session,
            "commit",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.increment_property_count(geo_bucket_id=self.geo_bucket.id)

            self.assertIn("unexpected error occurred", str(context.exception))


class GetFuzzyBucketsTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.location_utils = LocationUtils()

        self.lagos_bucket = GeoBucketFactory.create(
            canonical_name="Lagos",
            canonical_name_normalized=self.location_utils.normalize("Lagos"),
        )
        self.lagos_island_bucket = GeoBucketFactory.create(
            canonical_name="Lagos Island",
            canonical_name_normalized=self.location_utils.normalize("Lagos Island"),
        )
        self.lekki_bucket = GeoBucketFactory.create(
            canonical_name="Lekki",
            canonical_name_normalized=self.location_utils.normalize("Lekki"),
        )

    async def test_get_fuzzy_buckets__successful(self):
        service = GeoBucketService(session=self.async_db_session)
        normalized_location = self.location_utils.normalize("Lagos")

        buckets = await service.get_fuzzy_buckets(normalized_location=normalized_location, limit=10)

        self.assertIsNotNone(buckets)
        self.assertGreater(len(buckets), 0)

        bucket_names = [b.canonical_name for b in buckets]
        self.assertIn("Lagos", bucket_names)

    async def test_get_fuzzy_buckets__with_limit(self):
        service = GeoBucketService(session=self.async_db_session)
        normalized_location = self.location_utils.normalize("Lagos")

        buckets = await service.get_fuzzy_buckets(normalized_location=normalized_location, limit=1)

        self.assertEqual(len(buckets), 1)

    async def test_get_fuzzy_buckets__no_matches(self):
        service = GeoBucketService(session=self.async_db_session)
        normalized_location = self.location_utils.normalize("NonexistentLocation")

        buckets = await service.get_fuzzy_buckets(normalized_location=normalized_location, limit=10)

        self.assertEqual(len(buckets), 0)

    async def test_get_fuzzy_buckets__database_exception(self):
        service = GeoBucketService(session=self.async_db_session)
        normalized_location = self.location_utils.normalize("Lagos")

        with patch.object(
            service.geo_bucket_repository,
            "execute_raw",
            side_effect=DatabaseException("Database error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.get_fuzzy_buckets(normalized_location=normalized_location, limit=10)

            self.assertIn("Failed to retrieve fuzzy buckets", str(context.exception))

    async def test_get_fuzzy_buckets__unexpected_exception(self):
        service = GeoBucketService(session=self.async_db_session)
        normalized_location = self.location_utils.normalize("Lagos")

        with patch.object(
            service.geo_bucket_repository,
            "execute_raw",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.get_fuzzy_buckets(normalized_location=normalized_location, limit=10)

            self.assertIn("unexpected error occurred", str(context.exception))


class GetStatsTests(AsyncCustomDBTestCase):
    def setUp(self):
        super().setUp()

        self.geo_buckets = [GeoBucketFactory.create(property_count=0) for _ in range(3)]

        self.bucket_with_properties = GeoBucketFactory.create(property_count=5)
        PropertyFactory.create_batch(5, geo_bucket=self.bucket_with_properties)

    async def test_get_stats__successful(self):
        service = GeoBucketService(session=self.async_db_session)
        stats = await service.get_stats()

        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.total_buckets, 4)
        self.assertGreaterEqual(stats.empty_buckets, 3)
        self.assertIsNotNone(stats.top_buckets)
        self.assertIsNotNone(stats.coverage)
        self.assertIsNotNone(stats.resolution_stats)

    async def test_get_stats__top_buckets_ordered(self):
        bucket_10 = GeoBucketFactory.create(property_count=10)
        PropertyFactory.create_batch(10, geo_bucket=bucket_10)

        bucket_3 = GeoBucketFactory.create(property_count=3)
        PropertyFactory.create_batch(3, geo_bucket=bucket_3)

        service = GeoBucketService(session=self.async_db_session)
        stats = await service.get_stats()

        if len(stats.top_buckets) > 1:
            for i in range(len(stats.top_buckets) - 1):
                self.assertGreaterEqual(
                    stats.top_buckets[i].property_count,
                    stats.top_buckets[i + 1].property_count,
                )

    async def test_get_stats__database_exception(self):
        service = GeoBucketService(session=self.async_db_session)

        with patch.object(
            service,
            "_get_basic_stats",
            side_effect=DatabaseException("Database error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.get_stats()

            self.assertIn("Failed to retrieve geo bucket stats", str(context.exception))

    async def test_get_stats__unexpected_exception(self):
        service = GeoBucketService(session=self.async_db_session)

        with patch.object(
            service,
            "_get_basic_stats",
            side_effect=Exception("Unexpected error"),
        ):
            with self.assertRaises(AppException) as context:
                await service.get_stats()

            self.assertIn("unexpected error occurred", str(context.exception))

    async def test_get_stats__coverage_metrics(self):
        service = GeoBucketService(session=self.async_db_session)
        stats = await service.get_stats()

        self.assertIsNotNone(stats.coverage)
        self.assertIsNotNone(stats.coverage.unique_locations)
        self.assertGreaterEqual(stats.coverage.unique_locations, 0)

    async def test_get_stats__resolution_distribution(self):
        service = GeoBucketService(session=self.async_db_session)
        stats = await service.get_stats()

        self.assertIsNotNone(stats.resolution_stats)
        self.assertIsInstance(stats.resolution_stats, list)
