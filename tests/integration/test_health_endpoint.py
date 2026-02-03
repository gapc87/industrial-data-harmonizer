"""
Tests de integración para el endpoint de health check.
"""

import pytest


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests para /api/v1/health."""

    async def test_health_returns_ok(self, async_client) -> None:
        """El endpoint de health debe devolver status ok."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "idh-api"

    async def test_readiness_returns_ok(self, async_client) -> None:
        """El endpoint de readiness debe devolver estado de dependencias."""
        response = await async_client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "sap_connection" in data
        # Verificamos que la base de datos esté conectada (gracias a Testcontainers)
        assert data["database"] == "connected"


@pytest.mark.asyncio
class TestRootEndpoint:
    """Tests para endpoint raíz."""

    async def test_root_returns_system_online(self, async_client) -> None:
        """El endpoint raíz debe indicar que el sistema está online."""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
