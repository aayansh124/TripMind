
"""API routes for travel planning and trip management."""

from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_travel_service
from backend.api.schemas.travel import (
    TravelPlan,
    TravelRequest,
    TravelResponse,
)
from backend.services.travel_service import TravelService
from backend.utils.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from backend.utils.logger import logger


router = APIRouter(
    prefix="/api/v1/travel",
    tags=["Travel"],
)


TravelServiceDependency = Annotated[
    TravelService,
    Depends(get_travel_service),
]


@router.post(
    "",
    response_model=TravelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_travel_plan(
    request: TravelRequest,
    service: TravelServiceDependency,
) -> TravelResponse:
    """Generate a travel plan using the multi-agent workflow."""

    try:
        return await service.create_travel_plan(request)

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    except Exception as exc:
        logger.exception("Travel plan generation failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate travel plan.",
        ) from exc


@router.get(
    "",
    response_model=list[dict[str, Any]],
)
def list_saved_trips(
    service: TravelServiceDependency,
) -> list[dict[str, Any]]:
    """Retrieve all saved travel plans."""

    try:
        return service.get_all_trips()

    except Exception as exc:
        logger.exception("Failed to retrieve saved trips.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve travel plans.",
        ) from exc


@router.get(
    "/{trip_id}",
    response_model=TravelPlan,
)
def get_trip_by_id(
    trip_id: str,
    service: TravelServiceDependency,
) -> TravelPlan:
    """Retrieve a travel plan using its unique ID."""

    try:
        return service.get_trip(trip_id)

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID '{trip_id}' not found.",
        ) from exc

    except Exception as exc:
        logger.exception("Failed to retrieve trip %s.", trip_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve travel plan.",
        ) from exc


@router.delete(
    "/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_trip_by_id(
    trip_id: str,
    service: TravelServiceDependency,
) -> None:
    """Delete a saved travel plan."""

    try:
        service.delete_trip(trip_id)

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Travel plan with ID '{trip_id}' not found.",
        ) from exc

    except Exception as exc:
        logger.exception("Failed to delete trip %s.", trip_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete travel plan.",
        ) from exc
