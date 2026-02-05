"""
Tests Unitarios - Disponibilidad del Entorno.
"""

import os


def test_uv_and_environment_readiness() -> None:
    """
    Verifica la preparación del entorno de desarrollo.
    """
    # Simply running this test proves the environment is set up successfully
    # enough to run pytest. We explicitly check some key markers.

    # 1. Check we are in a virtual environment
    is_virtual_env = os.environ.get("VIRTUAL_ENV") is not None
    assert is_virtual_env, "Test suite must run inside a virtual environment (uv .venv)"

    # 2. Check essential quality tools imports work (AC5/6 Check)
    import importlib.util

    assert importlib.util.find_spec("httpx") is not None
    assert importlib.util.find_spec("pydantic") is not None
    assert importlib.util.find_spec("pytest") is not None

    # 3. Check .env exists at root
    # En CI (GitHub Actions) no existe archivo .env, se inyectan variables.
    if not os.getenv("CI"):
        assert os.path.exists(".env"), "The .env file must exist as part of setup-env"
