"""
Tests Unitarios - Configuración de la Aplicación.
"""

import pytest
from pydantic import ValidationError

from idh.infrastructure.config import Settings, get_settings

settings = get_settings()


def test_settings_load_from_env() -> None:
    """Prueba que la configuración se carga correctamente desde variables de entorno."""
    assert settings.secret_key is not None
    assert isinstance(settings.secret_key, str)
    assert len(settings.secret_key) > 0

    assert settings.oauth2_client_id is not None
    assert isinstance(settings.oauth2_client_id, str)

    assert settings.oauth2_client_secret is not None
    assert isinstance(settings.oauth2_client_secret, str)


def test_pydantic_validation() -> None:
    """Prueba que Pydantic valida la configuración."""
    assert hasattr(settings, "model_dump")


def test_missing_env_vars_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prueba que la falta de variables de entorno provoca un ValidationError."""
    # Necesitamos limpiar las variables esenciales.
    # Nota: secret_key, oauth2_client_id, mtls_cert_path son requeridos.
    # La configuración no distingue mayúsculas
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("OAUTH2_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH2_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MTLS_CERT_PATH", raising=False)

    # También se requiere la contraseña de Postgres en Settings
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    # Instanciar Settings sin archivo env para asegurar el fallo
    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    # Comprobar que campos específicos causaron el error de validación
    errors = excinfo.value.errors()
    failed_fields = [err["loc"][0] for err in errors]
    assert "secret_key" in failed_fields
    assert "oauth2_client_id" in failed_fields
    assert "oauth2_client_secret" in failed_fields
    assert "postgres_password" in failed_fields
