from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel

DataType = TypeVar("DataType")
MetaDataType = TypeVar("MetaDataType")


@dataclass
class RequestInfo:
    """
    Schema representing request information.

    Attributes:
        ip_address (str | None): The IP address from which the request originated.
        user_agent (str | None): The user agent string of the client making the request.
        request_id (str | None): An optional unique identifier for the request.
        cookies (dict[str, str]): The cookies from the request.
        authorization (str | None): The extracted bearer token from the Authorization header.
    """

    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    cookies: dict[str, str] = field(default_factory=dict)
    authorization: str | None = None


class IResponse(BaseModel, Generic[DataType, MetaDataType]):
    """
    Base response model for API responses.

    Attributes:
        message (str | None): A message providing additional information about the response.
        data (DataType | None): The main data payload of the response, which can be of any type `DataType`.
        metadata (MetaType | None): Additional metadata about the response.
    """

    message: str | None = None
    data: DataType | None = None
    metadata: MetaDataType | None = None
