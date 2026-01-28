from typing import List

from core.logging import get_logger
from pydantic_extra_types.coordinate import Latitude, Longitude
from sqlmodel.ext.asyncio.session import AsyncSession
from src.properties.schemas.property import PropertyCreateRequest, PropertyRead
from src.properties.services.property_service import PropertyService

logger = get_logger(__name__)


async def run(session: AsyncSession) -> List[PropertyRead]:
    """
    Create sample properties with geo-buckets.
    Includes test data for Sangotedo location matching.
    """

    property_service = PropertyService(session=session)

    created: list[PropertyRead] = []

    test_properties = [
        PropertyCreateRequest(
            title="Luxury 3 Bedroom Flat in Sangotedo",
            location_name="Sangotedo",
            lat=Latitude(6.4698),
            lng=Longitude(3.6285),
            attributes={
                "price": 15000000,
                "bedrooms": 3,
                "bathrooms": 3,
                "description": "Modern apartment with excellent facilities",
            },
        ),
        PropertyCreateRequest(
            title="Beautiful 4 Bedroom Duplex",
            location_name="Sangotedo, Ajah",
            lat=Latitude(6.4720),
            lng=Longitude(3.6301),
            attributes={
                "price": 25000000,
                "bedrooms": 4,
                "bathrooms": 4,
                "description": "Spacious duplex in a gated estate",
            },
        ),
        PropertyCreateRequest(
            title="Affordable 2 Bedroom Apartment",
            location_name="sangotedo lagos",
            lat=Latitude(6.4705),
            lng=Longitude(3.6290),
            attributes={
                "price": 12000000,
                "bedrooms": 2,
                "bathrooms": 2,
                "description": "Cozy apartment perfect for small families",
            },
        ),
        PropertyCreateRequest(
            title="5 Bedroom Detached House in Lekki",
            location_name="Lekki Phase 1",
            lat=Latitude(6.4474),
            lng=Longitude(3.4739),
            attributes={
                "price": 85000000,
                "bedrooms": 5,
                "bathrooms": 6,
                "description": "Luxury detached house with swimming pool",
            },
        ),
        PropertyCreateRequest(
            title="3 Bedroom Flat in Lekki Phase 1",
            location_name="Lekki Phase 1, Lagos",
            lat=Latitude(6.4480),
            lng=Longitude(3.4745),
            attributes={
                "price": 35000000,
                "bedrooms": 3,
                "bathrooms": 3,
                "description": "Well-finished apartment in prime location",
            },
        ),
        PropertyCreateRequest(
            title="Studio Apartment in Victoria Island",
            location_name="Victoria Island",
            lat=Latitude(6.4281),
            lng=Longitude(3.4219),
            attributes={
                "price": 18000000,
                "bedrooms": 1,
                "bathrooms": 1,
                "description": "Modern studio in the heart of VI",
            },
        ),
        PropertyCreateRequest(
            title="4 Bedroom Terrace in Ajah",
            location_name="Ajah",
            lat=Latitude(6.4650),
            lng=Longitude(3.5870),
            attributes={
                "price": 28000000,
                "bedrooms": 4,
                "bathrooms": 4,
                "description": "Contemporary terrace house in serene environment",
            },
        ),
        PropertyCreateRequest(
            title="2 Bedroom Flat in Ajah, Lagos",
            location_name="Ajah Lagos",
            lat=Latitude(6.4658),
            lng=Longitude(3.5880),
            attributes={
                "price": 16000000,
                "bedrooms": 2,
                "bathrooms": 2,
                "description": "Affordable flat in developing area",
            },
        ),
        PropertyCreateRequest(
            title="6 Bedroom Mansion in Ikoyi",
            location_name="Ikoyi",
            lat=Latitude(6.4541),
            lng=Longitude(3.4316),
            attributes={
                "price": 150000000,
                "bedrooms": 6,
                "bathrooms": 7,
                "description": "Opulent mansion with premium finishes",
            },
        ),
        PropertyCreateRequest(
            title="3 Bedroom Bungalow in Epe",
            location_name="Epe",
            lat=Latitude(6.5833),
            lng=Longitude(3.9833),
            attributes={
                "price": 9000000,
                "bedrooms": 3,
                "bathrooms": 2,
                "description": "Peaceful bungalow away from city noise",
            },
        ),
    ]

    for _, property_data in enumerate(test_properties, start=1):
        try:
            property = await property_service.create_property_if_not_exists(payload=property_data)
            created.append(property)
        except Exception as e:
            logger.error(f"Failed to create property {property_data.title}: {str(e)}")
            continue

    logger.info("Property seeding completed")

    return created
