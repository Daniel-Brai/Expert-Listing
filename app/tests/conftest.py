import os
from unittest.mock import patch

import pytest
import sqlalchemy
from bootstrap import create_app
from core.settings import settings
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import orm, text
from sqlalchemy.exc import ProgrammingError
from sqlmodel import Session, SQLModel, create_engine

patch.dict(
    os.environ,
    {
        "ENVIRONMENT": "staging",
        "APP_RUN_SEEDS": "true",
        "POSTGRES_DB": f"expert_listing_test_{os.environ.get('PYTEST_XDIST_WORKER', 'master')}",
    },
).start()  # noqa

engine = create_engine(url=str(settings.SQLALCHEMY_DATABASE_URI))
TestDBSession = orm.scoped_session(orm.sessionmaker(bind=engine, class_=Session))
TestDBSession.configure(bind=engine)


def client() -> TestClient:
    app = create_app()

    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def manage_test_database():
    connection_url = str(
        PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )
    )

    with sqlalchemy.create_engine(url=connection_url, isolation_level="AUTOCOMMIT").connect() as connection:
        try:
            connection.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
        except ProgrammingError:
            connection.execute(text(f"DROP DATABASE {settings.POSTGRES_DB}"))
            connection.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))

    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

    SQLModel.metadata.create_all(engine)

    yield

    with sqlalchemy.create_engine(url=connection_url, isolation_level="AUTOCOMMIT").connect() as connection:
        connection.execute(text(f"DROP DATABASE {settings.POSTGRES_DB} WITH (FORCE)"))
