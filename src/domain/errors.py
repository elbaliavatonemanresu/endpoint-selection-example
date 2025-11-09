"""Domain-specific exceptions for CTTI application."""


class CTTIError(Exception):
    """Base exception for all CTTI domain errors."""

    pass


class ValidationError(CTTIError):
    """Exception raised when model validation fails."""

    pass


class StateError(CTTIError):
    """Exception raised when invalid state transition is attempted."""

    pass


class NotFoundError(CTTIError):
    """Exception raised when a requested entity is not found."""

    pass


class LockedError(CTTIError):
    """Exception raised when attempting to edit a locked entity."""

    pass
