
"""API routes for conversational interactions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_travel_service
from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.services.travel_service import TravelService
from backend.utils.logger import logger


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


TravelServiceDependency = Annotated[
    TravelService,
    Depends(get_travel_service),
]


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_with_assistant(
    request: ChatRequest,
    service: TravelServiceDependency,
) -> ChatResponse:
    """Process conversational queries using the chat workflow."""

    try:
        return await service.handle_chat_message(request)

    except Exception as exc:
        logger.exception(
            "Chat processing failed for thread %s.",
            request.thread_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversational response.",
        ) from exc
