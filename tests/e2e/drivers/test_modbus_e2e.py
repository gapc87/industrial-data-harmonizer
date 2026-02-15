import logging

import pytest

from idh.features.ingestion.infrastructure.drivers.modbus import ModbusDriver

logger = logging.getLogger(__name__)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.e2e
async def test_modbus_driver_connects_to_local_server(
    modbus_server: tuple[str, int],
) -> None:
    """
    Test E2E de conectividad contra servidor Modbus local (Simulado con TCP Echo).
    """
    host, port = modbus_server
    registers = [{"address": 0, "count": 1, "slave_id": 1, "type": "holding"}]

    driver = ModbusDriver(host=host, port=port, registers=registers)

    try:
        logger.info(f"Conectando a Modbus Server en {host}:{port}...")
        await driver.connect()
        logger.info("✅ Conexión establecida.")

        events = []
        async for event in driver.poll():
            events.append(event)
            logger.info(f"✅ Evento recibido: {event.payload}")

        assert len(events) == 1
        assert event.payload["value"] is not None

    except Exception as e:
        pytest.fail(f"Fallo E2E Modbus: {e}")
    finally:
        await driver.disconnect()
