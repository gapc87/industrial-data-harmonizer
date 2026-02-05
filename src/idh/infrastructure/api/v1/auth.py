"""
Módulo de Autenticación.
"""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from idh.core.security.oauth2 import create_access_token
from idh.infrastructure.config import get_settings

router = APIRouter(tags=["Auth"])
settings = get_settings()


class ClientCredentialsRequest(BaseModel):
    """
    Esquema de solicitud para OAuth2 Client Credentials.
    """

    client_id: str
    client_secret: str


class Token(BaseModel):
    """
    Esquema de respuesta estándar OAuth2 con el token de acceso.
    """

    access_token: str
    token_type: str
    expires_in: int | None = None


@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: ClientCredentialsRequest) -> Token:
    """
    Endpoint para obtener un Token de Acceso (OAuth2 Client Credentials).

    Verifica las credenciales del cliente (ID y Secret) contra la configuración
    y devuelve un JWT firmado si son válidas.
    """
    import secrets

    # Use constant-time comparison to prevent timing attacks
    is_id_valid = secrets.compare_digest(
        credentials.client_id, settings.oauth2_client_id
    )
    is_secret_valid = secrets.compare_digest(
        credentials.client_secret, settings.oauth2_client_secret
    )

    if not (is_id_valid and is_secret_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client_id or client_secret",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

    # Store minimal info in token
    token_data = {"sub": credentials.client_id, "gateway_id": credentials.client_id}

    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )

    # AC: 3 ... and expires_in (usually in seconds for Oauth2 response)
    # The story says: "Then I receive a JWT with access_token and expires_in"

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )
