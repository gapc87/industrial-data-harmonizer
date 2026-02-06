"""
Tests de Integración - Seguridad de Autenticación.
"""

from fastapi.testclient import TestClient

from idh.infrastructure.config import get_settings
from idh.main import app

settings = get_settings()
client = TestClient(app)


def test_auth_failure_www_authenticate_header() -> None:
    """
    Estándar OAuth2: La respuesta 401 debe incluir la cabecera WWW-Authenticate.
    """
    payload = {"client_id": "wrong", "client_secret": "wrong"}
    response = client.post(f"{settings.api_v1_str}/token", json=payload)

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer"
