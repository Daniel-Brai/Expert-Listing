from shared.types.schemas import DataType, IResponse, MetaDataType


def build_json_response(
    data: DataType,
    message: str | None = None,
    metadata: MetaDataType | None = None,
) -> IResponse[DataType, MetaDataType]:
    """
    Creates a standardized API response.

    Args:
        data (DataType): The main data payload of the response.
        message (str | None): An optional message providing additional information about the response.
        metadata (MetaDataType | None): Optional metadata about the response

    Returns:
        IResponse[DataType, MetaDataType]: An instance of `IResponse` containing the provided data, message, and metadata.
    """

    return IResponse[DataType, MetaDataType](
        message=message,
        data=data,
        metadata=metadata,
    )
