"""
Excepciones de Dominio.

Excepciones específicas del negocio que representan violaciones de reglas.
Estas excepciones son capturadas en la capa de infraestructura/API
y traducidas a respuestas HTTP apropiadas.
"""


class DomainException(Exception):
    """Excepción base para errores de dominio."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(DomainException):
    """Se lanza cuando una entidad solicitada no existe."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} con ID '{entity_id}' no encontrado.")
        self.entity_type = entity_type
        self.entity_id = entity_id


class BusinessRuleViolationError(DomainException):
    """Se lanza cuando se viola una regla de negocio."""

    pass


class ValidationError(DomainException):
    """Se lanza cuando los datos no pasan validación de dominio."""

    pass
