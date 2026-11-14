"""Node implementations for LangGraph orchestration."""

import time
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agents.destination_agent import run_destination_agent
from backend.agents.flight_agent import run_flight_agent
from backend.agents.hotel_agent import run_hotel_agent
from backend.agents.itinerary_agent import run_itinerary_agent
from backend.agents.response_agent import run_response_agent
from backend.agents.weather_agent import run_weather_agent
from backend.api.schemas.travel import (
    DailyItinerary,
    DestinationResult,
    FlightResult,
    HotelResult,
    ItineraryResult,
    TravelPlan,
    TravelRequest,
    TravelStyle,
    WeatherResult,
)
from backend.clients.llm_client import get_gemini_client
from backend.graph.state import TravelState
from backend.prompts.agent_prompts import CHAT_AGENT_PROMPT
from backend.utils.logger import logger


async def destination_node(state: TravelState) -> Dict[str, Any]:
    """Execute Destination Agent."""
    start = time.time()
    logger.info("Executing Graph Node: destination_node")
    try:
        res = await run_destination_agent(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
            duration_days=state["duration_days"],
            travellers=state["travellers"],
            travel_style=state["travel_style"],
            preferences=state.get("travel_preferences"),
        )
        return {
            "destination_results": res.model_dump(),
            "execution_status": {"destination_agent": res.status.value},
            "errors": [res.error] if res.error else [],
        }
    except Exception as e:
        logger.exception("destination_node encountered error: %s", e)
        return {
            "execution_status": {"destination_agent": "failed"},
            "errors": [f"Destination agent node error: {str(e)}"],
        }


async def flight_node(state: TravelState) -> Dict[str, Any]:
    """Execute Flight Agent."""
    logger.info("Executing Graph Node: flight_node")
    try:
        res = await run_flight_agent(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )
        return {
            "flight_results": res.model_dump(),
            "execution_status": {"flight_agent": res.status.value},
            "errors": [res.error] if res.error else [],
        }
    except Exception as e:
        logger.exception("flight_node encountered error: %s", e)
        return {
            "execution_status": {"flight_agent": "failed"},
            "errors": [f"Flight agent node error: {str(e)}"],
        }


async def hotel_node(state: TravelState) -> Dict[str, Any]:
    """Execute Hotel Agent."""
    logger.info("Executing Graph Node: hotel_node")
    try:
        res = await run_hotel_agent(
            destination=state["destination"],
            budget=state["budget"],
            currency=state["currency"],
            travellers=state["travellers"],
            travel_style=state["travel_style"],
            accommodation_preference=state.get("accommodation_preference"),
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )
        return {
            "hotel_results": res.model_dump(),
            "execution_status": {"hotel_agent": res.status.value},
            "errors": [res.error] if res.error else [],
        }
    except Exception as e:
        logger.exception("hotel_node encountered error: %s", e)
        return {
            "execution_status": {"hotel_agent": "failed"},
            "errors": [f"Hotel agent node error: {str(e)}"],
        }


async def weather_node(state: TravelState) -> Dict[str, Any]:
    """Execute Weather Agent."""
    logger.info("Executing Graph Node: weather_node")
    try:
        res = await run_weather_agent(
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )
        return {
            "weather_results": res.model_dump(),
            "execution_status": {"weather_agent": res.status.value},
            "errors": [res.error] if res.error else [],
        }
    except Exception as e:
        logger.exception("weather_node encountered error: %s", e)
        return {
            "execution_status": {"weather_agent": "failed"},
            "errors": [f"Weather agent node error: {str(e)}"],
        }


