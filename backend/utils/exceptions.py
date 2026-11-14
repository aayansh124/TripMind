
"""Custom application exceptions."""


class TravelPlannerException(Exception):
    """Base class for Travel Planner application exceptions."""

    def __init__(
        self,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ExternalAPIError(TravelPlannerException):
    """Raised when an external API request fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int | None = None,
        details: object | None = None,
    ) -> None:
        super().__init__(f"[{service_name}] API error: {message}", details)
        self.service_name = service_name
        self.status_code = status_code


class LLMServiceError(TravelPlannerException):
    """Raised when an LLM inference or parsing operation fails."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        details: object | None = None,
    ) -> None:
        super().__init__(f"LLM Error ({model or 'Gemini'}): {message}")
        self.model = model


class DatabaseError(TravelPlannerException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(f"Database Error: {message}", details)


class CacheError(TravelPlannerException):
    """Raised when Redis caching encounters a failure."""

    def __init__(
        self,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(f"Cache Error: {message}", details)


class TravelPlanningError(TravelPlannerException):
    """Raised when travel plan generation fails."""

    def __init__(
        self,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(f"Travel Planning Error: {message}", details)


class ResourceNotFoundError(TravelPlannerException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
    ) -> None:
        super().__init__(
            f"{resource_type} with ID '{resource_id}' was not found."
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(TravelPlannerException):
    """Raised when business validation fails."""

    def __init__(
        self,
        message: str,
        fields: dict | None = None,
    ) -> None:
        super().__init__(f"Validation Error: {message}", fields)
        self.fields = fields or {}
