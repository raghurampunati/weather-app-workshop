"""Thin async client for the free Open-Meteo APIs (no key required)."""

from __future__ import annotations

import httpx

from .models import City, CurrentConditions
from .weather_codes import describe

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

CURRENT_FIELDS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "is_day",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
    ]
)


class OpenMeteoError(RuntimeError):
    """Open-Meteo was unreachable or returned an unusable payload."""


async def search_cities(
    client: httpx.AsyncClient, name: str, count: int = 5
) -> list[City]:
    """Look up cities by name. Returns an empty list when nothing matches."""
    params = {"name": name, "count": count, "language": "en", "format": "json"}
    payload = await _get_json(client, GEOCODING_URL, params)
    return [_to_city(result) for result in payload.get("results", [])]


async def fetch_current(
    client: httpx.AsyncClient, city: City
) -> CurrentConditions:
    """Fetch current conditions for an already-geocoded city."""
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": CURRENT_FIELDS,
        "timezone": "auto",
    }
    payload = await _get_json(client, FORECAST_URL, params)

    try:
        current = payload["current"]
        units = payload["current_units"]
    except KeyError as exc:
        raise OpenMeteoError("forecast response is missing its 'current' block") from exc

    code = int(current["weather_code"])
    description, icon = describe(code)

    return CurrentConditions(
        time=current["time"],
        temperature=current["temperature_2m"],
        temperature_unit=units["temperature_2m"],
        apparent_temperature=current["apparent_temperature"],
        humidity=current["relative_humidity_2m"],
        precipitation=current["precipitation"],
        precipitation_unit=units["precipitation"],
        wind_speed=current["wind_speed_10m"],
        wind_speed_unit=units["wind_speed_10m"],
        weather_code=code,
        description=description,
        icon=icon,
        is_day=bool(current["is_day"]),
    )


async def _get_json(
    client: httpx.AsyncClient, url: str, params: dict
) -> dict:
    try:
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc


def _to_city(result: dict) -> City:
    parts = [result["name"], result.get("admin1"), result.get("country")]
    return City(
        id=result["id"],
        name=result["name"],
        country=result.get("country"),
        admin1=result.get("admin1"),
        latitude=result["latitude"],
        longitude=result["longitude"],
        timezone=result.get("timezone"),
        label=", ".join(part for part in parts if part),
    )
