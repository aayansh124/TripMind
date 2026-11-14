"""Recommendation ranking and filtering service for destinations, activities, and hotels."""

from typing import Any, Dict, List, Optional
from backend.api.schemas.travel import HotelInformation, TravelStyle
from backend.utils.logger import logger


class RecommendationService:
    """Service providing filtering and ranking algorithms for travel recommendations."""

    @staticmethod
    def filter_hotels_by_budget(
        hotels: List[HotelInformation],
        max_nightly_rate: float,
    ) -> List[HotelInformation]:
        """Filter hotel list to accommodations strictly within the target nightly rate."""
        if not hotels:
            return []

        filtered = [
            h for h in hotels
            if h.estimated_price_per_night is None or h.estimated_price_per_night <= max_nightly_rate
        ]
        logger.debug(
            "Filtered %d hotels down to %d based on max rate of %.2f",
            len(hotels),
            len(filtered),
            max_nightly_rate,
        )
        return filtered or hotels

    @staticmethod
    def rank_attractions_by_style(
        attractions: List[str],
        travel_style: TravelStyle,
    ) -> List[str]:
        """Prioritize attractions that align with the specified travel style keywords."""
        if not attractions:
            return []

        style_keywords = {
            TravelStyle.CULTURAL: ["museum", "temple", "palace", "cathedral", "historic", "art", "heritage"],
            TravelStyle.ADVENTURE: ["hike", "trail", "mountain", "climb", "dive", "safari", "rafting", "outdoor"],
            TravelStyle.LUXURY: ["spa", "fine dining", "exclusive", "private", "lounge", "rooftop", "yacht"],
            TravelStyle.FAMILY: ["park", "aquarium", "zoo", "interactive", "garden", "beach", "kid"],
            TravelStyle.ROMANTIC: ["sunset", "cruise", "view", "garden", "wine", "promenade", "scenic"],
            TravelStyle.BUDGET: ["free", "walking tour", "public", "market", "plaza", "square", "street"],
            TravelStyle.STANDARD: [],
        }

        keywords = style_keywords.get(travel_style, [])
        if not keywords:
            return attractions

        def relevance_score(attraction: str) -> int:
            attraction_lower = attraction.lower()
            return sum(1 for kw in keywords if kw in attraction_lower)

        ranked = sorted(attractions, key=relevance_score, reverse=True)
        return ranked

