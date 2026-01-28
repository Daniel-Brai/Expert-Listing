from factory import Faker, LazyAttribute, LazyFunction, SubFactory  # type: ignore
from factory.alchemy import SQLAlchemyModelFactory  # type: ignore
from shared.utils import H3Utils, LocationUtils
from src.properties.models.property import Property
from tests.conftest import TestDBSession
from tests.geo_buckets.factory import GeoBucketFactory


class PropertyFactory(SQLAlchemyModelFactory):
    """
    Factory for creating Property test instances.
    """

    title = Faker("sentence", nb_words=6)
    location_name = Faker("city")
    location_name_normalized = LazyAttribute(lambda obj: LocationUtils().normalize(obj.location_name))

    _lat = LazyFunction(
        lambda: Faker("pyfloat", left_digits=1, right_digits=4, min_value=6.4, max_value=6.6).evaluate(
            None, None, {"locale": None}
        )
    )
    _lng = LazyFunction(
        lambda: Faker("pyfloat", left_digits=1, right_digits=4, min_value=3.3, max_value=3.7).evaluate(
            None, None, {"locale": None}
        )
    )

    coordinates = LazyAttribute(lambda obj: H3Utils.create_point_geometry(obj._lat, obj._lng))
    h3_index_r8 = LazyAttribute(lambda obj: H3Utils.calculate_h3_indexes(obj._lat, obj._lng).h3_r8)
    h3_index_r9 = LazyAttribute(lambda obj: H3Utils.calculate_h3_indexes(obj._lat, obj._lng).h3_r9)

    attributes = LazyFunction(
        lambda: {
            "price": Faker("pyint", min_value=50000, max_value=5000000).evaluate(None, None, {"locale": None}),
            "bedrooms": Faker("pyint", min_value=1, max_value=6).evaluate(None, None, {"locale": None}),
            "bathrooms": Faker("pyint", min_value=1, max_value=4).evaluate(None, None, {"locale": None}),
        }
    )

    geo_bucket = SubFactory(GeoBucketFactory)
    geo_bucket_id = LazyAttribute(lambda obj: obj.geo_bucket.id if obj.geo_bucket else None)

    class Meta:  # type: ignore
        model = Property
        sqlalchemy_session_factory = TestDBSession
        sqlalchemy_session_persistence = "commit"
        exclude = ("_lat", "_lng")
