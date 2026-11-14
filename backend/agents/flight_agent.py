
"""Flight specialist agent."""

import asyncio
import time

from backend.api.schemas.travel import (
    AgentStatus,
    FlightInformation,
    FlightResult,
)
from backend.tools.flight_tools import search_flights
from backend.utils.logger import logger


async def run_flight_agent(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
) -> FlightResult:
    """Retrieve and structure flight information from AviationStack."""

    start_time = time.perf_counter()

    logger.info(
        "Flight Agent started: %s -> %s for %s",
        origin,
        destination,
        departure_date,
    )

    try:
        # Retrieve flight schedules without blocking the event loop.
        raw_result = await asyncio.to_thread(
            search_flights,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            limit=5,
        )

        flights_data: list[FlightInformation] = []

        for flight in raw_result.get("flights", []):
            flights_data.append(
                FlightInformation(
                    airline=flight.get("airline"),
                    flight_number=flight.get("flight_number"),
                    departure_airport=flight.get("departure_airport"),
                    arrival_airport=flight.get("arrival_airport"),
                    departure_time=flight.get("departure_time"),
                    arrival_time=flight.get("arrival_time"),
                    flight_status=flight.get("flight_status", "scheduled"),
                    price=None,
                    currency=None,
                    is_verified_price=False,
                    source="AviationStack API",
                    note=flight.get(
                        "note",
                        "Flight timetable information retrieved from AviationStack.",
                    ),
                )
            )

        if flights_data:
            status = AgentStatus.SUCCESS
            limitations = raw_result.get("limitations")
        else:
            status = AgentStatus.UNAVAILABLE
            limitations = raw_result.get("limitations") or (
                f"No flight schedules were returned for {origin} to {destination}. "
                "Check the airport codes and confirm schedules with the airline."
            )

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Flight Agent completed in %.2f seconds with %d flights",
            elapsed,
            len(flights_data),
        )

        return FlightResult(
            status=status,
            data=flights_data,
            source=raw_result.get("source", "AviationStack API"),
            error=raw_result.get("error"),
            limitations=limitations,
        )

    except Exception as exc:
        logger.exception("Flight Agent failed during execution")

        return FlightResult(
            status=AgentStatus.FAILED,
            data=[],
            source="AviationStack API",
            error=str(exc),
            limitations="Flight service error encountered during execution.",
        )
