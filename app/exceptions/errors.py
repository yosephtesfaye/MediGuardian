"""Domain-specific exceptions for MediGuardian AI."""


class MediGuardianError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(MediGuardianError):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            f"{resource} '{identifier}' not found.",
            code="not_found",
        )


class ValidationError(MediGuardianError):
    def __init__(self, message: str):
        super().__init__(message, code="validation_error")


class SafetyViolationError(MediGuardianError):
    def __init__(self, message: str):
        super().__init__(message, code="safety_violation")


class AIUnavailableError(MediGuardianError):
    def __init__(self, message: str = "AI service is unavailable."):
        super().__init__(message, code="ai_unavailable")
