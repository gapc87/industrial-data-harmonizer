from datetime import datetime
from typing import Annotated, Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import AfterValidator


def validate_utc(dt: datetime) -> datetime:
    """Ensure the datetime is timezone-aware."""
    if dt.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware (UTC)")
    return dt


class TelemetryMetadata(BaseModel):
    """
    Metadata strictly following the architecture mandate.
    """

    model_config = ConfigDict(frozen=True)

    source_gateway_id: UUID
    origin_timestamp_utc: Annotated[datetime, AfterValidator(validate_utc)]
    event_type: str = Field(min_length=1)


class TelemetryEvent(BaseModel):
    """
    Domain model for telemetry events.
    Immutable representation of a historical fact.
    """

    model_config = ConfigDict(frozen=True)

    metadata: TelemetryMetadata
    payload: Dict[str, Any]
