"""API routes for conversational interactions and follow-up queries."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_travel_service
from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.services.travel_service import TravelService
from backend.utils.logger import logger

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_assistant(
    request: ChatRequest,
    service: TravelService = Depends(get_travel_service),
) -> ChatResponse:
    """Process follow-up questions about trips, flights, hotels, or itineraries."""
    try:
        response = await service.handle_chat_message(request)
        return response
    except Exception as e:
        logger.exception("Chat processing failure for thread %s: %s", request.thread_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversational response. Please try again.",
        )

