from typing import Any, MutableMapping
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from httpx import ASGITransport, AsyncClient

from idh.core.security.mtls import extract_certificate_identity

app = FastAPI()


async def get_gateway_id(request: Request) -> str:
    identity = extract_certificate_identity(request)
    if not identity:
        raise HTTPException(status_code=403, detail="Client certificate required")
    return identity


@app.get("/secure-resource")
async def secure_resource(gateway_id: str = Depends(get_gateway_id)) -> dict[str, str]:
    return {"message": f"Hello {gateway_id}"}


@pytest.mark.asyncio
async def test_mtls_integration_success() -> None:
    """Verifica el flujo completo con un certificado simualdo en el scope."""
    ssl_object = MagicMock()
    ssl_object.getpeercert.return_value = {
        "subject": ((("commonName", "gateway-integration-test"),),)
    }

    # Simular el transporte ASGI que incluya el SSL en el scope
    async def mock_app(
        scope: MutableMapping[str, Any], receive: Any, send: Any
    ) -> None:
        if scope["type"] == "http":
            scope["extensions"] = {"ssl": ssl_object}
        await app(scope, receive, send)

    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello gateway-integration-test"}


@pytest.mark.asyncio
async def test_mtls_integration_no_cert() -> None:
    """Verifica que falla si no hay certificado."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource")

    assert response.status_code == 403
    assert response.json()["detail"] == "Client certificate required"


@pytest.mark.asyncio
async def test_mtls_integration_invalid_cert() -> None:
    """Verifica que falla si el certificado no tiene CommonName."""
    ssl_object = MagicMock()
    # Certificado sin subject o sin CN
    ssl_object.getpeercert.return_value = {"subject": ()}

    async def mock_app(
        scope: MutableMapping[str, Any], receive: Any, send: Any
    ) -> None:
        if scope["type"] == "http":
            scope["extensions"] = {"ssl": ssl_object}
        await app(scope, receive, send)

    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource")

    assert response.status_code == 403
    assert response.json()["detail"] == "Client certificate required"


@pytest.mark.asyncio
async def test_mtls_integration_xfcc_success() -> None:
    """Verifica el flujo usando el header XFCC (simulando terminación en proxy)."""
    xfcc_header = 'By=...;Hash=...;Subject="CN=gateway-proxy";URI=...'
    headers = {"x-forwarded-client-cert": xfcc_header}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message": "Hello gateway-proxy"}
