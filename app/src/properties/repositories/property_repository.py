from database import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from src.properties.models.property import Property
from src.properties.schemas.property import PropertyCreate, PropertyUpdate


class PropertyRepository(BaseRepository[Property, PropertyCreate, PropertyUpdate]):
    """
    Repository class for managing `Property` entities.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Property, session)
