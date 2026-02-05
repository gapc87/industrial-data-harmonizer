from idh.infrastructure.config import Settings


def test_mtls_settings_exist():
    """Verifica que las configuraciones de mTLS existan en Settings."""
    # Esto fallará si los atributos no están definidos en la clase Settings
    settings = Settings(
        secret_key="x" * 32,
        oauth2_client_id="id",
        oauth2_client_secret="s" * 32,
        postgres_password="pass",
        mtls_cert_path="./certs/client.crt",
        mtls_enabled=True,
        mtls_ca_path="./certs/ca.crt",
        mtls_key_path="./certs/client.key",
    )
    assert settings.mtls_enabled is True
    assert settings.mtls_ca_path == "./certs/ca.crt"
    assert settings.mtls_cert_path == "./certs/client.crt"
    assert settings.mtls_key_path == "./certs/client.key"
