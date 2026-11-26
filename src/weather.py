"""Weather ingestion and transparent, non-scientific outdoor score."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, Any

import pandas as pd

from src.config import BREST, WEATHER_COLUMNS, WEATHER_VARIABLES, SOURCE_URLS


def outdoor_score(temp_max_c: float | None, rain_mm: float | None, wind_kmh: float | None) -> int | None:
    """Illustrative heuristic; not a visitor forecast or official safety recommendation."""
    if any(pd.isna(v) for v in (temp_max_c, rain_mm, wind_kmh)):
        return None
    value = 100.0 - min(65.0, 14.0 * float(rain_mm))
    value -= 1.7 * max(0.0, float(wind_kmh) - 20.0)
    value -= 1.2 * abs(float(temp_max_c) - 20.0)
    return max(0, min(100, round(value)))


def normalize_weather(payload: dict, dataset: str) -> pd.DataFrame:
    if dataset not in ("history", "forecast"):
        raise ValueError(f"Jeu météo inconnu : {dataset}")
    block = payload.get("daily")
    if not isinstance(block, dict):
        raise ValueError("La réponse Open-Meteo ne contient pas l'objet 'daily'")
    source_to_target = {
        "time": "day",
        "temperature_2m_max": "temp_max_c",
        "temperature_2m_min": "temp_min_c",
        "precipitation_sum": "rain_mm",
        "wind_speed_10m_max": "wind_kmh",
    }
    if any(not isinstance(block.get(source), list) for source in source_to_target):
        raise ValueError("Colonne quotidienne manquante dans la réponse Open-Meteo")
    counts = {len(block[source]) for source in source_to_target}
    if len(counts) != 1 or not next(iter(counts)):
        raise ValueError("Longueurs de colonnes météo incohérentes ou jeu vide")
    frame = pd.DataFrame({target: block[source] for source, target in source_to_target.items()})
    frame["day"] = pd.to_datetime(frame["day"], format="%Y-%m-%d", errors="raise").dt.strftime("%Y-%m-%d")
    for col in ("temp_max_c", "temp_min_c", "rain_mm", "wind_kmh"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["dataset"] = dataset
    frame["outdoor_score"] = [
        outdoor_score(t, r, w) for t, r, w in zip(frame.temp_max_c, frame.rain_mm, frame.wind_kmh)
    ]
    return frame[list(WEATHER_COLUMNS)]


def load_weather(today: date, fetcher: Callable[[str, dict[str, Any]], dict]) -> tuple[pd.DataFrame, dict]:
    common = {
        "latitude": BREST["latitude"],
        "longitude": BREST["longitude"],
        "timezone": BREST["timezone"],
        "daily": ",".join(WEATHER_VARIABLES),
    }
    archive_end = today - timedelta(days=7)
    archive_start = archive_end - timedelta(days=179)
    history_params = {**common, "start_date": archive_start.isoformat(), "end_date": archive_end.isoformat()}
    forecast_params = {**common, "forecast_days": 7}
    raw_history = fetcher(SOURCE_URLS["historical"], history_params)
    raw_forecast = fetcher(SOURCE_URLS["forecast"], forecast_params)
    history = normalize_weather(raw_history, "history")
    future = normalize_weather(raw_forecast, "forecast")
    weather = pd.concat([history, future], ignore_index=True).sort_values(["day", "dataset"]).reset_index(drop=True)
    return weather, {"history": raw_history, "forecast": raw_forecast}
