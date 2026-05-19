import re
from typing import Optional

from fast_flights import FlightData, Passengers, get_flights

_AIRLINE_PATTERNS = {
    "Air France":   re.compile(r"air\s+france",       re.IGNORECASE),
    "Air Caraïbes": re.compile(r"air\s+cara[ïi]bes",  re.IGNORECASE),
    "Corsair":      re.compile(r"corsair",             re.IGNORECASE),
}


class GoogleFlightsScraper:
    name = "Google Flights"

    def get_prices(self, outbound: str, return_date: str) -> dict[str, float]:
        """Récupère les prix aller-retour ORY→FDF via fast-flights (HTTP direct)."""
        try:
            result = get_flights(
                flight_data=[
                    FlightData(date=outbound,     from_airport="ORY", to_airport="FDF"),
                    FlightData(date=return_date,  from_airport="FDF", to_airport="ORY"),
                ],
                trip="round-trip",
                seat="economy",
                passengers=Passengers(adults=2, children=1,
                                      infants_in_seat=0, infants_on_lap=0),
                fetch_mode="fallback",
            )
        except Exception as e:
            print(f"[GoogleFlights] Erreur API {outbound}→{return_date}: {e}")
            return {}

        if not result or not result.flights:
            print(f"[GoogleFlights] Aucun vol retourné pour {outbound}→{return_date}")
            return {}

        prices: dict[str, float] = {}
        for flight in result.flights:
            airline = _normalize_airline(flight.name or "")
            if airline is None:
                continue
            price_text = getattr(flight, "price", None) or ""
            price = _parse_price(str(price_text))
            if price is None:
                continue
            if airline not in prices or price < prices[airline]:
                prices[airline] = price
            print(f"[GoogleFlights] Vol trouvé: {flight.name!r} {price_text!r} → {airline} {price:.0f}€")

        return prices


def _normalize_airline(text: str) -> Optional[str]:
    for name, pattern in _AIRLINE_PATTERNS.items():
        if pattern.search(text):
            return name
    return None


def _parse_price(text: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d\s,.]", "", text).strip()
    cleaned = re.sub(r"(\d)\s(\d)", r"\1\2", cleaned)
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None
