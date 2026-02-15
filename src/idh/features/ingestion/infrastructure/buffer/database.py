"""Infraestructura de persistencia SQLite para buffer local.

Configura el motor async con WAL mode y define el modelo
BufferEntry para la tabla telemetry_buffer.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, DateTime, Integer, event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)

DEFAULT_BUFFER_PATH = "var/lib/idh/buffer.db"


class Base(DeclarativeBase):
    """Base declarativa para modelos del buffer local."""

    pass


class BufferEntry(Base):
    """Modelo para almacenar eventos de telemetría en buffer local.

    Corresponde a la tabla ``telemetry_buffer``.
    """

    __tablename__ = "telemetry_buffer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def _setup_sqlite_optimizations(
    dbapi_connection: Any,
    connection_record: Any,
) -> None:
    """Activa WAL mode y synchronous=NORMAL para concurrencia y flash."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()


def resolve_buffer_path() -> str:
    """Resuelve la ruta del buffer desde IDH_BUFFER_PATH o el default.

    Solo resuelve la ruta, no crea directorios. La creación de
    directorios se realiza en ``create_buffer_engine``.
    """
    return os.environ.get("IDH_BUFFER_PATH", DEFAULT_BUFFER_PATH)


def create_buffer_engine(db_path: str | None = None) -> AsyncEngine:
    """Crea AsyncEngine para el buffer local con WAL habilitado.

    Si ``db_path`` es None, resuelve la ruta desde la variable de
    entorno ``IDH_BUFFER_PATH`` o usa el default. Crea el directorio
    padre si no existe.

    Argumentos:
        db_path: Ruta al fichero SQLite.
    """
    if db_path is None:
        db_path = resolve_buffer_path()

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)

    event.listen(engine.sync_engine, "connect", _setup_sqlite_optimizations)

    return engine
