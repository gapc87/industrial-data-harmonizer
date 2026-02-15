"""
Tests unitarios para los puertos (interfaces) de ingestión.
"""

import inspect
from abc import ABC

import pytest


def test_ingestion_driver_interface_exists() -> None:
    """Test that IngestionDriver interface exists and is an ABC"""
    try:
        from idh.features.ingestion.domain.ports import IngestionDriver
    except ImportError:
        pytest.fail(
            "Could not import IngestionDriver from idh.features.ingestion.domain.ports"
        )

    assert issubclass(IngestionDriver, ABC)


def test_ingestion_driver_methods() -> None:
    """Test that IngestionDriver has the required abstract methods"""
    from idh.features.ingestion.domain.ports import IngestionDriver

    required_methods = ["connect", "disconnect", "poll"]

    for method in required_methods:
        assert hasattr(IngestionDriver, method), (
            f"IngestionDriver missing method: {method}"
        )
        method_obj = getattr(IngestionDriver, method)
        assert method_obj.__isabstractmethod__, f"Method {method} should be abstract"
        assert inspect.isfunction(method_obj) or inspect.ismethod(method_obj)