async def itinerary_node(state: TravelState) -> Dict[str, Any]:
    """Execute Itinerary Agent after parallel upstream research completes."""
    logger.info("Executing Graph Node: itinerary_node")
    try:
        dest_res = DestinationResult.model_validate(state["destination_results"]) if state.get("destination_results") else None
        flight_res = FlightResult.model_validate(state["flight_results"]) if state.get("flight_results") else None
        hotel_res = HotelResult.model_validate(state["hotel_results"]) if state.get("hotel_results") else None
        weather_res = WeatherResult.model_validate(state["weather_results"]) if state.get("weather_results") else None

        res = await run_itinerary_agent(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
            duration_days=state["duration_days"],
            travellers=state["travellers"],
            budget=state["budget"],
            currency=state["currency"],
            travel_style=state["travel_style"],
            destination_res=dest_res,
            flight_res=flight_res,
            hotel_res=hotel_res,
            weather_res=weather_res,
        )
        return {
            "itinerary_results": res.model_dump(),
            "execution_status": {"itinerary_agent": res.status.value},
            "errors": [res.error] if res.error else [],
        }
    except Exception as e:
        logger.exception("itinerary_node encountered error: %s", e)
        return {
            "execution_status": {"itinerary_agent": "failed"},
            "errors": [f"Itinerary agent node error: {str(e)}"],
        }


async def response_node(state: TravelState) -> Dict[str, Any]:
    """Execute Response Agent to reconcile budget and assemble final TravelPlan."""
    logger.info("Executing Graph Node: response_node")
    try:
        dest_res = DestinationResult.model_validate(state["destination_results"]) if state.get("destination_results") else None
        flight_res = FlightResult.model_validate(state["flight_results"]) if state.get("flight_results") else None
        hotel_res = HotelResult.model_validate(state["hotel_results"]) if state.get("hotel_results") else None
        weather_res = WeatherResult.model_validate(state["weather_results"]) if state.get("weather_results") else None

        itinerary_items: List[DailyItinerary] = []
        if state.get("itinerary_results"):
            itin_data = state["itinerary_results"].get("data", [])
            for item in itin_data:
                itinerary_items.append(DailyItinerary.model_validate(item))

        # Reconstruct TravelRequest object
        req = TravelRequest(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
            travellers=state["travellers"],
            budget=state["budget"],
            currency=state["currency"],
            travel_preferences=state.get("travel_preferences"),
            accommodation_preference=state.get("accommodation_preference"),
            travel_style=TravelStyle(state["travel_style"]),
        )

        plan = await run_response_agent(
            trip_id=state["trip_id"],
            request=req,
            duration_days=state["duration_days"],
            destination_res=dest_res,
            flight_res=flight_res,
            hotel_res=hotel_res,
            weather_res=weather_res,
            itinerary_days=itinerary_items,
        )

        return {
            "final_plan": plan.model_dump(),
            "execution_status": {"response_agent": plan.execution_status.value},
        }
    except Exception as e:
        logger.exception("response_node encountered error: %s", e)
        return {
            "execution_status": {"response_agent": "failed"},
            "errors": [f"Response agent node error: {str(e)}"],
        }


async def chat_node(state: TravelState) -> Dict[str, Any]:
    """Handle conversational turn maintaining thread continuity."""
    logger.info("Executing Graph Node: chat_node for thread_id=%s", state.get("thread_id"))
    messages = state.get("messages", [])
    user_msg = messages[-1].content if messages else "Hello"

    trip_context_str = "No specific trip loaded."
    if state.get("final_plan"):
        fp = state["final_plan"]
        trip_context_str = (
            f"Trip to {fp.get('destination')} from {fp.get('origin')} "
            f"({fp.get('departure_date')} to {fp.get('return_date')}). "
            f"Budget: {fp.get('budget', {}).get('amount')} {fp.get('budget', {}).get('currency')}. "
            f"Style: {fp.get('travel_style')}."
        )

    history_str = "\n".join([f"{m.type}: {m.content}" for m in messages[:-1]])

    prompt = CHAT_AGENT_PROMPT.format(
        trip_context=trip_context_str,
        history=history_str or "No previous history.",
        user_message=user_msg,
    )

    try:
        llm = get_gemini_client(temperature=0.5)
        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_msg),
        ])
        return {
            "messages": [AIMessage(content=str(response.content))],
        }
    except Exception as e:
        logger.warning("chat_node LLM error: %s", e)
        fallback_reply = (
            f"I have received your request regarding {trip_context_str}. "
            "Please check back shortly or let me know if you would like me to adjust your activities, hotel recommendations, or budget."
        )
        return {
            "messages": [AIMessage(content=fallback_reply)],
        }

