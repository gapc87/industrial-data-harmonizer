"""Tests unitarios para la lógica OAuth2."""

from datetime import timedelta

import pytest
from jose import JWTError, jwt

from idh.core.security.oauth2 import create_access_token, verify_token
from idh.infrastructure.config import get_settings

settings = get_settings()


def test_create_access_token() -> None:
    """Verifica la creación correcta de un access token firmado."""
    data = {"sub": "test_client", "gateway_id": "gw-123"}
    expires = timedelta(minutes=15)
    token = create_access_token(data, expires)

    assert token is not None
    assert isinstance(token, str)

    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "test_client"
    assert payload["gateway_id"] == "gw-123"
    assert "exp" in payload


def test_verify_token_valid() -> None:
    """Verifica que un token válido es decodificado correctamente."""
    data = {"sub": "test_client", "gateway_id": "gw-123"}
    token = create_access_token(data, timedelta(minutes=15))

    payload = verify_token(token)
    assert payload["sub"] == "test_client"
    assert payload["gateway_id"] == "gw-123"


def test_verify_token_invalid() -> None:
    """Verifica que se lanza JWTError ante un token corrupto o mal firmado."""
    with pytest.raises(JWTError):
        verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalid_signature")
