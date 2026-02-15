"""Tests de integración para el buffer local Store & Forward (SQLite).

Valida: inicialización WAL, modelo BufferEntry, batching 2s,
retención 7 días, cleanup periódico y manejo de datos no sincronizados.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from idh.features.ingestion.domain.models import (
    TelemetryEvent,
    TelemetryMetadata,
)
from idh.features.ingestion.infrastructure.buffer.database import (
    Base,
    BufferEntry,
    create_buffer_engine,
    resolve_buffer_path,
)
from idh.features.ingestion.infrastructure.buffer.service import (
    BufferService,
)

_GATEWAY_ID = "11111111-1111-1111-1111-111111111111"


def _make_event(value: int = 42) -> TelemetryEvent:
    """Crea un TelemetryEvent de test con el valor indicado."""
    return TelemetryEvent(
        metadata=TelemetryMetadata(
            source_gateway_id=_GATEWAY_ID,
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="test_telemetry",
        ),
        payload={"sensor": "temp", "value": value},
    )


def _make_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Crea session factory para verificación directa en tests."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_path(tmp_path: Path) -> Path:
    """Ruta temporal para la base de datos de test."""
    return tmp_path / "test_buffer.db"


@pytest.fixture
async def buffer_service(
    db_path: Path,
) -> AsyncGenerator[BufferService, None]:
    """BufferService arrancado y con DB inicializada."""
    engine = create_buffer_engine(str(db_path))
    service = BufferService(engine)
    await service.start()
    yield service
    await service.stop()
    await engine.dispose()


@pytest.fixture
async def buffer_service_no_loop(
    db_path: Path,
) -> AsyncGenerator[BufferService, None]:
    """BufferService con DB lista pero SIN flush loop (control manual)."""
    engine = create_buffer_engine(str(db_path))
    service = BufferService(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield service
    await engine.dispose()


@pytest.mark.asyncio
async def test_wal_mode_enabled(db_path: Path) -> None:
    """WAL mode debe estar activo tras crear el engine."""
    engine = create_buffer_engine(str(db_path))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(text("PRAGMA journal_mode;"))
        mode = result.scalar()
        assert mode and mode.upper() == "WAL"

        result = await conn.execute(text("PRAGMA synchronous;"))
        sync_val = result.scalar()
        assert str(sync_val) in ("1", "NORMAL")
    await engine.dispose()


@pytest.mark.asyncio
async def test_buffer_entry_schema(db_path: Path) -> None:
    """El modelo BufferEntry debe persistir todos los campos."""
    engine = create_buffer_engine(str(db_path))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = _make_session_factory(engine)

    now = datetime.now(timezone.utc)
    entry = BufferEntry(
        event_data={"foo": "bar"},
        synced=False,
        created_at=now,
    )

    async with session_factory() as session:
        session.add(entry)
        await session.commit()

        row = (await session.execute(select(BufferEntry))).scalars().first()

    assert row is not None
    assert row.event_data == {"foo": "bar"}
    assert row.synced is False
    assert row.created_at is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_resolve_buffer_path_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin IDH_BUFFER_PATH usa la ruta por defecto."""
    monkeypatch.delenv("IDH_BUFFER_PATH", raising=False)
    path = resolve_buffer_path()
    assert path == "var/lib/idh/buffer.db"


@pytest.mark.asyncio
async def test_resolve_buffer_path_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """IDH_BUFFER_PATH sobreescribe la ruta por defecto."""
    custom = str(tmp_path / "custom" / "buffer.db")
    monkeypatch.setenv("IDH_BUFFER_PATH", custom)
    path = resolve_buffer_path()
    assert path == custom


@pytest.mark.asyncio
async def test_create_engine_creates_parent_dir(
    tmp_path: Path,
) -> None:
    """create_buffer_engine debe crear el directorio padre si no existe."""
    db_file = tmp_path / "subdir" / "nested" / "buffer.db"
    engine = create_buffer_engine(str(db_file))
    assert db_file.parent.is_dir()
    await engine.dispose()


