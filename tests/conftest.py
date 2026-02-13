"""
Configuración global de Pytest.

Este archivo contiene fixtures compartidos entre tests unitarios e integración.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer

from idh.main import app


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """
    Hook para marcar automáticamente tests basándose en su ubicación.

    - tests/unit/* -> unit
    - tests/integration/* -> integration
    - tests/e2e/* -> e2e
    """
    for item in items:
        # Convert path to string for reliable substring check
        path_str = str(item.path)

        if "tests/unit" in path_str:
            item.add_marker(pytest.mark.unit)
        elif "tests/integration" in path_str:
            item.add_marker(pytest.mark.integration)
        elif "tests/e2e" in path_str:
            item.add_marker(pytest.mark.e2e)


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
async def opc_plc_container() -> AsyncGenerator[str, None]:
    """
    Inicia un servidor OPC UA local (usando asyncua) para tests E2E.
    Retorna la URL de conexión (opc.tcp://localhost:port).

    Reemplaza la imagen de Docker flaky por un servidor en proceso.
    """
    from asyncua import Server

    server = Server()
    await server.init()

    # Usamos puerto 8555 o uno dinámico si falla
    endpoint = "opc.tcp://0.0.0.0:8555/freeopcua/server/"
    server.set_endpoint(endpoint)
    server.set_server_name("FreeOpcUa Example Server")

    # Configurar namespace y nodos básicos
    idx = await server.register_namespace("http://examples.freeopcua.github.io")
    ts_node = await server.nodes.objects.add_object(idx, "MyObject")
    await ts_node.add_variable(idx, "MyVariable", 6.7)

    # Iniciar servidor
    async with server:
        # Dar tiempo para que el endpoint esté activo
        await asyncio.sleep(1.0)
        yield "opc.tcp://127.0.0.1:8555/freeopcua/server/"


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
