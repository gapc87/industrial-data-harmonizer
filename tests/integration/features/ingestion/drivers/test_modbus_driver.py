import logging
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus.pdu import ModbusPDU

from idh.features.ingestion.domain.exceptions import DriverConnectionError
from idh.features.ingestion.domain.models import TelemetryEvent
from idh.features.ingestion.infrastructure.drivers.modbus import ModbusDriver

"""
Tests de integración para el driver Modbus TCP.
"""


@pytest.fixture
def mock_modbus_client() -> Generator[AsyncMock, None, None]:
    """Fixture que proporciona un cliente Modbus mockeado."""
    with patch(
        "idh.features.ingestion.infrastructure.drivers.modbus.AsyncModbusTcpClient"
    ) as MockClient:
        client_instance = AsyncMock()
        client_instance.close = MagicMock()
        MockClient.return_value = client_instance
        yield client_instance


@pytest.mark.asyncio
async def test_modbus_connect_success(mock_modbus_client: AsyncMock) -> None:
    """Verifica que la conexión se establece correctamente."""
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=[])
    mock_modbus_client.connect.return_value = True

    await driver.connect()

    mock_modbus_client.connect.assert_called_once()
    assert driver.client == mock_modbus_client


@pytest.mark.asyncio
async def test_modbus_connect_failure(mock_modbus_client: AsyncMock) -> None:
    """Verifica que se lanza DriverConnectionError si falla la conexión."""
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=[])
    mock_modbus_client.connect.return_value = False

    with pytest.raises(DriverConnectionError):
        await driver.connect()

    mock_modbus_client.connect.side_effect = Exception("Connection refused")

    with pytest.raises(DriverConnectionError):
        await driver.connect()


@pytest.mark.asyncio
async def test_modbus_disconnect(mock_modbus_client: AsyncMock) -> None:
    """Verifica que la desconexión cierra el cliente correctamente."""
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=[])
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    await driver.disconnect()

    mock_modbus_client.close.assert_called_once()
    assert driver.client is None


@pytest.mark.asyncio
async def test_modbus_poll_success(mock_modbus_client: AsyncMock) -> None:
    """Verifica el sondeo exitoso de registros holding."""
    registers = [{"address": 100, "count": 1, "slave_id": 1, "type": "holding"}]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    read_response = MagicMock(spec=ModbusPDU)
    read_response.isError.return_value = False
    read_response.registers = [12345]
    mock_modbus_client.read_holding_registers.return_value = read_response

    events = []
    async for event in driver.poll():
        events.append(event)

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, TelemetryEvent)
    assert event.metadata.event_type == "modbus_telemetry"
    assert event.payload["register_address"] == 100
    assert event.payload["value"] == 12345
    assert event.payload["slave_id"] == 1


@pytest.mark.asyncio
async def test_modbus_poll_read_error_resilience(
    mock_modbus_client: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Verifica que errores de lectura lanzan excepción de conexión."""
    registers = [{"address": 100, "count": 1, "slave_id": 1, "type": "holding"}]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    mock_modbus_client.read_holding_registers.side_effect = Exception("Read timeout")

    with pytest.raises(DriverConnectionError, match="Modbus polling failed"):
        async for _ in driver.poll():
            pass

    assert "Connection error reading register" in caplog.text


@pytest.mark.asyncio
async def test_modbus_poll_read_error_response(
    mock_modbus_client: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Verifica el manejo de respuestas de error del dispositivo Modbus."""
    registers = [{"address": 100, "count": 1, "slave_id": 1, "type": "holding"}]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    read_response = MagicMock()
    read_response.isError.return_value = True
    mock_modbus_client.read_holding_registers.return_value = read_response

    events = []
    with caplog.at_level(logging.WARNING):
        async for event in driver.poll():
            events.append(event)

    assert len(events) == 0
    assert "Modbus error reading" in caplog.text


@pytest.mark.asyncio
async def test_modbus_poll_decoding(mock_modbus_client: AsyncMock) -> None:
    """Verifica la decodificación correcta de tipos de datos complejos (float32)."""
    import struct

    registers = [
        {
            "address": 200,
            "count": 2,
            "slave_id": 1,
            "type": "holding",
            "data_type": "float32",
        }
    ]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    packed = struct.pack(">f", 123.45)
    regs = [struct.unpack(">H", packed[0:2])[0], struct.unpack(">H", packed[2:4])[0]]

    read_response = MagicMock(spec=ModbusPDU)
    read_response.isError.return_value = False
    read_response.registers = regs
    mock_modbus_client.read_holding_registers.return_value = read_response

    events = []
    async for event in driver.poll():
        events.append(event)

    assert len(events) == 1
    event = events[0]
    assert event.payload["value"] == pytest.approx(123.45, 0.001)
