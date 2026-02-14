import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.pdu import ModbusPDU

from idh.features.ingestion.domain.exceptions import DriverConnectionError
from idh.features.ingestion.domain.models import TelemetryEvent, TelemetryMetadata
from idh.features.ingestion.domain.ports import IngestionDriver

logger = logging.getLogger(__name__)


class ModbusDriver(IngestionDriver):
    """
    Implementación del Driver Modbus TCP usando pymodbus.
    """

    def __init__(
        self,
        host: str,
        port: int = 502,
        registers: Optional[List[Dict[str, Any]]] = None,
        gateway_id: Optional[UUID] = None,
    ):
        self.host = host
        self.port = port
        self.registers = registers or []
        self.gateway_id = gateway_id or uuid4()
        self.client: Optional[AsyncModbusTcpClient] = None

    async def connect(self) -> None:
        """Establece conexión con el dispositivo Modbus TCP."""
        try:
            self.client = AsyncModbusTcpClient(self.host, port=self.port)
            connected = await self.client.connect()
            if not connected:
                raise DriverConnectionError(
                    f"Failed to connect to Modbus device at {self.host}:{self.port}"
                )
            logger.info(f"Connected to Modbus device at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Error connecting to Modbus device: {e}")
            raise DriverConnectionError(
                f"Could not connect to {self.host}:{self.port}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Cierra la conexión."""
        if self.client:
            try:
                self.client.close()
                logger.info("Disconnected from Modbus device")
            except Exception as e:
                logger.warning(f"Error disconnecting from Modbus device: {e}")
            finally:
                self.client = None

    async def poll(self) -> AsyncGenerator[TelemetryEvent, None]:
        """Sondea los registros configurados."""
        if not self.client:
            raise DriverConnectionError("Driver is not connected")

        for reg_config in self.registers:
            address = int(reg_config.get("address", 0))
            count = int(reg_config.get("count", 1))
            slave_id = int(reg_config.get("slave_id", 1))
            reg_type = reg_config.get("type", "holding")

            try:
                if reg_type == "input":
                    response = await self.client.read_input_registers(
                        address=address, count=count, device_id=slave_id
                    )
                else:
                    response = await self.client.read_holding_registers(
                        address=address, count=count, device_id=slave_id
                    )
            except Exception as e:
                logger.warning(f"Connection error reading register {address}: {e}")
                raise DriverConnectionError(f"Modbus polling failed: {e}") from e

            if response.isError():
                logger.warning(
                    f"Modbus error reading {reg_type} register {address}: {response}"
                )
                continue

            if isinstance(response, ModbusPDU):
                try:
                    raw_values = response.registers
                    data_type = reg_config.get("data_type", "uint16")
                    value = self._decode_value(raw_values, data_type)
                    yield self._create_event(address, value, slave_id)
                except Exception as e:
                    logger.warning(f"Error decoding register {address}: {e}")
            else:
                logger.warning(f"Unexpected response type: {type(response)}")

    def _create_event(self, address: int, value: Any, slave_id: int) -> TelemetryEvent:
        """Crea un evento de telemetría normalizado."""
        timestamp = datetime.now(timezone.utc)

        metadata = TelemetryMetadata(
            source_gateway_id=self.gateway_id,
            origin_timestamp_utc=timestamp,
            event_type="modbus_telemetry",
        )

        payload = {
            "register_address": address,
            "value": value,
            "slave_id": slave_id,
        }

        return TelemetryEvent(metadata=metadata, payload=payload)

    def _decode_value(self, values: List[int], data_type: str) -> Any:
        """Decodifica lista de registros a tipo Python usando struct."""
        import struct

        if not values:
            return None

        dt = data_type.lower()

        if dt in ("uint16", "word"):
            return values[0]

        if dt in ("int16", "short"):
            val = values[0]
            if val > 32767:
                val -= 65536
            return val

        if dt == "float32":
            if len(values) < 2:
                logger.warning("Not enough registers for float32")
                return None
            try:
                packed = struct.pack(">HH", values[0], values[1])
                return struct.unpack(">f", packed)[0]
            except Exception as e:
                logger.error(f"Error decoding float32: {e}")
                return None

        return values
