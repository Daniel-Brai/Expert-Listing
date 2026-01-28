from factory import Faker, LazyAttribute, LazyFunction  # type: ignore
from factory.alchemy import SQLAlchemyModelFactory  # type: ignore
from shared.utils import H3Utils, LocationUtils
from src.geo_buckets.models.geo_bucket import GeoBucket
from tests.conftest import TestDBSession


class GeoBucketFactory(SQLAlchemyModelFactory):
    """
    Factory for creating GeoBucket test instances.
    """

    h3_index = LazyFunction(
        lambda: H3Utils.calculate_h3_indexes(
            lat=Faker("latitude").evaluate(None, None, {"locale": None}),
            lng=Faker("longitude").evaluate(None, None, {"locale": None}),
        ).h3_r8
    )
    h3_resolution = 8
    parent_h3 = LazyAttribute(lambda obj: H3Utils.get_parent_h3(obj.h3_index, 7))
    canonical_name = Faker("city")
    canonical_name_normalized = LazyAttribute(lambda obj: LocationUtils().normalize(obj.canonical_name))
    center_point = LazyAttribute(lambda obj: H3Utils.h3_to_geometry(obj.h3_index)[0])
    hexagon_boundary = LazyAttribute(lambda obj: H3Utils.h3_to_geometry(obj.h3_index)[1])
    property_count = 0

    class Meta:  # type: ignore
        model = GeoBucket
        sqlalchemy_session_factory = TestDBSession
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_get_or_create = ("h3_index",)
