"""Constants for the Unagi integration."""

from __future__ import annotations

DOMAIN = "unagi"
NAME = "Unagi Electricity Price Forecast"
VERSION = "0.1.0"

CONF_AREA = "area"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"

AREAS = ("SE1", "SE2", "SE3", "SE4")
UPDATE_INTERVAL_OPTIONS = (3, 6, 12, 24)
DEFAULT_UPDATE_INTERVAL_HOURS = 6

API_BASE_URL = "https://catch.unagieel.net/v1/forecast"
API_TIMEOUT_SECONDS = 20
SOURCE_TIME_ZONE = "Europe/Stockholm"

ATTR_FORECAST_DATA = "raw_forecast"
ATTR_ACCURACY = "accuracy"
