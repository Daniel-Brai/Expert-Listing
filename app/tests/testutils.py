from unittest import TestCase
from unittest.async_case import IsolatedAsyncioTestCase

from database import get_db_session
from sqlalchemy.orm import close_all_sessions
from sqlmodel import Session, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .conftest import TestDBSession, engine


class CustomDBTestCase(TestCase):
    session: Session

    def setUp(self) -> None:
        self.setUpClass()

    def tearDown(self) -> None:
        self.tearDownClass()

    @classmethod
    def _clear_database(cls) -> None:
        with engine.connect() as connection:
            for table in reversed(SQLModel.metadata.sorted_tables):
                connection.execute(table.delete())
                connection.commit()

    @classmethod
    def setUpClass(cls) -> None:
        close_all_sessions()
        cls.session = TestDBSession()

    @classmethod
    def tearDownClass(cls) -> None:
        close_all_sessions()
        cls._clear_database()


class AsyncCustomDBTestCase(CustomDBTestCase, IsolatedAsyncioTestCase):
    async_db_session: AsyncSession

    async def asyncSetUp(self):
        self.async_db_session = await anext(get_db_session())

    async def asyncTearDown(self):
        await self.async_db_session.close()
        close_all_sessions()
