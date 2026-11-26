"""Local analytical warehouse: persist data and materialize SQL marts with DuckDB."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import os
import pandas as pd

from src.config import Paths

EXPORTS = {
    "weather_daily.csv": "SELECT * FROM fact_weather_daily ORDER BY day, dataset",
    "sites.csv": "SELECT * FROM dim_site ORDER BY category, name",
    "weather_monthly.csv": "SELECT * FROM mart_weather_monthly ORDER BY year_month, dataset",
    "sites_by_category.csv": "SELECT * FROM mart_sites_category ORDER BY site_count DESC, category",
    "forecast.csv": "SELECT * FROM mart_forecast ORDER BY day",
}


def create_warehouse(weather: pd.DataFrame, sites: pd.DataFrame, paths: Paths) -> dict[str, pd.DataFrame]:
    """Build an entire new DB file, then atomically replace the previous warehouse.

    Exports are computed from this same validated snapshot, not from two unrelated
    interpretations of the transformation rules.
    """
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("DuckDB manquant. Lance python -m pip install -r requirements.txt") from exc
    paths.local.mkdir(parents=True, exist_ok=True)
    temp = paths.local / f".building-{uuid4().hex}.duckdb"
    try:
        with duckdb.connect(str(temp)) as connection:
            connection.register("weather_input", weather)
            connection.register("sites_input", sites)
            connection.execute("""
                CREATE TABLE fact_weather_daily AS
                SELECT CAST(day AS DATE) AS day,
                       CAST(dataset AS VARCHAR) AS dataset,
                       CAST(temp_max_c AS DOUBLE) AS temp_max_c,
                       CAST(temp_min_c AS DOUBLE) AS temp_min_c,
                       CAST(rain_mm AS DOUBLE) AS rain_mm,
                       CAST(wind_kmh AS DOUBLE) AS wind_kmh,
                       CAST(outdoor_score AS INTEGER) AS outdoor_score
                FROM weather_input
            """)
            connection.execute("""
                CREATE TABLE dim_site AS
                SELECT CAST(site_id AS VARCHAR) AS site_id,
                       CAST(name AS VARCHAR) AS name,
                       CAST(category AS VARCHAR) AS category,
                       CAST(latitude AS DOUBLE) AS latitude,
                       CAST(longitude AS DOUBLE) AS longitude,
                       CAST(website AS VARCHAR) AS website,
                       CAST(osm_url AS VARCHAR) AS osm_url
                FROM sites_input
            """)
            connection.execute(paths.model_sql.read_text(encoding="utf-8"))
            # Assert that importing has not changed row counts.
            if connection.execute("SELECT COUNT(*) FROM fact_weather_daily").fetchone()[0] != len(weather):
                raise RuntimeError("DuckDB : nombre de lignes météo inattendu")
            if connection.execute("SELECT COUNT(*) FROM dim_site").fetchone()[0] != len(sites):
                raise RuntimeError("DuckDB : nombre de sites inattendu")
            exports = {name: connection.execute(sql).df() for name, sql in EXPORTS.items()}
        os.replace(temp, paths.warehouse)
        return exports
    finally:
        if temp.exists():
            temp.unlink()
