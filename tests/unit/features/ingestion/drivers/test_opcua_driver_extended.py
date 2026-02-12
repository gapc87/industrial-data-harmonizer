from unittest.mock import AsyncMock, patch

import pytest
from asyncua import ua

from idh.features.ingestion.domain.exceptions import DriverConnectionError
from idh.features.ingestion.infrastructure.drivers.opcua import OpcUaDriver


@pytest.mark.asyncio
async def test_opcua_driver_mtls_configuration() -> None:
    """AC 1: Verify mTLS security policy is applied when certs are provided."""
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Test"]
    cert_path = "/path/to/cert.pem"
    key_path = "/path/to/key.pem"

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.set_security = AsyncMock()
        mock_instance.connect = AsyncMock()

        driver = OpcUaDriver(
            endpoint_url=endpoint,
            node_ids=node_ids,
            cert_path=cert_path,
            private_key_path=key_path,
        )

        await driver.connect()

        # Verify set_security called with correct params
        from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

        mock_instance.set_security.assert_called_once_with(
            SecurityPolicyBasic256Sha256,
            cert_path,
            key_path,
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )
        mock_instance.connect.assert_called_once()


@pytest.mark.asyncio
async def test_opcua_driver_mtls_validation_error_no_key() -> None:
    """AC 1: Verify ValueError if only certificate is provided without key."""
    driver = OpcUaDriver(
        endpoint_url="opc.tcp://localhost:4840",
        node_ids=[],
        cert_path="/path/to/cert.pem",
        private_key_path=None,
    )

    with pytest.raises(
        ValueError, match="Both certificate and private key must be provided"
    ):
        await driver.connect()


@pytest.mark.asyncio
async def test_opcua_driver_connection_error_handling() -> None:
    """AC 4: Verify DriverConnectionError is raised when connection fails."""
    endpoint = "opc.tcp://localhost:4840"
    node_ids = ["ns=1;s=Test"]

    with patch(
        "idh.features.ingestion.infrastructure.drivers.opcua.Client"
    ) as MockClient:
        mock_instance = MockClient.return_value
        # Simulate connection failure from asyncua
        # Note: asyncua might raise ConnectionError or similar
        mock_instance.connect = AsyncMock(
            side_effect=ConnectionError("Connection timed out")
        )

        driver = OpcUaDriver(endpoint_url=endpoint, node_ids=node_ids)

        with pytest.raises(DriverConnectionError, match="Could not connect to"):
            await driver.connect()
