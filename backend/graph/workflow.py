"""LangGraph workflow construction with parallel execution and checkpointing."""

import os
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.clients.database import check_db_health
from backend.config.settings import get_settings
from backend.graph.nodes import (
    chat_node,
    destination_node,
    flight_node,
    hotel_node,
    itinerary_node,
    response_node,
    weather_node,
)
from backend.graph.state import TravelState
from backend.utils.logger import logger

settings = get_settings()

# In-memory checkpointer singleton for fast memory/offline fallback
_memory_saver = MemorySaver()


def get_checkpointer() -> Any:
    """Retrieve LangGraph checkpointer (PostgresSaver if DB is available, otherwise MemorySaver)."""
    if (
        os.getenv("TESTING") != "1"
        and check_db_health() == "connected"
        and settings.DATABASE_URL.startswith("postgres")
    ):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            # Connect to PostgreSQL checkpointer
            saver = PostgresSaver.from_conn_string(settings.DATABASE_URL)
            saver.setup()
            logger.info("Using PostgreSQL LangGraph checkpointer.")
            return saver
        except Exception as e:
            logger.warning("Could not initialize PostgresSaver (%s). Falling back to MemorySaver.", e)

    return _memory_saver


def build_travel_workflow() -> Any:
    """Construct and compile the primary multi-agent travel planning graph with parallel fan-out/in."""
    builder = StateGraph(TravelState)

    # 1. Add all Agent Nodes
    builder.add_node("destination_agent", destination_node)
    builder.add_node("flight_agent", flight_node)
    builder.add_node("hotel_agent", hotel_node)
    builder.add_node("weather_agent", weather_node)
    builder.add_node("itinerary_agent", itinerary_node)
    builder.add_node("response_agent", response_node)

    # 2. Define Execution Edges
    # START -> Destination Agent
    builder.add_edge(START, "destination_agent")

    # Destination Agent -> PARALLEL Fan-Out to Flight, Hotel, and Weather Agents
    builder.add_edge("destination_agent", "flight_agent")
    builder.add_edge("destination_agent", "hotel_agent")
    builder.add_edge("destination_agent", "weather_agent")

    # PARALLEL Fan-In: Flight, Hotel, and Weather Agents -> Itinerary Agent
    builder.add_edge("flight_agent", "itinerary_agent")
    builder.add_edge("hotel_agent", "itinerary_agent")
    builder.add_edge("weather_agent", "itinerary_agent")

    # Itinerary Agent -> Response Agent -> END
    builder.add_edge("itinerary_agent", "response_agent")
    builder.add_edge("response_agent", END)

    checkpointer = get_checkpointer()
    compiled_graph = builder.compile(checkpointer=checkpointer)
    logger.info("Compiled Multi-Agent Travel Planning StateGraph with parallel execution.")
    return compiled_graph


def build_chat_workflow() -> Any:
    """Construct and compile the conversational follow-up graph."""
    builder = StateGraph(TravelState)
    builder.add_node("chat_node", chat_node)
    builder.add_edge(START, "chat_node")
    builder.add_edge("chat_node", END)

    checkpointer = get_checkpointer()
    compiled_chat = builder.compile(checkpointer=checkpointer)
    logger.info("Compiled Conversational LangGraph StateGraph.")
    return compiled_chat


# Pre-compiled workflow singletons
travel_workflow = build_travel_workflow()
chat_workflow = build_chat_workflow()

