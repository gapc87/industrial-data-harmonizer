"""
Tests unitarios para excepciones de dominio.

Ejemplo de tests TDD para la capa de dominio.
"""

from idh.domain.exceptions import (
    BusinessRuleViolationError,
    DomainException,
    EntityNotFoundError,
    ValidationError,
)


class TestDomainException:
    """Tests para DomainException base."""

    def test_domain_exception_stores_message(self) -> None:
        """La excepción debe almacenar el mensaje correctamente."""
        exception = DomainException("Test error message")
        assert exception.message == "Test error message"
        assert str(exception) == "Test error message"


class TestEntityNotFoundError:
    """Tests para EntityNotFoundError."""

    def test_entity_not_found_formats_message(self) -> None:
        """Debe formatear el mensaje con tipo e ID de entidad."""
        exception = EntityNotFoundError("Order", "ORD-123")
        assert exception.entity_type == "Order"
        assert exception.entity_id == "ORD-123"
        assert "Order" in exception.message
        assert "ORD-123" in exception.message


class TestBusinessRuleViolationError:
    """Tests para BusinessRuleViolationError."""

    def test_is_domain_exception(self) -> None:
        """Debe ser subclase de DomainException."""
        exception = BusinessRuleViolationError("Cannot exceed limit")
        assert isinstance(exception, DomainException)


class TestValidationError:
    """Tests para ValidationError."""

    def test_is_domain_exception(self) -> None:
        """Debe ser subclase de DomainException."""
        exception = ValidationError("Invalid format")
        assert isinstance(exception, DomainException)
