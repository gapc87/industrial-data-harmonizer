import logging

import pytest

from idh.features.ingestion.infrastructure.drivers.opcua import OpcUaDriver

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.external
@pytest.mark.skip(
    reason="Infrastructure flaky: OPC UA server connection issues in CI/CD pipeline"
)
async def test_opcua_driver_connects_to_public_server(
    opc_plc_container: str,
) -> None:
    """
    Test E2E de conectividad contra servidor OPC UA Simulator (iotechsys).
    Este test verifica que el OpcUaDriver puede conectar a un servidor real,
    negociar conexión y leer datos.

    NOTA: Requiere Docker en el entorno de ejecución.
    """
    endpoint = opc_plc_container

    # Nodo estándar OPC UA que siempre existe en el servidor:
    # Server_ServerStatus_CurrentTime (ns=0;i=2258)
    # Usamos el NodeID numérico estándar
    node_ids = ["ns=0;i=2258"]

    driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)

    try:
        logger.info(f"Conectando a {endpoint}...")
        await driver.connect()
        logger.info("✅ Conexión establecida exitosamente.")

        events = []
        # Leemos solo un evento para verificar
        logger.info("Leyendo nodos...")
        async for event in driver.poll():
            events.append(event)
            logger.info(f"✅ Evento recibido: {event.payload}")
            # Rompemos el generador después del primero
            # ya que poll() es síncrono en loop.
            # Pero nuestra implementación actual de poll() lee una vez y yield.

        assert len(events) == 1
        assert events[0].metadata.event_type == "opcua_telemetry"
        assert str(events[0].payload["node_id"]) == "ns=0;i=2258"
        assert events[0].payload["value"] is not None

    except Exception as e:
        logger.error(f"Fallo al conectar con servidor OPC UA: {e}")
        pytest.fail(f"Fallo al conectar con servidor OPC UA: {e}")
    finally:
        await driver.disconnect()
