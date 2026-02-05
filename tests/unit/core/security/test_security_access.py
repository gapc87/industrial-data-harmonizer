"""
Tests Unitarios - Acceso a Configuración de Seguridad.
"""

from idh.infrastructure.config import get_settings


def test_security_settings_are_accessible_via_get_settings() -> None:
    """
    Dado que el proyecto está inicializado
    Cuando importo/accedo a settings (vía get_settings singleton)
    Entonces puedo acceder a JWT_SECRET, OAUTH2_CLIENT_ID, MTLS_CERT_PATH
    """
    settings = get_settings()

    assert hasattr(settings, "secret_key")
    assert hasattr(settings, "oauth2_client_id")
    assert hasattr(settings, "mtls_cert_path")
    assert hasattr(settings, "oauth2_client_secret")

    assert settings.secret_key is not None
    assert settings.oauth2_client_id is not None
    assert settings.mtls_cert_path is not None
