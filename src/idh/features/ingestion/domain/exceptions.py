"""Excepciones del dominio de ingestión."""

from idh.core.domain.exceptions import DomainException


class DriverConnectionError(DomainException):
    """Lanzada cuando un driver falla al conectar o comunicar con el dispositivo."""

    pass
