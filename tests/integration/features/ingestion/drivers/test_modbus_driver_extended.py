"""
Tests extendidos para el driver Modbus TCP (casos borde y tipos de datos).
"""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus.pdu import ModbusPDU

from idh.features.ingestion.infrastructure.drivers.modbus import ModbusDriver


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
async def test_modbus_poll_input_registers(mock_modbus_client: AsyncMock) -> None:
    """[P1] Verifica la lectura de registros de entrada (Input Registers)."""
    registers = [{"address": 300, "count": 1, "slave_id": 1, "type": "input"}]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    read_response = MagicMock(spec=ModbusPDU)
    read_response.isError.return_value = False
    read_response.registers = [54321]
    mock_modbus_client.read_input_registers.return_value = read_response

    events = []
    async for event in driver.poll():
        events.append(event)

    mock_modbus_client.read_input_registers.assert_called_once_with(
        address=300, count=1, device_id=1
    )
    assert len(events) == 1
    assert events[0].payload["value"] == 54321


@pytest.mark.asyncio
async def test_modbus_decode_int16(mock_modbus_client: AsyncMock) -> None:
    """[P1] Verifica la decodificación de enteros con signo (int16)."""
    registers = [
        {
            "address": 400,
            "count": 1,
            "slave_id": 1,
            "type": "holding",
            "data_type": "int16",
        }
    ]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    read_response = MagicMock(spec=ModbusPDU)
    read_response.isError.return_value = False
    read_response.registers = [40000]
    mock_modbus_client.read_holding_registers.return_value = read_response

    events = []
    async for event in driver.poll():
        events.append(event)

    assert len(events) == 1
    assert events[0].payload["value"] == -25536


@pytest.mark.asyncio
async def test_modbus_decode_float32_insufficient_registers(
    mock_modbus_client: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """[P2] Verifica el manejo de registros insuficientes para float32."""
    registers = [
        {
            "address": 500,
            "count": 1,
            "slave_id": 1,
            "type": "holding",
            "data_type": "float32",
        }
    ]
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
    assert events[0].payload["value"] is None
    assert "Not enough registers for float32" in caplog.text


@pytest.mark.asyncio
async def test_modbus_decode_default(mock_modbus_client: AsyncMock) -> None:
    """
    [P2] Verifica el fallback a lista cruda cuando el tipo de dato es
    desconocido o por defecto.
    """
    registers = [
        {
            "address": 600,
            "count": 2,
            "slave_id": 1,
            "type": "holding",
            "data_type": "unknown",
        }
    ]
    driver = ModbusDriver(host="127.0.0.1", port=5020, registers=registers)
    mock_modbus_client.connect.return_value = True
    await driver.connect()

    read_response = MagicMock(spec=ModbusPDU)
    read_response.isError.return_value = False
    read_response.registers = [10, 20]
    mock_modbus_client.read_holding_registers.return_value = read_response

    events = []
    async for event in driver.poll():
        events.append(event)

    assert len(events) == 1
    assert events[0].payload["value"] == [10, 20]
