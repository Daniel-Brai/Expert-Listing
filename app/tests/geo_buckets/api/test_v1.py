from fastapi import status
from tests.conftest import client
from tests.geo_buckets.factory import GeoBucketFactory
from tests.properties.factory import PropertyFactory
from tests.testutils import CustomDBTestCase


class GetGeoBucketStatsRouterTests(CustomDBTestCase):
    def setUp(self):
        super().setUp()
        self.client = client()
        self.url = "/api/v1/geo-buckets/stats"

        self.empty_buckets = [GeoBucketFactory.create(property_count=0) for _ in range(3)]

        self.bucket_with_5_properties = GeoBucketFactory.create(property_count=5)
        PropertyFactory.create_batch(5, geo_bucket=self.bucket_with_5_properties)

        self.bucket_with_10_properties = GeoBucketFactory.create(property_count=10)
        PropertyFactory.create_batch(10, geo_bucket=self.bucket_with_10_properties)

    def test_get_stats__successful(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("data", response_data)
        self.assertIn("message", response_data)
        self.assertEqual(
            response_data["message"],
            "Geo bucket statistics retrieved successfully.",
        )

        stats_data = response_data["data"]
        self.assertIn("total_buckets", stats_data)
        self.assertIn("total_properties", stats_data)
        self.assertIn("empty_buckets", stats_data)
        self.assertIn("top_buckets", stats_data)
        self.assertIn("coverage", stats_data)
        self.assertIn("resolution_stats", stats_data)

    def test_get_stats__total_buckets_count(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        stats_data = response_data["data"]

        self.assertGreaterEqual(stats_data["total_buckets"], 5)

    def test_get_stats__empty_buckets_count(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        stats_data = response_data["data"]

        self.assertGreaterEqual(stats_data["empty_buckets"], 3)

    def test_get_stats__top_buckets_structure(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        top_buckets = response_data["data"]["top_buckets"]

        self.assertIsInstance(top_buckets, list)

        if len(top_buckets) > 0:
            bucket = top_buckets[0]
            self.assertIn("bucket_id", bucket)
            self.assertIn("h3_index", bucket)
            self.assertIn("canonical_name", bucket)
            self.assertIn("property_count", bucket)
            self.assertIn("center_lat", bucket)
            self.assertIn("center_lng", bucket)

    def test_get_stats__top_buckets_ordered_by_count(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        top_buckets = response_data["data"]["top_buckets"]

        if len(top_buckets) > 1:
            for i in range(len(top_buckets) - 1):
                self.assertGreaterEqual(
                    top_buckets[i]["property_count"],
                    top_buckets[i + 1]["property_count"],
                )

    def test_get_stats__top_buckets_excludes_empty(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        top_buckets = response_data["data"]["top_buckets"]

        for bucket in top_buckets:
            self.assertGreater(bucket["property_count"], 0)

    def test_get_stats__coverage_structure(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        coverage = response_data["data"]["coverage"]

        self.assertIsInstance(coverage, dict)
        self.assertIn("unique_locations", coverage)
        self.assertIn("avg_bucket_density", coverage)
        self.assertIn("total_area_km2", coverage)
        self.assertIn("bounding_box", coverage)

    def test_get_stats__coverage_unique_locations(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        coverage = response_data["data"]["coverage"]

        self.assertIsInstance(coverage["unique_locations"], int)
        self.assertGreaterEqual(coverage["unique_locations"], 0)

    def test_get_stats__resolutions_structure(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        resolutions = response_data["data"]["resolution_stats"]

        self.assertIsInstance(resolutions, list)

        if len(resolutions) > 0:
            resolution = resolutions[0]
            self.assertIn("resolution", resolution)
            self.assertIn("bucket_count", resolution)
            self.assertIn("avg_properties_per_bucket", resolution)
            self.assertIn("max_properties_in_bucket", resolution)
            self.assertIn("min_properties_in_bucket", resolution)
            self.assertIn("total_properties", resolution)

    def test_get_stats__no_metadata(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("metadata", response_data)
        self.assertIsNone(response_data["metadata"])

    def test_get_stats__response_format(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertIn("data", response_data)
        self.assertIn("message", response_data)
        self.assertIn("metadata", response_data)

        expected_keys = {
            "total_buckets",
            "total_properties",
            "empty_buckets",
            "top_buckets",
            "coverage",
            "resolution_stats",
        }
        self.assertEqual(set(response_data["data"].keys()), expected_keys)

    def test_get_stats__numeric_values(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        stats_data = response_data["data"]

        self.assertIsInstance(stats_data["total_buckets"], int)
        self.assertIsInstance(stats_data["empty_buckets"], int)
        self.assertIsInstance(stats_data["coverage"]["unique_locations"], int)
        self.assertIsInstance(stats_data["coverage"]["avg_bucket_density"], (int, float))

    def test_get_stats__top_buckets_limit(self):
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        top_buckets = response_data["data"]["top_buckets"]

        self.assertLessEqual(len(top_buckets), 10)

    def test_get_stats__consistent_results(self):
        response1 = self.client.get(url=self.url)
        response2 = self.client.get(url=self.url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.json()["data"]
        data2 = response2.json()["data"]

        self.assertEqual(data1["total_buckets"], data2["total_buckets"])
        self.assertEqual(data1["empty_buckets"], data2["empty_buckets"])
