from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import ValidationError
from structlog import get_logger

from idh.core.domain.models.security import GatewayIdentity
from idh.core.security.mtls import extract_certificate_identity
from idh.core.security.oauth2 import verify_token

logger = get_logger()

# Auto-error=True hace que FastAPI devuelva automáticamente 401 si falta la cabecera
oauth2_scheme = HTTPBearer(auto_error=True)


async def get_current_gateway(
    token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    request: Request,
) -> GatewayIdentity:
    """
    Valida el token JWT y devuelve la identidad del Gateway.

    También realiza una comprobación opcional de mTLS y
    registra advertencias si hay discrepancias.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token.credentials)
        if payload is None:
            raise credentials_exception

        # Validar que la carga útil coincide con nuestro modelo de Identidad
        # Se asume que 'sub' contiene el ID del gateway
        identity = GatewayIdentity(**payload)

        # Comprobación opcional de mTLS
        mtls_identity = extract_certificate_identity(request)
        if mtls_identity:
            if mtls_identity != identity.id:
                logger.warning(
                    "auth_mtls_mismatch", jwt_sub=identity.id, mtls_cn=mtls_identity
                )
            else:
                logger.debug("auth_mtls_match", gateway_id=identity.id)

        # Establecer la identidad en el estado de la solicitud
        request.state.gateway = identity
        request.state.user = identity

        logger.info("auth_success", gateway_id=identity.id)

        return identity
    except (JWTError, ValidationError) as e:
        logger.warning("auth_failed", reason="invalid_token_or_payload", error=str(e))
        raise credentials_exception from e
    except Exception as e:
        logger.error("auth_failed_unexpected", reason=str(e))
        raise credentials_exception from e


async def require_auth(
    gateway: Annotated[GatewayIdentity, Depends(get_current_gateway)],
) -> GatewayIdentity:
    """
    Dependencia para forzar la autenticación simple.

    Se puede usar como dependencies=[Depends(require_auth)] en routers.
    """
    return gateway
