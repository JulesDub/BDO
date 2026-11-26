from __future__ import annotations

import pytest


@pytest.fixture
def weather_api_payload():
    return {
        "daily": {
            "time": ["2026-11-01", "2026-11-02", "2026-11-03"],
            "temperature_2m_max": [14.0, 12.0, 15.0],
            "temperature_2m_min": [8.0, 7.0, 11.0],
            "precipitation_sum": [0.0, 2.0, 5.0],
            "wind_speed_10m_max": [20.0, 25.0, 30.0],
        }
    }


@pytest.fixture
def osm_api_payload():
    return {
        "elements": [
            {"type": "node", "id": 1, "lat": 48.3904, "lon": -4.4861,
             "tags": {"name": "Lieu alpha", "tourism": "museum", "website": "https://example.org"}},
            {"type": "way", "id": 2, "center": {"lat": 48.40, "lon": -4.50},
             "tags": {"name": "Point de vue beta", "tourism": "viewpoint"}},
            {"type": "node", "id": 3, "lat": 48.41, "lon": -4.48,
             "tags": {"tourism": "attraction"}},  # unnamed: excluded
        ]
    }
