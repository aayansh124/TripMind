"""API routes for travel plan generation and retrieval."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_travel_service
from backend.api.schemas.travel import TravelPlan, TravelRequest, TravelResponse
from backend.services.travel_service import TravelService
from backend.utils.exceptions import ResourceNotFoundError, ValidationError
from backend.utils.logger import logger

router = APIRouter(prefix="/api/v1/travel", tags=["Travel"])


@router.post("", response_model=TravelResponse, status_code=status.HTTP_201_CREATED)
async def create_travel_plan(
    request: TravelRequest,
    service: TravelService = Depends(get_travel_service),
) -> TravelResponse:
    """Generate a comprehensive multi-agent travel plan."""
    try:
        response = await service.create_travel_plan(request)
        return response
    except ValidationError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ve.message)
    except Exception as e:
        logger.exception("Unexpected error generating travel plan: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate travel plan. Please check backend logs.",
        )


@router.get("", response_model=List[Dict[str, Any]])
def list_saved_trips(
    service: TravelService = Depends(get_travel_service),
) -> List[Dict[str, Any]]:
    """Retrieve all saved travel plans."""
    try:
        return service.get_all_trips()
    except Exception as e:
        logger.exception("Failed to retrieve saved travel plans: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve trips.",
        )


@router.get("/{trip_id}", response_model=TravelPlan)
def get_trip_by_id(
    trip_id: str,
    service: TravelService = Depends(get_travel_service),
) -> TravelPlan:
    """Retrieve a specific travel plan by unique trip ID."""
    try:
        return service.get_trip(trip_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID '{trip_id}' not found.",
        )
    except Exception as e:
        logger.exception("Error fetching trip %s: %s", trip_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trip.",
        )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip_by_id(
    trip_id: str,
    service: TravelService = Depends(get_travel_service),
) -> None:
    """Delete a saved travel plan by unique trip ID."""
    try:
        service.delete_trip(trip_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID '{trip_id}' not found.",
        )
    except Exception as e:
        logger.exception("Error deleting trip %s: %s", trip_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trip.",
        )

