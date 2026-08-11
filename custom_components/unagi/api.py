"""Client for the public Unagi forecast feed."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE_URL, API_TIMEOUT_SECONDS, AREAS


class UnagiApiError(Exception):
    """Base exception for Unagi API errors."""


class UnagiApiConnectionError(UnagiApiError):
    """Raised when the Unagi feed cannot be reached."""


class UnagiApiDataError(UnagiApiError):
    """Raised when the Unagi feed returns unexpected data."""


class UnagiApiClient:
    """Small client for Unagi's static public JSON feed."""

    def __init__(self, session: ClientSession, area: str) -> None:
        self._session = session
        self._area = area.upper()

    async def async_get_forecast(self) -> dict[str, Any]:
        """Fetch and minimally validate one area's forecast document."""
        if self._area not in AREAS:
            raise UnagiApiDataError(f"Unsupported bidding area: {self._area}")

        url = f"{API_BASE_URL}/{self._area}.json"
        try:
            async with asyncio.timeout(API_TIMEOUT_SECONDS):
                async with self._session.get(
                    url,
                    headers={"Accept": "application/json"},
                ) as response:
                    response.raise_for_status()
                    payload = await response.json(content_type=None)
        except (TimeoutError, ClientResponseError, ClientError) as err:
            raise UnagiApiConnectionError(str(err)) from err
        except ValueError as err:
            raise UnagiApiDataError("Unagi returned invalid JSON") from err

        if not isinstance(payload, dict):
            raise UnagiApiDataError("Unagi response is not a JSON object")
        if payload.get("area") != self._area:
            raise UnagiApiDataError(
                f"Unexpected area in response: {payload.get('area')!r}"
            )
        if payload.get("schema_version") != 1:
            raise UnagiApiDataError(
                f"Unsupported Unagi schema version: {payload.get('schema_version')!r}"
            )
        if not isinstance(payload.get("days"), list):
            raise UnagiApiDataError("Unagi response is missing days[]")

        for day in payload["days"]:
            if not isinstance(day, dict):
                raise UnagiApiDataError("Invalid item in days[]")
            if not isinstance(day.get("date"), str):
                raise UnagiApiDataError("A day is missing its date")
            if day.get("kind") not in ("actual", "forecast"):
                raise UnagiApiDataError(
                    f"Unexpected day kind: {day.get('kind')!r}"
                )
            if not isinstance(day.get("hours"), list):
                raise UnagiApiDataError("A day is missing hours[]")

        return payload
