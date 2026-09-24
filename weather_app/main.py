"""FastAPI application: search a city, show its current weather."""

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import ssl

from . import openmeteo
from .models import City, WeatherResponse

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def build_ssl_context() -> ssl.SSLContext:
    """Build the TLS context for outbound calls.

    Corporate networks that intercept TLS (Zscaler here) re-sign traffic with a
    root CA whose basicConstraints extension is not marked critical. Python 3.13
    turns on VERIFY_X509_STRICT by default, which rejects that root outright.
    When a CA bundle is configured we trust it and relax that one strict check;
    certificates are still fully verified, and environments without a custom
    bundle keep Python's defaults untouched.
    """
    ca_bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if not ca_bundle:
        return ssl.create_default_context()

    context = ssl.create_default_context(cafile=ca_bundle)
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Share one HTTP client across the process, opened and closed with the app."""
    async with httpx.AsyncClient(
        verify=build_ssl_context(),
        headers={"User-Agent": "weather-app-workshop"},
    ) as client:
        app.state.http = client
        yield



app = FastAPI(title="Weather App Workshop", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/cities", response_model=list[City])
async def cities(
    request: Request,
    q: str = Query(min_length=1, description="City name to search for"),
):
    """Return up to five cities matching the query."""
    try:
        return await openmeteo.search_cities(request.app.state.http, q)
    except openmeteo.OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/weather", response_model=WeatherResponse)
async def weather(
    request: Request,
    q: str = Query(min_length=1, description="City name to report on"),
):
    """Geocode the query, then return current conditions for the best match."""
    client = request.app.state.http
    try:
        matches = await openmeteo.search_cities(client, q, count=1)
        if not matches:
            raise HTTPException(status_code=404, detail=f"No city found matching {q!r}")
        city = matches[0]
        current = await openmeteo.fetch_current(client, city)
    except openmeteo.OpenMeteoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return WeatherResponse(city=city, current=current)
