
"""Input validation utilities for Travel Planner."""

from datetime import date, datetime

from backend.utils.exceptions import ValidationError


def validate_travel_dates(
    departure_date_str: str,
    return_date_str: str,
) -> tuple[date, date, int]:
    """Validate departure and return dates."""

    try:
        departure_date = datetime.strptime(
            departure_date_str,
            "%Y-%m-%d",
        ).date()
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            f"Invalid departure date '{departure_date_str}'. "
            "Expected format: YYYY-MM-DD."
        ) from exc

    try:
        return_date = datetime.strptime(
            return_date_str,
            "%Y-%m-%d",
        ).date()
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            f"Invalid return date '{return_date_str}'. "
            "Expected format: YYYY-MM-DD."
        ) from exc

    if return_date < departure_date:
        raise ValidationError(
            "Return date cannot be earlier than departure date."
        )

    duration_days = (return_date - departure_date).days + 1

    if duration_days > 90:
        raise ValidationError(
            f"Travel duration of {duration_days} days "
            "exceeds the maximum supported limit of 90 days."
        )

    return departure_date, return_date, duration_days


def sanitize_string(
    value: str,
    max_length: int = 200,
) -> str:
    """Remove null bytes, trim whitespace, and limit input length."""

    if not isinstance(value, str):
        return ""

    if max_length < 0:
        raise ValueError("max_length cannot be negative.")

    cleaned = value.strip().replace("\x00", "")

    return cleaned[:max_length]
