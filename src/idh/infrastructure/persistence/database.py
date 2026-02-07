"""
Módulo de Persistencia - SQLAlchemy Async.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from idh.infrastructure.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.env_state == "dev",
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base para modelos ORM (SQLAlchemy 2.0 style)."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    Dependency Injection para FastAPI.
    Provee una sesión de base de datos transaccional por petición.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
