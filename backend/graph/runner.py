
"""Runner interface for travel planning and conversational workflows."""

from typing import Any

from langchain_core.messages import HumanMessage

from backend.api.schemas.travel import TravelPlan, TravelRequest
from backend.graph.state import TravelState
from backend.graph.workflow import (
    get_chat_workflow,
    get_travel_workflow,
)
from backend.utils.logger import logger


async def run_travel_workflow(
    trip_id: str,
    thread_id: str,
    request: TravelRequest,
    duration_days: int,
) -> tuple[TravelPlan | None, dict[str, str], list[str]]:
    """Execute the multi-agent graph to generate a travel plan."""

    logger.info(
        "Starting travel workflow: trip_id=%s, thread_id=%s",
        trip_id,
        thread_id,
    )

    initial_state: TravelState = {
        "messages": [],
        "thread_id": thread_id,
        "trip_id": trip_id,
        "origin": request.origin,
        "destination": request.destination,
        "departure_date": request.departure_date,
        "return_date": request.return_date,
        "duration_days": duration_days,
        "travellers": request.travellers,
        "budget": request.budget,
        "currency": request.currency,
        "travel_style": request.travel_style.value,
        "travel_preferences": request.travel_preferences,
        "accommodation_preference": request.accommodation_preference,
        "destination_results": None,
        "flight_results": None,
        "hotel_results": None,
        "weather_results": None,
        "itinerary_results": None,
        "final_plan": None,
        "errors": [],
        "execution_status": {},
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        workflow = get_travel_workflow()

        final_state: TravelState = await workflow.ainvoke(
            initial_state,
            config=config,
        )

        final_plan_data = final_state.get("final_plan")

        plan = (
            TravelPlan.model_validate(final_plan_data)
            if final_plan_data
            else None
        )

        execution_status = final_state.get("execution_status", {})
        errors = final_state.get("errors", [])

        logger.info(
            "Travel workflow completed: trip_id=%s, errors=%d",
            trip_id,
            len(errors),
        )

        return plan, execution_status, errors

    except Exception as exc:
        logger.exception(
            "Travel workflow failed for trip_id=%s.",
            trip_id,
        )
        return None, {"workflow": "failed"}, [str(exc)]


async def run_chat_turn(
    thread_id: str,
    user_message: str,
    trip_context: TravelPlan | None = None,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    """Execute a conversational turn while maintaining thread state."""

    logger.info("Executing chat turn for thread_id=%s", thread_id)

    initial_state: TravelState = {
        "messages": [HumanMessage(content=user_message)],
        "thread_id": thread_id,
        "trip_id": trip_context.trip_id if trip_context else "",
        "final_plan": (
            trip_context.model_dump(mode="json")
            if trip_context
            else None
        ),
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        workflow = get_chat_workflow()

        output_state = await workflow.ainvoke(
            initial_state,
            config=config,
        )

        messages = output_state.get("messages", [])

        reply = (
            messages[-1].content
            if messages
            else "I am ready to assist with your travel planning."
        )

        sources = trip_context.sources if trip_context else []

        return reply, None, sources

    except Exception:
        logger.exception(
            "Chat workflow failed for thread_id=%s.",
            thread_id,
        )

        return (
            "I apologize, but I encountered an error processing your message. "
            "Please try asking again.",
            None,
            [],
        )
