from database import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from src.geo_buckets.models.geo_bucket import GeoBucket
from src.geo_buckets.schemas.geo_bucket import GeoBucketCreate, GeoBucketUpdate


class GeoBucketRepository(BaseRepository[GeoBucket, GeoBucketCreate, GeoBucketUpdate]):
    """
    Repository class for managing `GeoBucket` entities.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(GeoBucket, session)
