"""
Lógica de autenticación OAuth2 con JWT.

Proporciona funciones para crear y verificar tokens JWT firmados
utilizando el algoritmo HS256.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from idh.infrastructure.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"


def create_access_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """
    Crea un JSON Web Token (JWT) firmado.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verifica la firma de un token y decodifica su contenido.
    Lanza JWTError si es inválido.
    """
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[ALGORITHM]
    )
    return payload
