from fastapi import status
from tests.conftest import client
from tests.geo_buckets.factory import GeoBucketFactory
from tests.properties.factory import PropertyFactory
from tests.testutils import CustomDBTestCase


class CreatePropertyRouterTests(CustomDBTestCase):
    def setUp(self):
        super().setUp()
        self.client = client()
        self.url = "/api/v1/properties"

        self.geo_bucket = GeoBucketFactory.create()

    def test_create_property__successful(self):
        request_data = {
            "title": "Beautiful 3-bedroom apartment",
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 3.3792,
            "attributes": {
                "price": 150000,
                "bedrooms": 3,
                "bathrooms": 2,
            },
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertIn("data", response_data)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Property created successfully")
        self.assertIsNotNone(response_data["data"]["id"])
        self.assertEqual(response_data["data"]["title"], request_data["title"])
        self.assertEqual(response_data["data"]["location_name"], request_data["location_name"])

    def test_create_property__minimal_data(self):
        request_data = {
            "title": "Simple property",
            "location_name": "Abuja",
            "lat": 9.0765,
            "lng": 7.3986,
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("data", response_data)
        self.assertEqual(response_data["data"]["title"], request_data["title"])

    def test_create_property__missing_required_field(self):
        request_data = {
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 3.3792,
        }

        response = self.client.post(url=self.url, json=request_data)

        response_data = response.json()
        self.assertIn("detail", response_data)

    def test_create_property__invalid_latitude(self):
        request_data = {
            "title": "Test property",
            "location_name": "Lagos",
            "lat": 95.0,  # Invalid latitude (must be -90 to 90)
            "lng": 3.3792,
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_property__invalid_longitude(self):
        request_data = {
            "title": "Test property",
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 185.0,  # Invalid longitude (must be -180 to 180)
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_property__empty_title(self):
        request_data = {
            "title": "",
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 3.3792,
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_property__title_too_long(self):
        request_data = {
            "title": "A" * 2001,  # Exceeds max length
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 3.3792,
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_property__with_complex_attributes(self):
        request_data = {
            "title": "Luxury villa with amenities",
            "location_name": "Lagos",
            "lat": 6.5244,
            "lng": 3.3792,
            "attributes": {
                "price": 5000000,
                "bedrooms": 5,
                "bathrooms": 4,
                "amenities": ["pool", "gym", "parking"],
                "features": {
                    "has_garden": True,
                    "has_security": True,
                    "floor_number": 2,
                },
            },
        }

        response = self.client.post(url=self.url, json=request_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIsNotNone(response_data["data"]["id"])


class GetPropertiesRouterTests(CustomDBTestCase):
    def setUp(self):
        super().setUp()
        self.client = client()
        self.url = "/api/v1/properties"

        self.geo_bucket = GeoBucketFactory.create()

        self.properties = [PropertyFactory.create(geo_bucket=self.geo_bucket) for _ in range(10)]

    def test_get_properties__successful(self):
        """Test successful retrieval of properties."""
        response = self.client.get(url=self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("data", response_data)
        self.assertIn("metadata", response_data)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Properties retrieved successfully")
        self.assertIsInstance(response_data["data"], list)
        self.assertGreaterEqual(len(response_data["data"]), 1)

    def test_get_properties__with_cursor_pagination(self):
        first_response = self.client.get(url=self.url, params={"size": 3})
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        first_data = first_response.json()

        if len(first_data["data"]) < 3:
            return

        next_cursor = first_data["metadata"].get("next_page")
        if not next_cursor:
            return

        second_response = self.client.get(url=self.url, params={"size": 3, "cursor": next_cursor})
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        second_data = second_response.json()

        first_ids = {prop["id"] for prop in first_data["data"]}
        second_ids = {prop["id"] for prop in second_data["data"]}
        self.assertEqual(len(first_ids.intersection(second_ids)), 0)

    def test_get_properties__with_location_filter(self):
        location_name = "Test Location"
        filtered_geo_bucket = GeoBucketFactory.create(
            canonical_name=location_name,
        )
        filtered_property = PropertyFactory.create(
            location_name=location_name,
            geo_bucket=filtered_geo_bucket,
        )

        response = self.client.get(url=self.url, params={"location": location_name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertGreaterEqual(len(response_data["data"]), 1)

        property_ids = [prop["id"] for prop in response_data["data"]]
        self.assertIn(filtered_property.id, property_ids)

    def test_get_properties__empty_result(self):
        response = self.client.get(url=self.url, params={"location": "NonexistentLocation"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data["data"]), 0)
        self.assertEqual(response_data["metadata"]["total"], 0)

    def test_get_properties__metadata_structure(self):
        response = self.client.get(url=self.url, params={"limit": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        metadata = response_data["metadata"]

        self.assertIsNotNone(metadata)
        self.assertIn("total", metadata)
        self.assertIn("next_page", metadata)
        self.assertIsInstance(metadata["total"], int)

    def test_get_properties__data_structure(self):
        response = self.client.get(url=self.url, params={"limit": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        if len(response_data["data"]) > 0:
            property_data = response_data["data"][0]
            self.assertIn("id", property_data)
            self.assertIn("title", property_data)
            self.assertIn("location_name", property_data)
            self.assertIn("latitude", property_data)
            self.assertIn("longitude", property_data)