@pytest.mark.asyncio
async def test_add_event_is_atomic(
    buffer_service: BufferService,
) -> None:
    """Un evento añadido y flusheado aparece en la DB."""
    ev = _make_event(99)
    await buffer_service.add_event(ev)
    await buffer_service.flush()

    total = await buffer_service.count_buffered()
    assert total == 1

    pending = await buffer_service.count_pending()
    assert pending == 1


@pytest.mark.asyncio
async def test_batching_not_written_immediately(
    buffer_service_no_loop: BufferService,
) -> None:
    """Los eventos NO deben aparecer en DB justo después de add_event."""
    svc = buffer_service_no_loop

    await svc.add_event(_make_event(1))
    await svc.add_event(_make_event(2))

    total = await svc.count_buffered()
    assert total == 0, "Los eventos se escribieron antes del flush"


@pytest.mark.asyncio
async def test_batching_written_after_flush(
    buffer_service: BufferService,
) -> None:
    """Tras flush explícito los eventos aparecen en la DB."""
    await buffer_service.add_event(_make_event(1))
    await buffer_service.add_event(_make_event(2))
    await buffer_service.flush()

    total = await buffer_service.count_buffered()
    assert total == 2


@pytest.mark.asyncio
async def test_flush_loop_writes_after_interval(
    db_path: Path,
) -> None:
    """El flush loop automático escribe tras ~2 s."""
    engine = create_buffer_engine(str(db_path))
    service = BufferService(engine)
    await service.start()

    await service.add_event(_make_event(10))

    await asyncio.sleep(2.5)

    total = await service.count_buffered()
    assert total == 1
    await service.stop()
    await engine.dispose()


@pytest.mark.asyncio
async def test_max_batch_triggers_flush(
    buffer_service_no_loop: BufferService,
) -> None:
    """Al alcanzar MAX_BATCH_SIZE se dispara flush inmediato."""
    svc = buffer_service_no_loop

    for i in range(100):
        await svc.add_event(_make_event(i))

    total = await svc.count_buffered()
    assert total == 100


@pytest.mark.asyncio
async def test_cleanup_deletes_old_events(
    buffer_service: BufferService,
    db_path: Path,
) -> None:
    """Registros con más de 7 días deben eliminarse."""
    old_date = datetime.now(timezone.utc) - timedelta(days=8)
    recent_date = datetime.now(timezone.utc)

    engine = create_buffer_engine(str(db_path))
    session_factory = _make_session_factory(engine)

    async with session_factory() as session:
        async with session.begin():
            session.add(
                BufferEntry(
                    event_data={"old": True},
                    synced=True,
                    created_at=old_date,
                )
            )
            session.add(
                BufferEntry(
                    event_data={"recent": True},
                    synced=False,
                    created_at=recent_date,
                )
            )
    await engine.dispose()

    await buffer_service.cleanup_old_events()

    total = await buffer_service.count_buffered()
    assert total == 1


@pytest.mark.asyncio
async def test_cleanup_warns_on_unsynced_deletion(
    buffer_service: BufferService,
    db_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Debe emitir WARNING al eliminar eventos no sincronizados."""
    old_date = datetime.now(timezone.utc) - timedelta(days=10)

    engine = create_buffer_engine(str(db_path))
    session_factory = _make_session_factory(engine)

    async with session_factory() as session:
        async with session.begin():
            session.add(
                BufferEntry(
                    event_data={"lost": True},
                    synced=False,
                    created_at=old_date,
                )
            )
    await engine.dispose()

    with caplog.at_level("WARNING"):
        await buffer_service.cleanup_old_events()

    assert any("NO sincronizados" in msg for msg in caplog.messages)


@pytest.mark.asyncio
async def test_cleanup_loop_is_started(
    buffer_service: BufferService,
) -> None:
    """El cleanup loop debe arrancarse al iniciar el servicio."""
    assert buffer_service._cleanup_task is not None
    assert not buffer_service._cleanup_task.done()
