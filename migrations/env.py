"""
Entorno de migraciones Alembic.

Configura el contexto de migraciones para soportar ejecución asíncrona (AsyncIO)
y carga de configuración desde Pydantic Settings.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importar configuración de la aplicación
from idh.infrastructure.config import get_settings

# Importar el Base de SQLAlchemy para autogenerate
from idh.infrastructure.persistence.database import Base

# Alembic Config object
config = context.config

# Configurar logging desde el archivo ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Obtener URL de la base de datos desde Pydantic Settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Metadata para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Ejecutar migraciones en modo 'offline'.

    Genera SQL sin conectar a la base de datos.
    Útil para revisar el SQL antes de aplicar.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper para ejecutar migraciones con una conexión."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Ejecutar migraciones en modo async.

    Crea un engine async y ejecuta las migraciones dentro de una transacción.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Ejecutar migraciones en modo 'online'.

    Usa asyncio para manejar la conexión async.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
