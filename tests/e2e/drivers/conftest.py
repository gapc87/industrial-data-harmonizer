import asyncio
import logging
from typing import AsyncGenerator

import pytest_asyncio

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="function")
async def modbus_server() -> AsyncGenerator[tuple[str, int], None]:
    """
    Fixture que levanta un servidor Modbus TCP (Mock Asyncio)
    en un proceso/tarea aparte.

    Retorna (host, port).
    """
    import logging

    logger = logging.getLogger("drivers.conftest")
    port = 5025

    logger.info(f"Iniciando servidor Modbus Mock en puerto {port}...")

    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            data = await reader.read(1024)
            if not data:
                return

            if len(data) >= 8:
                tid = data[0:2]
                response = tid + b"\x00\x00\x00\x05\x01\x03\x02\x00\x11"
                writer.write(response)
                await writer.drain()
            else:
                logger.warning(f"Mock Server received unexpected data len: {len(data)}")

        except Exception as e:
            logger.error(f"Mock Server error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", port)

    async def run_server() -> None:
        async with server:
            await server.serve_forever()

    task = asyncio.create_task(run_server())

    server_ready = False
    for _ in range(50):
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            server_ready = True
            break
        except Exception:
            await asyncio.sleep(0.1)

    if not server_ready:
        task.cancel()
        raise RuntimeError("Mock Server failed to start")

    yield "127.0.0.1", port

    logger.info("Deteniendo servidor Modbus dummy...")
    try:
        if hasattr(server, "shutdown"):
            await server.shutdown()
        if hasattr(server, "server_close"):
            server.server_close()
    except Exception:
        pass

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
