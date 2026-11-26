"""Configuration and filesystem layout. No secrets are stored in this module."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def published(self) -> Path:
        return self.root / "data" / "published"

    @property
    def local(self) -> Path:
        return self.root / "data" / "local"

    @property
    def warehouse(self) -> Path:
        return self.local / "observatory.duckdb"

    @property
    def model_sql(self) -> Path:
        return self.root / "sql" / "models.sql"


BREST = {"latitude": 48.3904, "longitude": -4.4861, "timezone": "Europe/Paris"}
WEATHER_VARIABLES = (
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
)

WEATHER_COLUMNS = (
    "day", "dataset", "temp_max_c", "temp_min_c", "rain_mm", "wind_kmh", "outdoor_score"
)
SITE_COLUMNS = (
    "site_id", "name", "category", "latitude", "longitude", "website", "osm_url"
)
SOURCE_URLS = {
    "historical": "https://archive-api.open-meteo.com/v1/archive",
    "forecast": "https://api.open-meteo.com/v1/forecast",
    "sites_primary": "https://overpass.private.coffee/api/interpreter",
    "sites_backup": "https://ovp.dresel.systems/api/interpreter",
}
