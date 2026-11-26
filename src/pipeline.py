"""Command-line ETL: two live data sources -> checks -> DuckDB -> public CSV.

Usage: python -m src.pipeline
Use --allow-stale-sites to preserve previously validated sites when Overpass is down.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo
from typing import Callable, Any

import pandas as pd

from src.config import BREST, Paths, SITE_COLUMNS, SOURCE_URLS
from src.http_client import make_session, get_json, overpass_json
from src.quality import validate_weather, validate_sites
from src.sites import normalize_sites, overpass_query
from src.storage import write_json, write_csv
from src.weather import load_weather
from src.warehouse import create_warehouse


def run_pipeline(
    *,
    today: date | None = None,
    paths: Paths | None = None,
    weather_fetcher: Callable[[str, dict[str, Any]], dict] | None = None,
    sites_fetcher: Callable[[], tuple[dict, str]] | None = None,
    allow_stale_sites: bool = False,
) -> dict:
    paths = paths or Paths()
    today = today or datetime.now(ZoneInfo(BREST["timezone"])).date()
    run_id = f"{today.isoformat()}-{uuid4().hex[:8]}"
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    session = None
    if weather_fetcher is None or sites_fetcher is None:
        session = make_session()
    if weather_fetcher is None:
        weather_fetcher = lambda url, params: get_json(url, params=params, session=session)
    if sites_fetcher is None:
        sites_fetcher = lambda: overpass_json(
            overpass_query(),
            session=session,
            endpoints=(SOURCE_URLS["sites_primary"], SOURCE_URLS["sites_backup"]),
        )
    try:
        weather, raw_weather = load_weather(today, weather_fetcher)
        weather_quality = validate_weather(weather)

        sites_fallback = False
        source_url = ""
        raw_sites = None
        site_error = None
        try:
            raw_sites, source_url = sites_fetcher()
            sites = normalize_sites(raw_sites)
            sites_quality = validate_sites(sites)
        except Exception as exc:
            # Stale data is an opt-in operation, never a silent replacement.
            if not allow_stale_sites:
                raise
            old_file = paths.published / "sites.csv"
            if not old_file.exists():
                raise RuntimeError("Sites indisponibles et aucun export précédent utilisable") from exc
            sites = pd.read_csv(old_file, dtype={"site_id": "string"}).fillna("")
            sites = sites[list(SITE_COLUMNS)]
            sites_quality = validate_sites(sites)
            sites_fallback = True
            site_error = str(exc)
            source_url = "https://www.openstreetmap.org"

        exports = create_warehouse(weather, sites, paths)
        # Only public, validated data are committed. Raw API payloads stay local.
        for name, frame in exports.items():
            write_csv(paths.published / name, frame)
        if raw_sites is not None:
            write_json(paths.raw / f"{run_id}_sites.json", raw_sites)
        for key, payload in raw_weather.items():
            write_json(paths.raw / f"{run_id}_{key}.json", payload)
        metadata = {
            "run_id": run_id,
            "status": "success_with_stale_sites" if sites_fallback else "success",
            "started_at_utc": started,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reference_day_local": today.isoformat(),
            "source": {
                "weather_history": SOURCE_URLS["historical"],
                "weather_forecast": SOURCE_URLS["forecast"],
                "sites": source_url,
                "sites_license": "OpenStreetMap contributors — ODbL",
                "weather_license": "Open-Meteo — CC BY 4.0",
                "sites_fallback": sites_fallback,
                "sites_error": site_error,
            },
            "quality": {"weather": weather_quality, "sites": sites_quality},
            "export_rows": {name: len(df) for name, df in exports.items()},
        }
        write_json(paths.published / "manifest.json", metadata)  # Last operation on purpose.
        return metadata
    finally:
        if session is not None:
            session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion et publication des données ouvertes brestoises")
    parser.add_argument("--allow-stale-sites", action="store_true", help="Réutilise l'export sites précédent si Overpass ne répond pas")
    args = parser.parse_args()
    result = run_pipeline(allow_stale_sites=args.allow_stale_sites)
    print(f"Exécution : {result['status']} | ID : {result['run_id']}")
    for name, size in result["export_rows"].items():
        print(f"  {name}: {size} lignes")
    print("Entrepôt : data/local/observatory.duckdb")
    print("Dashboard : python -m streamlit run app.py")


if __name__ == "__main__":
    main()
