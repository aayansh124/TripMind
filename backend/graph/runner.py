"""Runner interface for executing multi-agent travel plans and conversations."""

from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import HumanMessage

from backend.api.schemas.travel import TravelPlan, TravelRequest
from backend.graph.state import TravelState
from backend.graph.workflow import chat_workflow, travel_workflow
from backend.utils.logger import logger


async def run_travel_workflow(
    trip_id: str,
    thread_id: str,
    request: TravelRequest,
    duration_days: int,
) -> Tuple[Optional[TravelPlan], Dict[str, str], List[str]]:
    """Execute the multi-agent graph workflow to generate a travel plan.

    Args:
        trip_id: Unique trip ID.
        thread_id: LangGraph checkpoint thread ID.
        request: Validated travel request payload.
        duration_days: Computed total trip days.

    Returns:
        Tuple of (TravelPlan or None, execution_status dict, errors list).
    """
    logger.info("Starting travel graph execution for trip_id: %s, thread_id: %s", trip_id, thread_id)

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
        final_state: TravelState = await travel_workflow.ainvoke(initial_state, config=config)

        plan: Optional[TravelPlan] = None
        if final_state.get("final_plan"):
            plan = TravelPlan.model_validate(final_state["final_plan"])

        exec_status = final_state.get("execution_status", {})
        errors = final_state.get("errors", [])

        logger.info(
            "Graph workflow execution completed for trip_id: %s. Status: %s, Errors: %d",
            trip_id,
            exec_status,
            len(errors),
        )

        return plan, exec_status, errors

    except Exception as e:
        logger.exception("Catastrophic error during graph workflow execution: %s", e)
        return None, {"workflow": "failed"}, [str(e)]


async def run_chat_turn(
    thread_id: str,
    user_message: str,
    trip_context: Optional[TravelPlan] = None,
) -> Tuple[str, Optional[Dict[str, Any]], List[str]]:
    """Execute a conversational follow-up turn maintaining thread state.

    Args:
        thread_id: Conversation thread ID for LangGraph checkpointer.
        user_message: Traveler's query text.
        trip_context: Optional associated travel plan context.

    Returns:
        Tuple of (assistant_reply, structured_info, sources).
    """
    logger.info("Executing chat turn for thread_id: %s", thread_id)

    initial_state: TravelState = {
        "messages": [HumanMessage(content=user_message)],
        "thread_id": thread_id,
        "trip_id": trip_context.trip_id if trip_context else "",
        "final_plan": trip_context.model_dump() if trip_context else None,
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        output_state = await chat_workflow.ainvoke(initial_state, config=config)
        messages = output_state.get("messages", [])
        reply = messages[-1].content if messages else "I am ready to assist with your travel planning."
        sources = trip_context.sources if trip_context else []
        return reply, None, sources

    except Exception as e:
        logger.exception("Error executing chat workflow: %s", e)
        return (
            "I apologize, but I encountered an error processing your message. Please try asking again.",
            None,
            [],
        )
