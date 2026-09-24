"""Response schemas for the weather API."""

from pydantic import BaseModel


class City(BaseModel):
    """A geocoding match from Open-Meteo."""

    id: int
    name: str
    country: str | None = None
    admin1: str | None = None
    latitude: float
    longitude: float
    timezone: str | None = None
    label: str


class CurrentConditions(BaseModel):
    """Current weather at a single location."""

    time: str
    temperature: float
    temperature_unit: str
    apparent_temperature: float
    humidity: int
    precipitation: float
    precipitation_unit: str
    wind_speed: float
    wind_speed_unit: str
    weather_code: int
    description: str
    icon: str
    is_day: bool


class WeatherResponse(BaseModel):
    city: City
    current: CurrentConditions

