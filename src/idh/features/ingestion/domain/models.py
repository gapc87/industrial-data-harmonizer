"""
Modelos de dominio para eventos de telemetría.

Estos modelos representan los datos capturados desde fuentes OT
siguiendo el patrón Forensic Medallion de la arquitectura.
"""

from datetime import datetime
from typing import Annotated, Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import AfterValidator


def validate_utc(dt: datetime) -> datetime:
    """Valida que el datetime tenga zona horaria definida."""
    if dt.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware (UTC)")
    return dt


class TelemetryMetadata(BaseModel):
    """Metadatos siguiendo estrictamente el mandato arquitectónico."""

    model_config = ConfigDict(frozen=True)

    source_gateway_id: UUID
    origin_timestamp_utc: Annotated[datetime, AfterValidator(validate_utc)]
    event_type: str = Field(min_length=1)


class TelemetryEvent(BaseModel):
    """Modelo de dominio para eventos de telemetría. Inmutable."""

    model_config = ConfigDict(frozen=True)

    metadata: TelemetryMetadata
    payload: Dict[str, Any]
