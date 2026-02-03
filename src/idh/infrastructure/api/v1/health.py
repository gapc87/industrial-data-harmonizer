"""
Health Check Endpoints.

Endpoints para monitoreo y orquestación de contenedores:
- /health: Liveness probe (¿el proceso está vivo?)
- /health/ready: Readiness probe (¿puede recibir tráfico?)
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Respuesta del health check."""

    status: str
    service: str = "idh-api"


class ReadinessResponse(BaseModel):
    """Respuesta del readiness check."""

    status: str
    database: str
    sap_connection: str


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Verifica que el proceso de la API está corriendo.",
)
async def health_check() -> HealthResponse:
    """Endpoint básico de liveness para orquestadores (K8s, Docker)."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Verifica que el sistema puede atender peticiones.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Endpoint de readiness que verifica dependencias críticas.
    """
    db_status = "disconnected"
    try:
        from sqlalchemy import text

        from idh.infrastructure.persistence.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:  # pylint: disable=broad-except
        db_status = "disconnected"

    # TODO: Verificar conectividad a SAP (ping)
    return ReadinessResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        sap_connection="unknown",
    )
