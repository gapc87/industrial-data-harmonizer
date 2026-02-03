"""
Industrial Data Harmonizer - Application Factory.

Punto de entrada principal de la aplicación FastAPI.
Utiliza el patrón Application Factory para configuración modular.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from idh.infrastructure.api.v1.health import router as health_router
from idh.infrastructure.config import get_settings
from idh.infrastructure.logging import get_logger, setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona el ciclo de vida de la aplicación.

    Startup: Inicializa conexiones, logging, etc.
    Shutdown: Cierra conexiones limpiamente (Graceful Shutdown).
    """
    logger = get_logger(__name__)

    setup_logging(settings)
    logger.info(
        "Sistema IDH arrancando",
        environment=settings.env_state,
        log_level=settings.log_level,
    )

    # TODO: Inicializar pool de conexiones a PostgreSQL
    # TODO: Inicializar cliente SAP con Circuit Breaker

    yield

    logger.info("Sistema IDH deteniéndose - Graceful Shutdown iniciado")
    # TODO: Cerrar pool de conexiones a PostgreSQL
    # TODO: Cerrar conexiones HTTP pendientes


def create_app() -> FastAPI:
    """
    Factory de la aplicación FastAPI.

    Returns:
        Instancia configurada de FastAPI
    """
    application = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- Middlewares ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    application.include_router(health_router, prefix=settings.api_v1_str)

    # Root endpoint
    @application.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Endpoint raíz para verificación básica."""
        return {"msg": "IDH System Online", "status": "running"}

    return application


app = create_app()
