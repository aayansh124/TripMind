
"""Construct LangGraph workflows with PostgreSQL checkpointing."""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

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

_connection_pool: ConnectionPool | None = None
_checkpointer: PostgresSaver | None = None

travel_workflow = None
chat_workflow = None


def _get_postgres_connection_string() -> str:
    """Convert the SQLAlchemy PostgreSQL URL to a psycopg connection URL."""

    database_url = settings.DATABASE_URL

    return database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )


def initialize_workflows() -> None:
    """Initialize PostgreSQL checkpointing and compile LangGraph workflows."""

    global _connection_pool
    global _checkpointer
    global travel_workflow
    global chat_workflow

    if travel_workflow is not None and chat_workflow is not None:
        return

    logger.info("Initializing PostgreSQL LangGraph checkpointer.")

    try:
        _connection_pool = ConnectionPool(
            conninfo=_get_postgres_connection_string(),
            min_size=1,
            max_size=10,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
            },
            open=False,
        )

        _connection_pool.open(wait=True)

        _checkpointer = PostgresSaver(_connection_pool)
        _checkpointer.setup()

        travel_workflow = build_travel_workflow(_checkpointer)
        chat_workflow = build_chat_workflow(_checkpointer)

        logger.info("LangGraph workflows initialized successfully.")

    except Exception:
        logger.exception("Failed to initialize LangGraph workflows.")

        if _connection_pool is not None:
            _connection_pool.close()

        _connection_pool = None
        _checkpointer = None
        travel_workflow = None
        chat_workflow = None

        raise


def close_workflows() -> None:
    """Close the PostgreSQL checkpoint connection pool."""

    global _connection_pool
    global _checkpointer
    global travel_workflow
    global chat_workflow

    if _connection_pool is not None:
        _connection_pool.close()

    _connection_pool = None
    _checkpointer = None
    travel_workflow = None
    chat_workflow = None

    logger.info("LangGraph PostgreSQL connection pool closed.")


def get_travel_workflow():
    """Return the initialized travel workflow."""

    if travel_workflow is None:
        raise RuntimeError(
            "Travel workflow is not initialized. "
            "Initialize workflows during application startup."
        )

    return travel_workflow


def get_chat_workflow():
    """Return the initialized chat workflow."""

    if chat_workflow is None:
        raise RuntimeError(
            "Chat workflow is not initialized. "
            "Initialize workflows during application startup."
        )

    return chat_workflow


def build_travel_workflow(checkpointer: PostgresSaver):
    """Build the multi-agent travel planning graph."""

    builder = StateGraph(TravelState)

    builder.add_node("destination_agent", destination_node)
    builder.add_node("flight_agent", flight_node)
    builder.add_node("hotel_agent", hotel_node)
    builder.add_node("weather_agent", weather_node)
    builder.add_node("itinerary_agent", itinerary_node)
    builder.add_node("response_agent", response_node)

    builder.add_edge(START, "destination_agent")

    builder.add_edge("destination_agent", "flight_agent")
    builder.add_edge("destination_agent", "hotel_agent")
    builder.add_edge("destination_agent", "weather_agent")

    # Wait for all specialist agents before generating the itinerary.
    builder.add_edge(
        ["flight_agent", "hotel_agent", "weather_agent"],
        "itinerary_agent",
    )

    builder.add_edge("itinerary_agent", "response_agent")
    builder.add_edge("response_agent", END)

    compiled_graph = builder.compile(checkpointer=checkpointer)

    logger.info("Travel planning graph compiled successfully.")

    return compiled_graph


def build_chat_workflow(checkpointer: PostgresSaver):
    """Build the conversational follow-up graph."""

    builder = StateGraph(TravelState)

    builder.add_node("chat_node", chat_node)

    builder.add_edge(START, "chat_node")
    builder.add_edge("chat_node", END)

    compiled_graph = builder.compile(checkpointer=checkpointer)

    logger.info("Chat workflow compiled successfully.")

    return compiled_graph
