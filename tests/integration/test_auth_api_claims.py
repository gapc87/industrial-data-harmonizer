"""
Tests de Integración - Claims del Token JWT.
"""

from fastapi.testclient import TestClient
from jose import jwt

from idh.core.security.oauth2 import ALGORITHM
from idh.infrastructure.config import get_settings
from idh.main import app

settings = get_settings()
client = TestClient(app)


def test_get_token_verifies_gateway_id_claim() -> None:
    """
    Verifica que el token incluye el claim `gateway_id`.
    """
    payload = {
        "client_id": settings.oauth2_client_id,
        "client_secret": settings.oauth2_client_secret,
    }
    response = client.post(f"{settings.api_v1_str}/token", json=payload)
    assert response.status_code == 200

    data = response.json()
    access_token = data.get("access_token")
    assert access_token is not None

    # Decodificar el token para verificar claims
    # La backend ya validó la firma al generarlo, aquí verificamos
    # que se hayan incluido los datos correctos.

    decoded_payload = jwt.decode(
        access_token, settings.secret_key, algorithms=[ALGORITHM]
    )

    assert "gateway_id" in decoded_payload
    assert decoded_payload["gateway_id"] == settings.oauth2_client_id
