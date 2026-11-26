from __future__ import annotations

import pandas as pd
import pytest
from src.weather import outdoor_score, normalize_weather, load_weather
from src.quality import DataQualityError, validate_weather
from datetime import date


def test_score_dry_and_temperate():
    assert outdoor_score(20, 0, 20) == 100


def test_score_capped():
    assert 0 <= outdoor_score(-30, 200, 120) <= 100


def test_score_missing():
    assert outdoor_score(20, None, 20) is None


def test_score_falls_when_rain_increases():
    assert outdoor_score(18, 2, 20) < outdoor_score(18, 0, 20)


def test_parse_weather(weather_api_payload):
    table = normalize_weather(weather_api_payload, "history")
    assert list(table.columns) == ["day", "dataset", "temp_max_c", "temp_min_c", "rain_mm", "wind_kmh", "outdoor_score"]
    assert len(table) == 3
    assert table.rain_mm.sum() == 7


def test_missing_daily_field(weather_api_payload):
    del weather_api_payload["daily"]["precipitation_sum"]
    with pytest.raises(ValueError):
        normalize_weather(weather_api_payload, "history")


def test_inconsistent_daily_lengths(weather_api_payload):
    weather_api_payload["daily"]["time"].pop()
    with pytest.raises(ValueError):
        normalize_weather(weather_api_payload, "forecast")


def test_bad_temperature_rejected(weather_api_payload):
    table = normalize_weather(weather_api_payload, "history")
    table.loc[0, "temp_min_c"] = 100
    with pytest.raises(DataQualityError):
        validate_weather(table)


def test_duplicate_day_rejected(weather_api_payload):
    table = normalize_weather(weather_api_payload, "history")
    table = pd.concat([table, table.iloc[:1]], ignore_index=True)
    with pytest.raises(DataQualityError):
        validate_weather(table)


def test_weather_fetcher_injected(weather_api_payload):
    calls = []
    def fake_fetch(url, params):
        calls.append((url, params))
        return weather_api_payload
    frame, raw = load_weather(date(2026, 11, 18), fake_fetch)
    assert len(frame) == 6
    assert len(calls) == 2
    assert calls[0][1]["end_date"] == "2026-11-11"
    assert calls[1][1]["forecast_days"] == 7
