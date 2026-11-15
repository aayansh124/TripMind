
"""Node implementations for LangGraph orchestration."""

from typing import Any

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
    TravelPlan,
    TravelRequest,
    TravelStyle,
    WeatherResult,
)
from backend.clients.llm_client import get_gemini_client
from backend.graph.state import TravelState
from backend.prompts.agent_prompts import CHAT_AGENT_PROMPT
from backend.utils.logger import logger


async def destination_node(state: TravelState) -> dict[str, Any]:
    """Execute the destination research agent."""

    logger.info("Executing destination node.")

    try:
        result = await run_destination_agent(
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
            "destination_results": result.model_dump(mode="json"),
            "execution_status": {
                "destination_agent": result.status.value,
            },
            "errors": [result.error] if result.error else [],
        }

    except Exception as exc:
        logger.exception("Destination node failed.")

        return {
            "execution_status": {"destination_agent": "failed"},
            "errors": [f"Destination agent node error: {exc}"],
        }


async def flight_node(state: TravelState) -> dict[str, Any]:
    """Execute the flight search agent."""

    logger.info("Executing flight node.")

    try:
        result = await run_flight_agent(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )

        return {
            "flight_results": result.model_dump(mode="json"),
            "execution_status": {
                "flight_agent": result.status.value,
            },
            "errors": [result.error] if result.error else [],
        }

    except Exception as exc:
        logger.exception("Flight node failed.")

        return {
            "execution_status": {"flight_agent": "failed"},
            "errors": [f"Flight agent node error: {exc}"],
        }


async def hotel_node(state: TravelState) -> dict[str, Any]:
    """Execute the hotel recommendation agent."""

    logger.info("Executing hotel node.")

    try:
        result = await run_hotel_agent(
            destination=state["destination"],
            budget=state["budget"],
            currency=state["currency"],
            travellers=state["travellers"],
            travel_style=state["travel_style"],
            accommodation_preference=state.get(
                "accommodation_preference"
            ),
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )

        return {
            "hotel_results": result.model_dump(mode="json"),
            "execution_status": {
                "hotel_agent": result.status.value,
            },
            "errors": [result.error] if result.error else [],
        }

    except Exception as exc:
        logger.exception("Hotel node failed.")

        return {
            "execution_status": {"hotel_agent": "failed"},
            "errors": [f"Hotel agent node error: {exc}"],
        }


async def weather_node(state: TravelState) -> dict[str, Any]:
    """Execute the destination weather agent."""

    logger.info("Executing weather node.")

    try:
        result = await run_weather_agent(
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
        )

        return {
            "weather_results": result.model_dump(mode="json"),
            "execution_status": {
                "weather_agent": result.status.value,
            },
            "errors": [result.error] if result.error else [],
        }

    except Exception as exc:
        logger.exception("Weather node failed.")

        return {
            "execution_status": {"weather_agent": "failed"},
            "errors": [f"Weather agent node error: {exc}"],
        }


async def itinerary_node(state: TravelState) -> dict[str, Any]:
    """Generate the itinerary using specialist agent results."""

    logger.info("Executing itinerary node.")

    try:
        destination_result = (
            DestinationResult.model_validate(state["destination_results"])
            if state.get("destination_results")
            else None
        )

        flight_result = (
            FlightResult.model_validate(state["flight_results"])
            if state.get("flight_results")
            else None
        )

        hotel_result = (
            HotelResult.model_validate(state["hotel_results"])
            if state.get("hotel_results")
            else None
        )

        weather_result = (
            WeatherResult.model_validate(state["weather_results"])
            if state.get("weather_results")
            else None
        )

        result = await run_itinerary_agent(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
            duration_days=state["duration_days"],
            travellers=state["travellers"],
            budget=state["budget"],
            currency=state["currency"],
            travel_style=state["travel_style"],
            destination_res=destination_result,
            flight_res=flight_result,
            hotel_res=hotel_result,
            weather_res=weather_result,
        )

        return {
            "itinerary_results": result.model_dump(mode="json"),
            "execution_status": {
                "itinerary_agent": result.status.value,
            },
            "errors": [result.error] if result.error else [],
        }

    except Exception as exc:
        logger.exception("Itinerary node failed.")

        return {
            "execution_status": {"itinerary_agent": "failed"},
            "errors": [f"Itinerary agent node error: {exc}"],
        }


