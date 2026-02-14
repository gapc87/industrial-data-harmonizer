"""
Tests de Integración de Autenticación.
"""

from unittest.mock import patch

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from idh.core.domain.models.security import GatewayIdentity
from idh.infrastructure.api.dependencies import get_current_gateway


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    router = APIRouter()

    @router.get("/protected")
    async def protected_route(
        gateway: GatewayIdentity = Depends(get_current_gateway),  # noqa: B008
    ) -> dict[str, str]:
        return {"id": gateway.id}

    app.include_router(router)
    return TestClient(app)


def test_auth_missing_header(client: TestClient) -> None:
    """Verifica rechazo 401 cuando falta la cabecera de autorización."""
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_auth_valid_token(client: TestClient) -> None:
    """Verifica autenticación exitosa con token válido mockeado."""

    with (
        patch("idh.infrastructure.api.dependencies.verify_token") as mock_verify,
        patch(
            "idh.infrastructure.api.dependencies.extract_certificate_identity"
        ) as mock_mtls,
    ):
        mock_verify.return_value = {"sub": "gateway-integration", "exp": 1234567890}
        mock_mtls.return_value = None

        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/protected", headers=headers)

        assert response.status_code == 200
        assert response.json() == {"id": "gateway-integration"}
