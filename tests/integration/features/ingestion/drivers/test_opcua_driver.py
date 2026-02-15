"""
Tests de integración para el driver OPC UA.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from idh.features.ingestion.infrastructure.drivers.opcua import OpcUaDriver


@pytest.mark.asyncio
async def test_opcua_driver_connection_success() -> None:
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Test"]

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.connect = MagicMock(side_effect=lambda: None)
        from unittest.mock import AsyncMock

        mock_instance.connect = AsyncMock()
        mock_instance.disconnect = AsyncMock()

        driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)
        await driver.connect()

        mock_instance.connect.assert_called_once()

        await driver.disconnect()
        mock_instance.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_opcua_driver_connection_validation_partial_creds() -> None:
    """Prueba la lógica de validación."""
    driver = OpcUaDriver(
        endpoint_url="opc.tcp://localhost:4840",
        node_ids=[],
        username="admin",
        password=None,
    )

    with pytest.raises(ValueError, match="Both username and password must be provided"):
        await driver.connect()


@pytest.mark.asyncio
async def test_opcua_driver_poll_bulk_success() -> None:
    """Prueba el sondeo estándar con optimización por lotes."""
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Var1", "ns=1;s=Var2"]

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.connect = MagicMock()
        from unittest.mock import AsyncMock

        mock_instance.read_values = AsyncMock(return_value=[10.5, 20])

        driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)
        driver.client = mock_instance

        events = []
        async for event in driver.poll():
            events.append(event)

        assert len(events) == 2
        assert events[0].payload["value"] == 10.5
        assert events[1].payload["value"] == 20

        mock_instance.read_values.assert_called_once()


@pytest.mark.asyncio
async def test_opcua_driver_poll_fallback_resilience() -> None:
    """Prueba la recuperación a lectura secuencial cuando falla la lectura por lotes."""
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Good", "ns=1;s=Bad"]

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value

        mock_instance.read_values = AsyncMock(side_effect=Exception("Bulk read failed"))

        mock_node_good = MagicMock()
        mock_node_good.read_value = AsyncMock(return_value="GoodValue")

        mock_node_bad = MagicMock()
        mock_node_bad.read_value = AsyncMock(side_effect=Exception("Bad Node ID"))

        def get_node_side_effect(node_id: str) -> MagicMock:
            if node_id == "ns=1;s=Good":
                return mock_node_good
            return mock_node_bad

        mock_instance.get_node = MagicMock(side_effect=get_node_side_effect)

        driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)
        driver.client = mock_instance

        events = []
        async for event in driver.poll():
            events.append(event)

        assert len(events) == 1
        assert events[0].payload["node_id"] == "ns=1;s=Good"
        assert events[0].payload["value"] == "GoodValue"

        mock_instance.read_values.assert_called_once()
        assert mock_instance.get_node.call_count >= 2


@pytest.mark.asyncio
async def test_opcua_driver_serialization_safety() -> None:
    """Prueba la serialización del payload."""
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Complex"]

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value

        complex_obj = datetime(2023, 1, 1, 10, 0, 0)
        mock_instance.read_values = AsyncMock(return_value=[complex_obj])

        driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)
        driver.client = mock_instance

        events = []
        async for event in driver.poll():
            events.append(event)

        assert events[0].payload["value"] == complex_obj.isoformat()
