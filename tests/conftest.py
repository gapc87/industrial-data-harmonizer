"""
Configuración global de Pytest.

Este archivo contiene fixtures compartidos entre tests unitarios e integración.
"""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer

from idh.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Backend para tests async (usado por pytest-asyncio)."""
    return "asyncio"


@pytest.fixture(scope="session")
def db_container() -> Generator[str, None, None]:
    """
    Inicia un contenedor de PostgreSQL para toda la sesión de pruebas.
    Retorna la URL de conexión (async).
    """
    postgres = PostgresContainer("postgres:15-alpine")
    postgres.start()

    url = postgres.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )

    yield url

    postgres.stop()


@pytest.fixture(scope="session")
async def test_engine(db_container: str) -> AsyncGenerator[AsyncEngine, None]:
    """Crea un motor SQLAlchemy conectado al contenedor de prueba."""
    engine = create_async_engine(db_container, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def patch_database_engine(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """
    Parchea globalmente el objeto 'engine' en el módulo de persistencia
    para que apunte al contenedor de Testcontainers en lugar de localhost.
    """
    with patch("idh.infrastructure.persistence.database.engine", test_engine):
        yield


@pytest.fixture(scope="session")
async def async_client(
    patch_database_engine: None,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP asíncrono para probar la API.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
