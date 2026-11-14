"""Flight Specialist Agent."""

import time
from typing import List, Optional
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
    """Execute flight intelligence query using AviationStack and format verified details.

    Returns:
        Structured FlightResult.
    """
    start_time = time.time()
    logger.info("Flight Agent started: %s -> %s for %s", origin, destination, departure_date)

    try:
        raw_result = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            limit=5,
        )

        flights_data: List[FlightInformation] = []
        raw_flights = raw_result.get("flights", [])

        for f in raw_flights:
            flights_data.append(
                FlightInformation(
                    airline=f.get("airline"),
                    flight_number=f.get("flight_number"),
                    departure_airport=f.get("departure_airport"),
                    arrival_airport=f.get("arrival_airport"),
                    departure_time=f.get("departure_time"),
                    arrival_time=f.get("arrival_time"),
                    flight_status=f.get("flight_status", "scheduled"),
                    price=None,  # Preserved as None; never fabricated
                    currency=None,
                    is_verified_price=False,
                    source="AviationStack API",
                    note=f.get("note", "Flight timetable status."),
                )
            )

        status = AgentStatus.SUCCESS if flights_data else AgentStatus.UNAVAILABLE
        limitations = raw_result.get("limitations")

        if not flights_data:
            limitations = (
                f"No scheduled flights found between '{origin}' and '{destination}' via AviationStack API. "
                "AviationStack requires specific IATA airport codes (e.g. JFK, LHR) or active commercial carrier feeds. "
                "Prices and live inventory are not supported by the public feed and must be confirmed via airline portals."
            )

        elapsed = time.time() - start_time
        logger.info("Flight Agent completed in %.2fs with %d flights", elapsed, len(flights_data))

        return FlightResult(
            status=status,
            data=flights_data,
            source=raw_result.get("source", "AviationStack API"),
            error=raw_result.get("error"),
            limitations=limitations,
        )

    except Exception as e:
        logger.error("Flight Agent encountered an exception: %s", e)
        return FlightResult(
            status=AgentStatus.FAILED,
            data=[],
            source="AviationStack API",
            error=str(e),
            limitations="Flight service error encountered during execution.",
        )

