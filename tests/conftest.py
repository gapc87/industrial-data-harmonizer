"""
Configuración global de Pytest.

Este archivo contiene fixtures compartidos entre tests unitarios e integración.
"""

import re
import time
from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
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
def opc_plc_container() -> Generator[str, None, None]:
    """
    Inicia un contenedor de OPC UA Simulator (iotechsys) para tests E2E.
    Retorna la URL de conexión (opc.tcp://localhost:port).
    """
    # Usamos iotechsys/opc-ua-sim para mayor simplicidad
    opc = DockerContainer("iotechsys/opc-ua-sim:1.2")

    # Usamos red host para simplificar (solo Linux)
    opc.with_kwargs(network_mode="host")

    opc.start()

    opc.waiting_for(LogMessageWaitStrategy("TCP network layer listening on opc.tcp://"))
    time.sleep(2)  # Pequeña pausa extra para asegurar

    logs = opc.get_logs()
    stdout = logs[0].decode("utf-8") if isinstance(logs, tuple) else str(logs)

    # Buscamos algo como: opc.tcp://<hostname>:<port>/
    match = re.search(r"opc\.tcp://[^:]+:(\d+)/", stdout)
    if not match:
        opc.stop()
        raise RuntimeError(f"Could not find OPC UA port in logs: {stdout}")

    port = match.group(1)
    host = "localhost"
    url = f"opc.tcp://{host}:{port}"

    yield url

    opc.stop()


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
