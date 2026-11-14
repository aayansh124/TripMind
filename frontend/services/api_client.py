"""HTTP Client communicating with the FastAPI Travel Planner Backend."""

import os
from typing import Any, Dict, List, Optional
import httpx

BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"


class BackendAPIClient:
    """Robust client interfacing with Travel Planner backend API."""

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def check_backend_health(self) -> Dict[str, Any]:
        """Query backend health check endpoint."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "degraded", "backend": f"HTTP {resp.status_code}"}
        except Exception:
            return {"status": "offline", "backend": "disconnected", "database": "unknown", "redis": "unknown"}

    def create_trip(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit travel parameters to generate a multi-agent plan."""
        url = f"{self.base_url}/api/v1/travel"
        try:
            # Plan generation orchestrates multiple agents; allow up to 90 seconds
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(url, json=trip_request)

            if resp.status_code in [200, 201]:
                return resp.json()

            error_detail = "Failed to create trip."
            try:
                error_detail = resp.json().get("detail", error_detail)
            except Exception:
                error_detail = resp.text

            return {"error": error_detail, "status_code": resp.status_code}
        except httpx.ConnectError:
            return {"error": "Backend server is offline or unreachable. Please verify FastAPI is running at http://127.0.0.1:8000."}
        except httpx.TimeoutException:
            return {"error": "Request timed out while multi-agent workflow was synthesizing your plan. Please retry."}
        except Exception as e:
            return {"error": f"Client request error: {str(e)}"}

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific saved trip by unique ID."""
        url = f"{self.base_url}/api/v1/travel/{trip_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def get_trips(self) -> List[Dict[str, Any]]:
        """Retrieve all previously saved trips."""
        url = f"{self.base_url}/api/v1/travel"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a saved trip."""
        url = f"{self.base_url}/api/v1/travel/{trip_id}"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.delete(url)
            return resp.status_code == 204
        except Exception:
            return False

    def send_chat_message(
        self,
        thread_id: str,
        message: str,
        trip_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Post a follow-up conversational question to the travel assistant."""
        url = f"{self.base_url}/api/v1/chat"
        payload = {
            "thread_id": thread_id,
            "message": message,
            "trip_id": trip_id,
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()

            err = "Failed to obtain assistant reply."
            try:
                err = resp.json().get("detail", err)
            except Exception:
                pass
            return {"error": err}
        except httpx.ConnectError:
            return {"error": "Backend server is currently unreachable."}
        except httpx.TimeoutException:
            return {"error": "Assistant response timed out. Please try again."}
        except Exception as e:
            return {"error": f"Chat client error: {str(e)}"}


# Singleton instance for frontend
api_client = BackendAPIClient()

