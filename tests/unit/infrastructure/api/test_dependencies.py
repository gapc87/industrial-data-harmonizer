"""
Tests unitarios de dependencias de API.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from idh.infrastructure.api.dependencies import get_current_gateway, require_auth


@pytest.mark.asyncio
async def test_get_current_gateway_valid_token() -> None:
    """Prueba la validación de un token válido."""
    # Parchear verify_token y extract_certificate_identity donde se CONFIGURAN
    with (
        patch("idh.infrastructure.api.dependencies.verify_token") as mock_verify,
        patch(
            "idh.infrastructure.api.dependencies.extract_certificate_identity"
        ) as mock_mtls,
    ):
        mock_verify.return_value = {"sub": "gateway-001", "exp": 1234567890}
        mock_mtls.return_value = None  # Sin identidad mTLS para este caso de prueba

        token = "valid_token"
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        gateway = await get_current_gateway(creds, request)

        assert gateway.id == "gateway-001"
        mock_verify.assert_called_once_with(token)


@pytest.mark.asyncio
async def test_get_current_gateway_invalid_token() -> None:
    """Prueba que un token inválido lance 401."""
    with patch("idh.infrastructure.api.dependencies.verify_token") as mock_verify:
        from jose import JWTError

        mock_verify.side_effect = JWTError("Invalid token")

        token = "invalid_token"
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        with pytest.raises(HTTPException) as exc:
            await get_current_gateway(creds, request)

        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_gateway_mtls_mismatch() -> None:
    """Prueba que se registre advertencia si hay discrepancia mTLS."""
    with (
        patch("idh.infrastructure.api.dependencies.verify_token") as mock_verify,
        patch(
            "idh.infrastructure.api.dependencies.extract_certificate_identity"
        ) as mock_mtls,
        patch("idh.infrastructure.api.dependencies.logger") as mock_logger,
    ):
        mock_verify.return_value = {"sub": "gateway-001", "exp": 1234567890}
        mock_mtls.return_value = "gateway-002"  # Discrepancia

        token = "valid_token"
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        gateway = await get_current_gateway(creds, request)

        assert gateway.id == "gateway-001"
        mock_mtls.assert_called_once_with(request)
        mock_logger.warning.assert_called_with(
            "auth_mtls_mismatch", jwt_sub="gateway-001", mtls_cn="gateway-002"
        )


@pytest.mark.asyncio
async def test_get_current_gateway_validation_error() -> None:
    """Prueba error de validación cuando el payload es incorrecto."""
    with patch("idh.infrastructure.api.dependencies.verify_token") as mock_verify:
        # Payload sin 'sub' dispara ValidationError de Pydantic
        mock_verify.return_value = {"foo": "bar"}

        token = "token_with_invalid_payload"
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        with pytest.raises(HTTPException) as exc:
            await get_current_gateway(creds, request)

        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_auth() -> None:
    """Prueba simple para asegurar que require_auth devuelve la identidad."""
    # Prueba simple para asegurar que require_auth pasa la identidad del gateway
    gateway_mock = Mock()
    result = await require_auth(gateway_mock)
    assert result == gateway_mock
