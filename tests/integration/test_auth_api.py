"""
Tests de Integración - API de Autenticación.
"""

from fastapi.testclient import TestClient

from idh.infrastructure.config import get_settings
from idh.main import app

settings = get_settings()

client = TestClient(app)


def test_get_token_success() -> None:
    """Verifica que se obtiene un token válido con credenciales correctas."""
    payload = {
        "client_id": settings.oauth2_client_id,
        "client_secret": settings.oauth2_client_secret,
    }
    response = client.post(f"{settings.api_v1_str}/token", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_get_token_invalid_credentials() -> None:
    """Verifica el rechazo (401) ante credenciales inválidas (ID o Secret)."""
    # Case 1: Both wrong
    payload = {"client_id": "wrong", "client_secret": "wrong"}
    response = client.post(f"{settings.api_v1_str}/token", json=payload)
    assert response.status_code == 401

    # Case 2: Correct ID, Wrong Secret
    payload = {"client_id": settings.oauth2_client_id, "client_secret": "wrong"}
    response = client.post(f"{settings.api_v1_str}/token", json=payload)
    assert response.status_code == 401

    # Case 3: Wrong ID, Correct Secret
    payload = {"client_id": "wrong", "client_secret": settings.oauth2_client_secret}
    response = client.post(f"{settings.api_v1_str}/token", json=payload)
    assert response.status_code == 401
