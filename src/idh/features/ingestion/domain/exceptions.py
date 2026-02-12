from idh.core.domain.exceptions import DomainException


class DriverConnectionError(DomainException):
    """Raised when a driver fails to connect or communicate with the device."""

    pass
