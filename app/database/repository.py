from collections.abc import Callable
from typing import Any, Generic, Literal, TypeVar

from core.filters import Filter
from core.logging import get_logger
from core.pagination import CursorParams, LimitOffsetParams
from database.transaction import in_transaction
from fastapi_pagination import set_page, set_params
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_pagination.limit_offset import LimitOffsetPage
from pydantic import BaseModel
from shared.exceptions import DatabaseException
from shared.types import ID
from shared.utils import get_obj_or_type_value as call
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from sqlmodel import SQLModel, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing CRUD operations for SQLModel models.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def paginate(
        self,
        *,
        query: Any,
        count_query: Any,
        filters: Filter | None,
        cursor_params: CursorParams,
        page_schema: type[BaseModel] | ModelType,
        transformer: Callable[..., Any] | None,
    ) -> CursorPage[Any]:
        """
        Paginate records of the models that returns a `CursorPage[PageSchema]` using keyset pagination.

        Args:
            query (Any): Base SQLAlchemy query to paginate
            filter (Filter): Filter instance to apply filtering and sorting
            cursor_params (CursorParams): Cursor pagination parameters
            page_schema: The schema type for the paginated response items
            count_query (Any): Optional count query for total records (if None, total won't be included)
            transformer (Callable[..., Any] | None): Optional function to transform query results before returning

        Returns:
            CursorPage[Any]: CursorPage with paginated results

        Raises:
            DatabaseException: If the pagination fails

        Example:
            ```python
            paginated_result = await repository.paginate(
                query=select(User).options(selectinload(User.profile)),
                filter=user_filter,
                cursor_params=pagination_data,
                page_schema=UserSchema,
                count_query=select(func.count(User.id)),
                transformer=lambda users: [UserSchema.to_schema(user) for user in users],
            )
            ```
        """
        try:
            filtered_query = query

            if filters:
                filtered_query = filters.sort(filters.filter(query))  # type: ignore

            set_page(CursorPage[page_schema])
            set_params(cursor_params)  # type: ignore

            paginated_result = await apaginate(  # type: ignore
                conn=self.session,
                query=filtered_query,  # type: ignore
                count_query=count_query,
                transformer=transformer if transformer else None,
            )

            return paginated_result  # type: ignore
        except SQLAlchemyError as e:
            logger.error(f"Failed to paginate records: {str(e)}")
            raise DatabaseException(
                message="Failed to paginate records",
            ) from e

    async def paginate_with_offset(
        self,
        *,
        query: Any,
        count_query: Any,
        filters: Filter | None,
        limit_offset_params: LimitOffsetParams,
        page_schema: type[BaseModel] | ModelType,
        transformer: Callable[..., Any] | None,
    ) -> LimitOffsetPage[Any]:
        """
        Paginate records of the models that returns a `LimitOffsetPage[PageSchema]` using limit and offset pagination.

        Args:
            query (Any): Base SQLAlchemy query to paginate
            filter (Filter): Filter instance to apply filtering and sorting
            limit_offset_params (LimitOffsetParams): Limit-offset pagination parameters
            page_schema: The schema type for the paginated response items
            count_query (Any): Optional count query for total records (if None, total won't be included)
            transformer (Callable[..., Any] | None): Optional function to transform query results before returning

        Returns:
            LimitOffsetPage[Any]: LimitOffsetPage with paginated results

        Raises:
            DatabaseException: If the pagination fails
        """
        try:
            filtered_query = query

            if filters:
                filtered_query = filters.sort(filters.filter(query))  # type: ignore

            set_page(LimitOffsetPage[page_schema])
            set_params(limit_offset_params)  # type: ignore

            paginated_result = await apaginate(  # type: ignore
                conn=self.session,
                query=filtered_query,  # type: ignore
                count_query=count_query,
                transformer=transformer if transformer else None,
            )

            return paginated_result  # type: ignore
        except SQLAlchemyError as e:
            logger.error(f"Failed to paginate records: {str(e)}")
            raise DatabaseException(
                message="Failed to paginate records",
            ) from e

    async def find_all(self, where: dict[str, Any] | None = None) -> list[ModelType]:
        """
        Find all records of the model.

        Returns:
            List of all records
        """
        try:
            query = select(self.model)
            if where:
                for field, value in where.items():
                    if hasattr(self.model, field):
                        query = query.where(col(getattr(self.model, field)) == value)

            result = await self.session.exec(query)
            return list(result.all())
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to retrieve records",
            ) from e

    async def find_all_in(
        self,
        field: str,
        values: list[Any],
        preload_relationships: list[str] | None = None,
        load_strategy: Literal["selectin", "joined", "subquery"] | None = None,
    ) -> list[ModelType]:
        """
        Find all records where a field's value is in the provided list (IN operator).

        Args:
            field: The model attribute name to filter on
            values: List of values to match using the SQL IN operator
            preload_relationships: Optional list of relationship attribute names to preload
            load_strategy: Optional loading strategy to use for the preloads ("selectin", "joined", "subquery").
                If None (default) no preload loading strategy will be applied even if `preload_relationships` is provided.

        Returns:
            List of matching records
        """
        try:
            if not values:
                return []

            if not hasattr(self.model, field):
                return []

            column = col(getattr(self.model, field))
            query = select(self.model).where(column.in_(values))  # type: ignore

            if preload_relationships and load_strategy is not None:
                if load_strategy == "selectin":
                    loader = selectinload
                elif load_strategy == "joined":
                    loader = joinedload
                elif load_strategy == "subquery":
                    loader = subqueryload
                else:
                    raise ValueError(
                        f"Invalid load_strategy: {load_strategy}. Must be one of: 'selectin', 'joined', 'subquery'"
                    )

                for relationship in preload_relationships:
                    if hasattr(self.model, relationship):
                        query = query.options(loader(getattr(self.model, relationship)))

            result = await self.session.exec(query)
            return list(result.all())
        except ValueError as ve:
            raise DatabaseException(
                message=str(ve),
            ) from ve
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to retrieve records via IN operator",
            ) from e

    async def find_one_by_and_none(self, **kwargs: Any) -> ModelType | None:
        """
        Find a single record by field values (use AND condition).

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            The found record or None
        """
        try:
            query = select(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.where(col(getattr(self.model, field)) == value)
            result = await self.session.exec(query)
            return result.one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to find record",
            ) from e

    # Backwards-compatible alias used in some tests / older code
    async def find_one_by(self, **kwargs: Any) -> ModelType | None:
        """Alias to `find_one_by_and_none` for compatibility."""
        return await self.find_one_by_and_none(**kwargs)

    async def find_one_by_or_none(self, **kwargs: Any) -> ModelType | None:
        """
        Find a single record by field values (use OR condition).

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            The found record or None
        """

        try:
            query = select(self.model)
            conditions = [
                col(getattr(self.model, field)) == value
                for field, value in kwargs.items()
                if hasattr(self.model, field)
            ]

            if not conditions:
                return None

            query = query.filter(or_(*conditions))
            result = await self.session.exec(query)
            return result.one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to find record",
            ) from e

    async def find_one_with_criteria(
        self,
        criteria: dict[str, Any],
        preload_relationships: list[str] | None = None,
        load_strategy: Literal["selectin", "joined", "subquery"] = "selectin",
    ) -> ModelType | None:
        """
        Find a single record with preloaded relationships.

        Args:
            criteria: Field names and values to filter by
            preload_relationships: List of relationship attribute names to preload
            load_strategy: The loading strategy to use ("selectin", "joined", "subquery")

        Returns:
            The found record with preloaded relationships or None

        Raises:
            DatabaseException: If the query fails or an invalid load strategy is provided
        """
        try:
            query = select(self.model)

            for field, value in criteria.items():
                if hasattr(self.model, field):
                    query = query.where(col(getattr(self.model, field)) == value)

            if preload_relationships:
                if load_strategy == "selectin":
                    loader = selectinload
                elif load_strategy == "joined":
                    loader = joinedload
                elif load_strategy == "subquery":
                    loader = subqueryload
                else:
                    raise ValueError(
                        f"Invalid load_strategy: {load_strategy}. " "Must be one of: 'selectin', 'joined', 'subquery'"
                    )

                for relationship in preload_relationships:
                    if hasattr(self.model, relationship):
                        query = query.options(loader(getattr(self.model, relationship)))

            result = await self.session.exec(query)
            return result.one_or_none()
        except ValueError as ve:
            raise DatabaseException(
                message=str(ve),
            ) from ve
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to find record with preloads",
            ) from e

    async def create(self, schema: CreateSchemaType | dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            schema: The data to create the record with

        Returns:
            The created record
        """

        try:
            if isinstance(schema, dict):
                db_obj = self.model(**schema)
            else:
                db_obj = self.model(**schema.model_dump())

            if hasattr(db_obj, "set_friendly_fields"):
                call(db_obj, "set_friendly_fields")

            self.session.add(db_obj)
            await self.save_changes(refresh_obj=db_obj)
            return db_obj
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to create record",
            ) from e

    async def create_if_not_exists(
        self, schema: CreateSchemaType | dict[str, Any], unique_fields: list[str]
    ) -> ModelType:
        """
        Create a new record if it does not already exist based on unique fields.

        Args:
            schema: The data to create the record with
            unique_fields: List of field names that should be unique
        Returns:
            The created or existing record
        """

        try:
            filter_kwargs = {field: getattr(schema, field) for field in unique_fields if hasattr(schema, field)}
            existing_entity = await self.find_one_by_and_none(**filter_kwargs)

            if existing_entity:
                return existing_entity

            return await self.create(schema)
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to create record",
            ) from e

    async def create_many(self, schemas: list[CreateSchemaType]) -> list[ModelType]:
        """
        Create multiple records.

        Args:
            schemas: The data to create the records with

        Returns:
            The created records
        """

        try:
            db_objs = [self.model(**schema.model_dump()) for schema in schemas]

            for db_obj in db_objs:
                if hasattr(db_obj, "set_friendly_fields"):
                    call(db_obj, "set_friendly_fields")

            self.session.add_all(db_objs)
            await self.save_changes()
            return db_objs
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to create records",
            ) from e

    async def create_many_if_not_exists(
        self, schemas: list[CreateSchemaType], unique_fields: list[str]
    ) -> list[ModelType]:
        """
        Create multiple records if they do not already exist based on unique fields.

        Args:
            schemas: The data to create the records with
            unique_fields: List of field names that should be unique
        Returns:
            The created or existing records
        """

        created_entities: list[ModelType] = []

        try:
            for schema in schemas:
                filter_kwargs = {field: getattr(schema, field) for field in unique_fields if hasattr(schema, field)}
                existing_entity = await self.find_one_by_and_none(**filter_kwargs)

                if existing_entity:
                    created_entities.append(existing_entity)
                else:
                    new_entity = await self.create(schema)
                    created_entities.append(new_entity)

            return created_entities
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to create records",
            ) from e

    async def update(self, id: ID, schema: UpdateSchemaType | dict[str, Any]) -> ModelType | None:
        """
        Update a record by ID.

        Args:
            id: The id of the record to update
            schema: The data to update the record with

        Returns:
            The updated record or None if not found
        """

        try:
            existing_entity = await self.find_one_by_and_none(id=id)

            if not existing_entity:
                return None

            if isinstance(schema, BaseModel):
                schema = schema.model_dump(exclude_unset=True)

            updated_fields = schema
            if not updated_fields:
                return existing_entity

            existing_entity.sqlmodel_update(updated_fields)
            self.session.add(existing_entity)
            await self.save_changes(refresh_obj=existing_entity)

            return existing_entity
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to update record",
            ) from e

    async def update_many(self, ids: list[ID], schema: list[UpdateSchemaType | dict[str, Any]]) -> list[ModelType]:
        """
        Update multiple records by their IDs.
        Args:
            ids: The ids of the records to update
            schema: The data to update the records with
        Returns:
            The updated records
        """

        try:
            updated_entities: list[ModelType] = []

            for record_id, record_schema in zip(ids, schema):
                existing_entity = await self.find_one_by_and_none(id=record_id)

                if not existing_entity:
                    continue

                if isinstance(record_schema, BaseModel):
                    record_schema = record_schema.model_dump(exclude_unset=True)

                updated_fields = record_schema
                if not updated_fields:
                    updated_entities.append(existing_entity)
                    continue

                existing_entity.sqlmodel_update(updated_fields)
                self.session.add(existing_entity)
                updated_entities.append(existing_entity)

            await self.save_changes()

            return updated_entities
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to update records",
            ) from e

    async def delete(self, id: ID) -> bool:
        """
        Delete a record by ID.

        Args:
            id: The id of the record to delete

        Returns:
            True if the record was deleted, False if not found
        """

        try:
            query = select(self.model).where(col(self.model.id) == id)  # type: ignore
            result = (await self.session.exec(query)).one_or_none()

            if not result:
                return False

            await self.session.delete(result)
            await self.save_changes()
            return True
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to delete record",
            ) from e

    async def delete_with_criteria(self, where: dict[str, Any]) -> int:
        """
        Delete records matching the given criteria.

        Args:
            where (dict[str, Any]): Field names and values to filter by

        Returns:
            The number of records deleted
        """

        try:
            query = select(self.model)

            for field, value in where.items():
                if hasattr(self.model, field):
                    query = query.where(col(getattr(self.model, field)) == value)

            results = await self.session.exec(query)
            records_to_delete = results.all()

            for record in records_to_delete:
                await self.session.delete(record)

            await self.save_changes()
            return len(records_to_delete)
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to delete records",
            ) from e

    async def delete_many(self, ids: list[ID]) -> int:
        """
        Delete multiple records by their IDs.

        Args:
            ids: The ids of the records to delete

        Returns:
            The number of records deleted
        """

        try:
            if len(ids) == 0:
                return 0

            query = select(self.model).where(col(self.model.id).in_(ids))  # type: ignore
            results = await self.session.exec(query)
            records_to_delete = results.all()

            for record in records_to_delete:
                await self.session.delete(record)

            await self.save_changes()
            return len(records_to_delete)
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to delete records",
            ) from e

    async def delete_many_with_criteria(
        self, where: dict[str, Any], operator: Literal["AND", "OR", "IN"] = "AND"
    ) -> int:
        """
        Delete multiple records matching the given criteria.

        Args:
            where (dict[str, Any]): Field names and values to filter by
            op (Literal['and', 'or', "in"]): The logical operator to use for combining conditions ('and', 'or', 'in')

        Returns:
            The number of records deleted
        """

        try:
            query = select(self.model)
            conditions = []

            for field, value in where.items():
                if hasattr(self.model, field):
                    column = col(getattr(self.model, field))
                    # Use IN operator if value is a list
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    elif operator == "AND":
                        conditions.append(column == value)
                    elif operator == "OR":
                        conditions.append(column == value)
                    elif operator == "IN":
                        if isinstance(value, list):
                            conditions.append(column.in_(value))
                        else:
                            conditions.append(column.in_([value]))

            if conditions:
                if operator == "AND":
                    for condition in conditions:
                        query = query.where(condition)
                elif operator == "OR":
                    query = query.filter(or_(*conditions))
                elif operator == "IN":
                    query = query.filter(*conditions)

            results = await self.session.exec(query)
            records_to_delete = results.all()

            for record in records_to_delete:
                await self.session.delete(record)

            await self.save_changes()
            return len(records_to_delete)
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to delete records",
            ) from e

    async def exists(self, id: ID) -> bool:
        """
        Check if a record exists by ID.

        Args:
            id: The id of the record to check

        Returns:
            bool: True if the record exists, False otherwise
        """

        try:
            query = select(self.model).where(col(self.model.id) == id)  # type: ignore
            result = await self.session.exec(query)
            return result.one_or_none() is not None
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to check existence of record",
            ) from e

    async def exists_one(self) -> ModelType | None:
        """
        Check if at least one record exists.

        Returns:
            bool: True if at least one record exists, False otherwise
        """

        try:
            query = select(self.model)
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to check existence of record",
            ) from e

    async def execute_raw(self, query: Any, params: dict[str, Any] | None = None) -> Any:
        """
        Execute a raw SQL query.

        Args:
            query (Any): The raw SQL query to execute

        Returns:
            Any: The result of the query execution
        """

        try:
            result = await self.session.exec(query, params=params)  # type: ignore
            return result
        except SQLAlchemyError as e:
            raise DatabaseException(
                message="Failed to execute raw query",
            ) from e

    async def save_changes(self, refresh_obj=None):
        """
        Save changes to the database, respecting transaction context.

        If running within a transaction, just flush changes.
        If not in a transaction, commit changes.

        Args:
            refresh_obj: Object to refresh after saving changes
        """
        if in_transaction():
            await self.session.flush()
        else:
            await self.session.commit()

        if refresh_obj is not None:
            await self.session.refresh(refresh_obj)
