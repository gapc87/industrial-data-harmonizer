"""
Logging Estructurado con Structlog.

Configura el logging según el entorno:
- dev: Logs legibles en consola con colores
- prod: Logs en formato JSON para ingesta por ELK/Datadog

Uso:
    from idh.infrastructure.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Mensaje", extra_field="valor")
"""

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from idh.infrastructure.config import Settings


def setup_logging(settings: "Settings") -> None:
    """
    Configura el logging estructurado según el entorno.

    Args:
        settings: Configuración de la aplicación
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_production:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )
        )

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtiene un logger estructurado.

    Args:
        name: Nombre del módulo (típicamente __name__)

    Returns:
        Logger estructurado configurado
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
