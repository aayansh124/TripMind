
"""HTTP client for communicating with the FastAPI backend."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv


# Load environment variables before reading backend configuration.
load_dotenv()

BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

HEALTH_TIMEOUT = 3.0
DEFAULT_TIMEOUT = 10.0
TRAVEL_TIMEOUT = 90.0
CHAT_TIMEOUT = 45.0


class BackendAPIClient:
    """Client for Travel Planner backend endpoints."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def _get_error_detail(self, response: httpx.Response) -> str:
        """Extract a readable error message from an API response."""

        try:
            detail = response.json().get("detail")

            if isinstance(detail, str):
                return detail

            if detail is not None:
                return str(detail)

        except (ValueError, AttributeError):
            pass

        return response.text or f"HTTP {response.status_code}"

    def check_backend_health(self) -> dict[str, Any]:
        """Check backend health."""

        try:
            with httpx.Client(timeout=HEALTH_TIMEOUT) as client:
                response = client.get(f"{self.base_url}/health")

            if response.status_code == 200:
                return response.json()

            return {
                "status": "degraded",
                "backend": f"HTTP {response.status_code}",
            }

        except httpx.RequestError:
            return {
                "status": "offline",
                "backend": "disconnected",
                "database": "unknown",
                "redis": "unknown",
            }

    def create_trip(
        self,
        trip_request: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit travel parameters and generate a travel plan."""

        url = f"{self.base_url}/api/v1/travel"

        try:
            with httpx.Client(timeout=TRAVEL_TIMEOUT) as client:
                response = client.post(url, json=trip_request)

            if response.status_code in (200, 201):
                return response.json()

            return {
                "error": self._get_error_detail(response),
                "status_code": response.status_code,
            }

        except httpx.ConnectError:
            return {"error": "Backend server is offline or unreachable."}

        except httpx.TimeoutException:
            return {
                "error": "Travel planning request timed out. Please retry."
            }

        except httpx.RequestError:
            return {"error": "Unable to communicate with the backend."}

    def get_trip(self, trip_id: str) -> dict[str, Any] | None:
        """Retrieve a saved trip by ID."""

        url = f"{self.base_url}/api/v1/travel/{trip_id}"

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(url)

            if response.status_code == 200:
                return response.json()

            return None

        except httpx.RequestError:
            return None

    def get_trips(self) -> list[dict[str, Any]]:
        """Retrieve all saved trips."""

        url = f"{self.base_url}/api/v1/travel"

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(url)

            if response.status_code == 200:
                return response.json()

            return []

        except httpx.RequestError:
            return []

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a saved trip."""

        url = f"{self.base_url}/api/v1/travel/{trip_id}"

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.delete(url)

            return response.status_code == 204

        except httpx.RequestError:
            return False

    def send_chat_message(
        self,
        thread_id: str,
        message: str,
        trip_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a conversational message to the travel assistant."""

        url = f"{self.base_url}/api/v1/chat"

        payload = {
            "thread_id": thread_id,
            "message": message,
            "trip_id": trip_id,
        }

        try:
            with httpx.Client(timeout=CHAT_TIMEOUT) as client:
                response = client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()

            return {"error": self._get_error_detail(response)}

        except httpx.ConnectError:
            return {"error": "Backend server is currently unreachable."}

        except httpx.TimeoutException:
            return {"error": "Assistant response timed out. Please try again."}

        except httpx.RequestError:
            return {"error": "Unable to communicate with the backend."}


api_client = BackendAPIClient()
