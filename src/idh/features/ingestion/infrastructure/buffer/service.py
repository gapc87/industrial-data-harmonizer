"""Servicio de buffer local Store & Forward para telemetría.

Acumula TelemetryEvents en memoria y los escribe en lotes a SQLite
cada 2 segundos (NFR-04 - protección de flash/eMMC en PCs industriales).
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from idh.features.ingestion.domain.models import TelemetryEvent

from .database import Base, BufferEntry

logger = logging.getLogger(__name__)

FLUSH_INTERVAL_SECONDS: float = 2.0
MAX_BATCH_SIZE: int = 100
RETENTION_DAYS: int = 7
CLEANUP_INTERVAL_SECONDS: float = 3600.0  # 1 hora


class BufferService:
    """Servicio de buffer local con batching y retención.

    Acumula eventos en memoria y los vuelca a SQLite en lotes para
    minimizar las escrituras a disco (flash endurance, NFR-04).
    """

    def __init__(self, engine: AsyncEngine) -> None:
        """Inicializa el servicio con el motor de base de datos indicado."""
        self._engine = engine
        self._session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._pending: List[TelemetryEvent] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Inicializa la base de datos y arranca flush loop + cleanup loop."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("BufferService iniciado")

    async def stop(self) -> None:
        """Detiene los loops y vuelca eventos pendientes."""
        for task in (self._flush_task, self._cleanup_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await self.flush()
        logger.info("BufferService detenido")

    async def add_event(self, event: TelemetryEvent) -> None:
        """Encola un evento para escritura en el siguiente batch."""
        should_flush = False
        async with self._lock:
            self._pending.append(event)
            if len(self._pending) >= MAX_BATCH_SIZE:
                should_flush = True

        if should_flush:
            await self.flush()

    async def flush(self) -> None:
        """Vuelca los eventos pendientes a SQLite en una sola transacción."""
        async with self._lock:
            if not self._pending:
                return
            batch = self._pending.copy()
            self._pending.clear()

        entries = [
            BufferEntry(
                event_data=ev.model_dump(mode="json"),
                created_at=datetime.now(timezone.utc),
                synced=False,
            )
            for ev in batch
        ]

        async with self._session_factory() as session:
            async with session.begin():
                session.add_all(entries)
        logger.debug("Flush completado: %d eventos escritos", len(entries))

    async def cleanup_old_events(self) -> None:
        """Elimina registros con más de RETENTION_DAYS días de antigüedad."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        async with self._session_factory() as session:
            unsynced_stmt = select(func.count()).select_from(
                select(BufferEntry)
                .where(BufferEntry.created_at < cutoff)
                .where(BufferEntry.synced.is_(False))
                .subquery()
            )
            result = await session.execute(unsynced_stmt)
            unsynced_count: int = result.scalar() or 0

        if unsynced_count > 0:
            logger.warning(
                "Se eliminarán %d eventos NO sincronizados (posible pérdida de datos)",
                unsynced_count,
            )

        async with self._session_factory() as session:
            async with session.begin():
                stmt = delete(BufferEntry).where(BufferEntry.created_at < cutoff)
                result = await session.execute(stmt)
                deleted = result.rowcount  # type: ignore[attr-defined]

        logger.info(
            "Limpieza completada: %d registros eliminados (cutoff=%s)",
            deleted,
            cutoff.isoformat(),
        )

    async def count_buffered(self) -> int:
        """Devuelve el total de eventos almacenados en buffer."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(BufferEntry)
            )
            return result.scalar() or 0

    async def count_pending(self) -> int:
        """Devuelve el total de eventos pendientes (no sincronizados)."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count())
                .select_from(BufferEntry)
                .where(BufferEntry.synced.is_(False))
            )
            return result.scalar() or 0

    async def _flush_loop(self) -> None:
        """Bucle que ejecuta flush cada FLUSH_INTERVAL_SECONDS."""
        while True:
            await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
            try:
                await self.flush()
            except Exception:
                logger.exception("Error en flush loop")

    async def _cleanup_loop(self) -> None:
        """Bucle que ejecuta cleanup cada CLEANUP_INTERVAL_SECONDS (1h)."""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            try:
                await self.cleanup_old_events()
            except Exception:
                logger.exception("Error en cleanup loop")
