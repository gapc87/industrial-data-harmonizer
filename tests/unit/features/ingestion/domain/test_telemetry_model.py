"""
Pruebas unitarias para los modelos de dominio de telemetría.

Cubre:
- Estructura del modelo TelemetryEvent (AC 1)
- Reglas de validación (AC 2)
- Inmutabilidad (AC 3)
- Serialización/deserialización JSON
"""

from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

import pytest
from pydantic import ValidationError

from idh.features.ingestion.domain.models import TelemetryEvent, TelemetryMetadata


class TestTelemetryEventStructure:
    """Tests para verificar la estructura del modelo TelemetryEvent (AC 1)."""

    def test_valid_event_creation(self) -> None:
        """Verifica creación de TelemetryEvent válido con metadata y payload."""
        gateway_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        metadata = TelemetryMetadata(
            source_gateway_id=gateway_id,
            origin_timestamp_utc=timestamp,
            event_type="test_event",
        )

        payload: dict[str, Any] = {"temperature": 25.5, "status": "ok"}

        event = TelemetryEvent(metadata=metadata, payload=payload)

        assert event.metadata.source_gateway_id == gateway_id
        assert event.metadata.origin_timestamp_utc == timestamp
        assert event.metadata.event_type == "test_event"
        assert event.payload == payload

    def test_nested_payload_supported(self) -> None:
        """Verifica que payload soporta objetos JSON anidados."""
        metadata = TelemetryMetadata(
            source_gateway_id=uuid4(),
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="sensor_reading",
        )

        nested_payload: dict[str, Any] = {
            "sensors": {
                "temp": {"value": 25.5, "unit": "celsius"},
                "pressure": {"value": 1013.25, "unit": "hPa"},
            },
            "tags": ["production", "line-1"],
        }

        event = TelemetryEvent(metadata=metadata, payload=nested_payload)
        assert event.payload["sensors"]["temp"]["value"] == 25.5

    def test_empty_payload_valid(self) -> None:
        """Verifica que un payload vacío es válido."""
        metadata = TelemetryMetadata(
            source_gateway_id=uuid4(),
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="heartbeat",
        )

        event = TelemetryEvent(metadata=metadata, payload={})
        assert event.payload == {}


class TestImmutability:
    """Tests para verificar la inmutabilidad de los modelos (AC 3)."""

    def test_telemetry_event_is_frozen(self) -> None:
        """Verifica que TelemetryEvent es inmutable (frozen)."""
        metadata = TelemetryMetadata(
            source_gateway_id=uuid4(),
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="test_event",
        )

        event = TelemetryEvent(metadata=metadata, payload={})

        with pytest.raises(ValidationError):
            event.metadata = metadata  # type: ignore[misc]

        with pytest.raises(ValidationError):
            event.payload = {"new": "value"}  # type: ignore[misc]

    def test_telemetry_metadata_is_frozen(self) -> None:
        """Verifica que TelemetryMetadata es inmutable (frozen)."""
        metadata = TelemetryMetadata(
            source_gateway_id=uuid4(),
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="test_event",
        )

        with pytest.raises(ValidationError):
            metadata.event_type = "modified"  # type: ignore[misc]


class TestValidationRules:
    """Tests para verificar las reglas de validación (AC 2)."""

    def test_invalid_uuid_raises_validation_error(self) -> None:
        """Verifica que un UUID inválido genera ValidationError."""
        with pytest.raises(ValidationError):
            TelemetryMetadata(
                source_gateway_id="invalid-uuid",
                origin_timestamp_utc=datetime.now(timezone.utc),
                event_type="test",
            )

    def test_naive_datetime_raises_validation_error(self) -> None:
        """Verifica que un datetime sin timezone genera ValidationError (AC 2.2)."""
        naive_datetime = datetime(2026, 1, 1, 12, 0, 0)  # Sin timezone

        with pytest.raises(ValidationError) as exc_info:
            TelemetryMetadata(
                source_gateway_id=uuid4(),
                origin_timestamp_utc=naive_datetime,
                event_type="test",
            )

        assert "timezone-aware" in str(exc_info.value).lower()

    def test_empty_event_type_raises_validation_error(self) -> None:
        """Verifica que event_type vacío genera ValidationError."""
        with pytest.raises(ValidationError):
            TelemetryMetadata(
                source_gateway_id=uuid4(),
                origin_timestamp_utc=datetime.now(timezone.utc),
                event_type="",
            )

    def test_invalid_payload_type_raises_validation_error(self) -> None:
        """Verifica que un payload que no es dict genera ValidationError."""
        metadata = TelemetryMetadata(
            source_gateway_id=uuid4(),
            origin_timestamp_utc=datetime.now(timezone.utc),
            event_type="test",
        )

        with pytest.raises(ValidationError):
            TelemetryEvent(
                metadata=metadata,
                payload=cast(dict[str, Any], "not-a-dict"),
            )


class TestJsonSerialization:
    """Tests para verificar serialización/deserialización JSON (AC 2 task)."""

    def test_model_dump_produces_valid_json(self) -> None:
        """Verifica que model_dump() produce JSON válido con fechas ISO 8601."""
        gateway_id = uuid4()
        timestamp = datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc)

        event = TelemetryEvent(
            metadata=TelemetryMetadata(
                source_gateway_id=gateway_id,
                origin_timestamp_utc=timestamp,
                event_type="sensor_data",
            ),
            payload={"value": 42},
        )

        dumped = event.model_dump(mode="json")

        assert dumped["metadata"]["source_gateway_id"] == str(gateway_id)
        assert dumped["metadata"]["origin_timestamp_utc"] == "2026-02-06T12:00:00Z"
        assert dumped["metadata"]["event_type"] == "sensor_data"
        assert dumped["payload"] == {"value": 42}

    def test_model_validate_round_trip(self) -> None:
        """Verifica que model_validate() permite recrear el objeto desde JSON."""
        gateway_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        original = TelemetryEvent(
            metadata=TelemetryMetadata(
                source_gateway_id=gateway_id,
                origin_timestamp_utc=timestamp,
                event_type="test",
            ),
            payload={"key": "value"},
        )

        json_data = original.model_dump(mode="json")
        restored = TelemetryEvent.model_validate(json_data)

        assert (
            restored.metadata.source_gateway_id == original.metadata.source_gateway_id
        )
        assert restored.metadata.event_type == original.metadata.event_type
        assert restored.payload == original.payload
