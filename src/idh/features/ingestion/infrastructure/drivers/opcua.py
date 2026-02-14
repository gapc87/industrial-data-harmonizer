import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, List, Optional
from uuid import UUID, uuid4

from asyncua import Client, ua
from asyncua.common.node import Node
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

from idh.features.ingestion.domain.exceptions import DriverConnectionError
from idh.features.ingestion.domain.models import TelemetryEvent, TelemetryMetadata
from idh.features.ingestion.domain.ports import IngestionDriver

logger = logging.getLogger(__name__)


class OpcUaDriver(IngestionDriver):
    """
    Implementación del Driver OPC UA usando la librería asyncua.
    (Adaptador de Infraestructura)
    """

    def __init__(
        self,
        endpoint_url: str,
        node_ids: List[str],
        gateway_id: Optional[UUID] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cert_path: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url
        self.node_ids = node_ids
        self.gateway_id = gateway_id or uuid4()
        self.username = username
        self.password = password
        self.cert_path = cert_path
        self.private_key_path = private_key_path
        self.client: Optional[Client] = None

    async def connect(self) -> None:
        """Establece conexión con el servidor OPC UA."""
        self.client = Client(url=self.endpoint_url)
        if self.username or self.password:
            if not (self.username and self.password):
                raise ValueError(
                    "Both username and password must be provided "
                    "for user authentication."
                )
            self.client.set_user(self.username)
            self.client.set_password(self.password)

        if self.cert_path or self.private_key_path:
            if not (self.cert_path and self.private_key_path):
                raise ValueError(
                    "Both certificate and private key must be provided for mTLS."
                )
            await self.client.set_security(
                SecurityPolicyBasic256Sha256,
                self.cert_path,
                self.private_key_path,
                mode=ua.MessageSecurityMode.SignAndEncrypt,
            )

        try:
            await self.client.connect()
            logger.info(f"Connected to OPC UA server at {self.endpoint_url}")
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            raise DriverConnectionError(
                f"Could not connect to {self.endpoint_url}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Cierra la conexión con el servidor OPC UA."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from OPC UA server")
            except Exception as e:
                logger.warning(f"Error disconnecting from OPC UA server: {e}")
            finally:
                self.client = None

    async def poll(self) -> AsyncGenerator[TelemetryEvent, None]:
        """Sondea los nodos configurados y genera TelemetryEvents."""
        if not self.client:
            raise DriverConnectionError("Driver is not connected")

        try:
            nodes: List[Node] = [
                self.client.get_node(node_id) for node_id in self.node_ids
            ]
            values = await self.client.read_values(nodes)

            for i, value in enumerate(values):
                yield self._create_event(self.node_ids[i], value)

        except Exception as e:
            logger.warning(f"Bulk read failed ({e}), falling back to sequential read.")

            for node_id in self.node_ids:
                try:
                    node = self.client.get_node(node_id)
                    value = await node.read_value()
                    yield self._create_event(node_id, value)
                except Exception as inner_e:
                    logger.error(f"Failed to read individual node {node_id}: {inner_e}")
                    continue

    def _create_event(self, node_id: str, value: Any) -> TelemetryEvent:
        """Helper para crear un TelemetryEvent saneado"""

        safe_value = self._ensure_serializable(value)
        variant_type = type(value).__name__

        timestamp = datetime.now(timezone.utc)

        metadata = TelemetryMetadata(
            source_gateway_id=self.gateway_id,
            origin_timestamp_utc=timestamp,
            event_type="opcua_telemetry",
        )

        payload = {
            "node_id": node_id,
            "value": safe_value,
            "variant_type": variant_type,
        }

        return TelemetryEvent(metadata=metadata, payload=payload)

    def _ensure_serializable(self, value: Any) -> Any:
        """Asegura recursivamente que el valor sea serializable a JSON."""
        if value is None:
            return None
        if isinstance(value, (int, float, bool, str)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (list, tuple)):
            return [self._ensure_serializable(v) for v in value]
        if isinstance(value, dict):
            return {str(k): self._ensure_serializable(v) for k, v in value.items()}

        return str(value)
