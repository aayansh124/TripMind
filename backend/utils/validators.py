"""Input validation utilities for Travel Planner."""

from datetime import date, datetime
from typing import Tuple
from backend.utils.exceptions import ValidationError


def validate_travel_dates(departure_date_str: str, return_date_str: str) -> Tuple[date, date, int]:
    """Validate departure and return dates.

    Args:
        departure_date_str: String formatted as YYYY-MM-DD.
        return_date_str: String formatted as YYYY-MM-DD.

    Returns:
        Tuple of (departure_date, return_date, duration_days).

    Raises:
        ValidationError: If format is invalid or return date is before departure.
    """
    try:
        dep_date = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"Invalid departure date format '{departure_date_str}'. Expected YYYY-MM-DD.")

    try:
        ret_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"Invalid return date format '{return_date_str}'. Expected YYYY-MM-DD.")

    if ret_date < dep_date:
        raise ValidationError(
            f"Return date ({return_date_str}) cannot be earlier than departure date ({departure_date_str})."
        )

    # Duration includes both departure and return days (at least 1 day)
    duration_days = (ret_date - dep_date).days + 1

    if duration_days > 90:
        raise ValidationError(
            f"Travel duration of {duration_days} days exceeds maximum supported limit of 90 days."
        )

    return dep_date, ret_date, duration_days


def sanitize_string(value: str, max_length: int = 200) -> str:
    """Sanitize and truncate user text inputs to prevent prompt injection or buffer overflows."""
    if not value:
        return ""
    cleaned = value.strip().replace("\x00", "")
    return cleaned[:max_length]