async def response_node(state: TravelState) -> dict[str, Any]:
    """Assemble the final travel plan and calculate its budget."""

    logger.info("Executing response node.")

    try:
        destination_result = (
            DestinationResult.model_validate(state["destination_results"])
            if state.get("destination_results")
            else None
        )

        flight_result = (
            FlightResult.model_validate(state["flight_results"])
            if state.get("flight_results")
            else None
        )

        hotel_result = (
            HotelResult.model_validate(state["hotel_results"])
            if state.get("hotel_results")
            else None
        )

        weather_result = (
            WeatherResult.model_validate(state["weather_results"])
            if state.get("weather_results")
            else None
        )

        itinerary_items = []

        if state.get("itinerary_results"):
            itinerary_data = state["itinerary_results"].get("data", [])

            itinerary_items = [
                DailyItinerary.model_validate(item)
                for item in itinerary_data
            ]

        request = TravelRequest(
            origin=state["origin"],
            destination=state["destination"],
            departure_date=state["departure_date"],
            return_date=state["return_date"],
            travellers=state["travellers"],
            budget=state["budget"],
            currency=state["currency"],
            travel_preferences=state.get("travel_preferences"),
            accommodation_preference=state.get(
                "accommodation_preference"
            ),
            travel_style=TravelStyle(state["travel_style"]),
        )

        plan = await run_response_agent(
            trip_id=state["trip_id"],
            request=request,
            duration_days=state["duration_days"],
            destination_res=destination_result,
            flight_res=flight_result,
            hotel_res=hotel_result,
            weather_res=weather_result,
            itinerary_days=itinerary_items,
        )

        return {
            "final_plan": plan.model_dump(mode="json"),
            "execution_status": {
                "response_agent": plan.execution_status.value,
            },
        }

    except Exception as exc:
        logger.exception("Response node failed.")

        return {
            "execution_status": {"response_agent": "failed"},
            "errors": [f"Response agent node error: {exc}"],
        }


async def chat_node(state: TravelState) -> dict[str, Any]:
    """Handle conversational turns using the saved conversation context."""

    thread_id = state.get("thread_id", "")
    logger.info("Executing chat node for thread_id=%s", thread_id)

    messages = state.get("messages", [])
    user_message = messages[-1].content if messages else "Hello"

    trip_context = "No specific trip loaded."

    if state.get("final_plan"):
        plan = state["final_plan"]
        budget = plan.get("budget", {})

        trip_context = (
            f"Trip to {plan.get('destination')} from "
            f"{plan.get('origin')} "
            f"({plan.get('departure_date')} to {plan.get('return_date')}). "
            f"Budget: {budget.get('amount')} {budget.get('currency')}. "
            f"Style: {plan.get('travel_style')}."
        )

    history = "\n".join(
        f"{message.type}: {message.content}"
        for message in messages[:-1]
    )

    prompt = CHAT_AGENT_PROMPT.format(
        trip_context=trip_context,
        history=history or "No previous history.",
        user_message=user_message,
    )

    try:
        llm = get_gemini_client(temperature=0.5)

        response = await llm.ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content=user_message),
            ]
        )

        content = response.content

        if isinstance(content, str):
            assistant_text = content

        elif isinstance(content, list):
            text_parts = []

            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)

                elif isinstance(block, dict):
                    if (
                        block.get("type") == "text"
                        and isinstance(block.get("text"), str)
                    ):
                        text_parts.append(block["text"])

            assistant_text = "\n".join(text_parts)

        else:
            assistant_text = ""

        if not assistant_text.strip():
            raise ValueError("Gemini returned no readable text.")

        return {
            "messages": [
                AIMessage(content=assistant_text)
            ],
        }

    except Exception:
        logger.exception("Chat node failed.")

        fallback_reply = (
            f"I have received your request regarding {trip_context}. "
            "Please try again shortly or let me know if you would like "
            "to adjust your activities, hotel recommendations, or budget."
        )

        return {
            "messages": [
                AIMessage(content=fallback_reply)
            ],
        }
