"""
Configuración de la Aplicación - Pydantic Settings.

Centraliza todas las variables de entorno siguiendo la metodología 12-Factor App.
Validación estricta al arranque (Fail-Fast): si falta una variable requerida,
la aplicación no arranca.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación IDH."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    env_state: Literal["dev", "test", "prod"] = Field(
        default="dev",
        description="Entorno de ejecución: dev, test, prod",
    )
    project_name: str = Field(
        default="Industrial Data Harmonizer",
        description="Nombre del proyecto para Swagger UI",
    )
    api_v1_str: str = Field(
        default="/api/v1",
        description="Prefijo de la API v1",
    )
    secret_key: str = Field(
        ...,
        description="Clave secreta para firmar JWTs (requerida)",
        min_length=32,
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Tiempo de expiración de tokens JWT en minutos",
    )

    # --- PostgreSQL ---
    postgres_server: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="idh_admin")
    postgres_password: str = Field(...)
    postgres_db: str = Field(default="idh_dev")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión async para SQLAlchemy."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_server,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    # --- SAP Integration ---
    sap_api_base_url: str = Field(
        default="https://sandbox.api.sap.com/s4hana",
        description="URL base de la API OData de SAP",
    )
    sap_timeout_seconds: float = Field(
        default=5.0,
        description="Timeout para llamadas a SAP antes de abrir Circuit Breaker",
    )
    sap_auth_user: str | None = Field(default=None)
    sap_auth_pass: str | None = Field(default=None)

    # --- CORS ---
    backend_cors_origins: str = Field(
        default="http://localhost:8000,http://localhost:3000",
        description="Orígenes permitidos separados por coma",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Devuelve la lista de orígenes CORS."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    @property
    def is_production(self) -> bool:
        """Indica si el entorno es producción."""
        return self.env_state == "prod"


@lru_cache
def get_settings() -> Settings:
    """
    Singleton de configuración cacheado.

    Uso:
        from idh.infrastructure.config import get_settings
        settings = get_settings()
    """
    return Settings()
