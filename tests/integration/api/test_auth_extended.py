"""
Tests Extendidos de Autenticación.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt

from idh.infrastructure.api.dependencies import require_auth
from idh.infrastructure.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"
SECRET_KEY = settings.secret_key


def create_token(data: dict[str, Any]) -> str:
    """Genera un token JWT firmado para pruebas."""
    return str(jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM))


# --- Configuración de App de Prueba ---
@pytest.fixture
async def protected_client() -> AsyncGenerator[AsyncClient, None]:
    """Configura una app FastAPI temporal con una ruta protegida para pruebas."""
    test_app = FastAPI()

    @test_app.get("/protected", dependencies=[Depends(require_auth)])
    async def protected_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_auth_nbf_future(protected_client: AsyncClient) -> None:
    """Prueba token con claim nbf (Not Before) en el futuro."""
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    future_ts = future.timestamp()
    exp_ts = (future + timedelta(minutes=10)).timestamp()
    token = create_token({"sub": "future-user", "nbf": future_ts, "exp": exp_ts})

    response = await protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {token}"}
    )

    # Debería ser no autorizado porque nbf está en el futuro
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_malformed_header(protected_client: AsyncClient) -> None:
    """Prueba cabeceras de autorización mal formadas."""
    token = create_token({"sub": "user"})

    # Falta prefijo Bearer
    response = await protected_client.get(
        "/protected", headers={"Authorization": token}
    )
    assert response.status_code in [401, 403]

    # Esquema incorrecto
    response = await protected_client.get(
        "/protected", headers={"Authorization": f"Basic {token}"}
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_auth_missing_sub(protected_client: AsyncClient) -> None:
    """Prueba token al que le falta el claim subject."""
    exp_ts = (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()
    token = create_token({"exp": exp_ts})
    response = await protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
