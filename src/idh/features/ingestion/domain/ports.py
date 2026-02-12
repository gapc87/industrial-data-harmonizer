from abc import ABC, abstractmethod
from typing import AsyncGenerator

from .models import TelemetryEvent


class IngestionDriver(ABC):
    """Clase Base Abstracta para Drivers de Ingesta de Telemetría (Puerto Hexagonal)"""

    @abstractmethod
    async def connect(self) -> None:
        """Establece la conexión con la fuente de datos"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Cierra la conexión con la fuente de datos"""
        pass

    @abstractmethod
    def poll(self) -> AsyncGenerator[TelemetryEvent, None]:
        """Sondea la fuente de datos y genera TelemetryEvents"""

        pass
