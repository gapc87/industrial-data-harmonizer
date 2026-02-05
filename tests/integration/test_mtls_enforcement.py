from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from httpx import ASGITransport, AsyncClient

from idh.core.security.mtls import extract_certificate_identity

# Definir una app de test local para asegurar que el endpoint existe
test_app = FastAPI()


async def get_gateway_id(request: Request):
    identity = extract_certificate_identity(request)
    if not identity:
        raise HTTPException(status_code=403, detail="Client certificate required")
    return identity


@test_app.get("/secure-resource")
async def secure_resource(gateway_id: str = Depends(get_gateway_id)):
    return {"message": f"Hello {gateway_id}"}


@pytest.mark.asyncio
async def test_mtls_enforcement_lifecycle():
    """Simula el ciclo de vida completo de una sesión mTLS. [P0]"""
    # 1. Intento sin certificado -> 403
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource")
    assert response.status_code == 403

    # 2. Intento con certificado válido (simulado)
    ssl_object = MagicMock()
    ssl_object.getpeercert.return_value = {
        "subject": ((("commonName", "edge-gateway-001"),),)
    }

    async def mock_app_with_ssl(scope, receive, send):
        if scope["type"] == "http":
            scope["extensions"] = {"ssl": ssl_object}
        await test_app(scope, receive, send)

    transport_ssl = ASGITransport(app=mock_app_with_ssl)
    async with AsyncClient(transport=transport_ssl, base_url="https://test") as ac:
        response = await ac.get("/secure-resource")

    assert response.status_code == 200
    assert response.json()["message"] == "Hello edge-gateway-001"

    # 3. Intento con header XFCC (simulando proxy)
    headers = {"x-forwarded-client-cert": 'Subject="CN=proxy-gateway"'}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/secure-resource", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Hello proxy-gateway"
