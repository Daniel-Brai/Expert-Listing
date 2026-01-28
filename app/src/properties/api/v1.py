from typing import Annotated

from core.pagination import CursorPaginationMetadata, CursorParams
from database import get_db_session
from fastapi import APIRouter, Body, Depends, status
from fastapi.encoders import jsonable_encoder
from shared.types import IResponse
from shared.utils import build_json_response
from sqlmodel.ext.asyncio.session import AsyncSession
from src.properties.schemas.property import PropertyCreateRequest, PropertyQueryParams, PropertyRead
from src.properties.services.property_service import PropertyService

router = APIRouter()


@router.post(
    "",
    operation_id="create_property",
    status_code=status.HTTP_200_OK,
    response_model=IResponse[PropertyRead, None],
)
async def create_property(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    body: Annotated[PropertyCreateRequest, Body(..., description="Payload to create a new property")],
) -> IResponse[PropertyRead, None]:
    """
    Creates a new property listing
    """

    property_service = PropertyService(session=session)

    data = await property_service.create_property(payload=body)

    return build_json_response(data=jsonable_encoder(data), message="Property created successfully")


@router.get(
    "",
    operation_id="get_properties",
    status_code=status.HTTP_200_OK,
    response_model=IResponse[list[PropertyRead], CursorPaginationMetadata],
)
async def get_properties(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    pagination: Annotated[CursorParams, Depends()],
    query: Annotated[PropertyQueryParams, Depends()],
) -> IResponse[list[PropertyRead], CursorPaginationMetadata]:
    """
    Retrieves property listings in pages
    """

    property_service = PropertyService(session=session)

    data, metadata = await property_service.list_properties(pagination=pagination, query_params=query)

    return build_json_response(
        data=[jsonable_encoder(item) for item in data],
        metadata=metadata,
        message="Properties retrieved successfully",
    )
