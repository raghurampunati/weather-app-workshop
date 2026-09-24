"""API tests with Open-Meteo mocked out via respx."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from weather_app.main import app

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

GEOCODING_PAYLOAD = {
    "results": [
        {
            "id": 2643743,
            "name": "London",
            "latitude": 51.50853,
            "longitude": -0.12574,
            "country": "United Kingdom",
            "admin1": "England",
            "timezone": "Europe/London",
        }
    ]
}

FORECAST_PAYLOAD = {
    "current": {
        "time": "2026-09-23T14:00",
        "temperature_2m": 17.4,
        "relative_humidity_2m": 72,
        "apparent_temperature": 16.1,
        "is_day": 1,
        "precipitation": 0.0,
        "weather_code": 3,
        "wind_speed_10m": 11.2,
    },
    "current_units": {
        "temperature_2m": "°C",
        "precipitation": "mm",
        "wind_speed_10m": "km/h",
    },
}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@respx.mock
def test_city_search_returns_labelled_matches(client):
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_PAYLOAD)
    )

    response = client.get("/api/cities", params={"q": "London"})

    assert response.status_code == 200
    assert response.json()[0]["label"] == "London, England, United Kingdom"


@respx.mock
def test_weather_reports_current_conditions(client):
    respx.get(GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODING_PAYLOAD)
    )
    respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_PAYLOAD)
    )

    response = client.get("/api/weather", params={"q": "London"})

    assert response.status_code == 200
    body = response.json()
    assert body["city"]["name"] == "London"
    assert body["current"]["temperature"] == 17.4
    assert body["current"]["description"] == "Overcast"
    assert body["current"]["is_day"] is True


@respx.mock
def test_unknown_city_returns_404(client):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json={}))

    response = client.get("/api/weather", params={"q": "Atlantis"})

    assert response.status_code == 404


@respx.mock
def test_upstream_failure_returns_502(client):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(503))

    response = client.get("/api/weather", params={"q": "London"})

    assert response.status_code == 502


def test_missing_query_is_rejected(client):
    assert client.get("/api/weather").status_code == 422
