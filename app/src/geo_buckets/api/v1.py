from typing import Annotated

from database import get_db_session
from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from shared.types import IResponse
from shared.utils import build_json_response
from sqlmodel.ext.asyncio.session import AsyncSession
from src.geo_buckets.schemas.geo_bucket import GeoBucketStats
from src.geo_buckets.services.geo_bucket_service import GeoBucketService

router = APIRouter()


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    operation_id="get_geo_bucket_stats",
    response_model=IResponse[GeoBucketStats, None],
)
async def get_stats(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IResponse[GeoBucketStats, None]:
    """
    Get the statistics of geo buckets.
    """

    geo_bucket_service = GeoBucketService(session=session)

    data = await geo_bucket_service.get_stats()

    return build_json_response(
        data=jsonable_encoder(data),
        message="Geo bucket statistics retrieved successfully.",
    )
