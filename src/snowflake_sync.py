"""Optional, explicit export into demo-only Snowflake tables.

No credentials are stored here. No application data is ever fetched from Snowflake:
Snowflake is an additional learning destination, not a dependency of Streamlit.
"""
from __future__ import annotations

import os
import pandas as pd

from src.config import Paths

TABLES = {
    "BREST_WEATHER_DAILY": (
        "weather_daily.csv",
        "DAY DATE, DATASET VARCHAR(20), TEMP_MAX_C FLOAT, TEMP_MIN_C FLOAT, "
        "RAIN_MM FLOAT, WIND_KMH FLOAT, OUTDOOR_SCORE INTEGER",
    ),
    "BREST_TOURISM_SITES": (
        "sites.csv",
        "SITE_ID VARCHAR(80), NAME VARCHAR(500), CATEGORY VARCHAR(160), "
        "LATITUDE FLOAT, LONGITUDE FLOAT, WEBSITE VARCHAR(2000), OSM_URL VARCHAR(300)",
    ),
}
REQUIRED_ENV = (
    "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
)


def config_from_environment() -> dict:
    missing = [key for key in REQUIRED_ENV if not os.getenv(key)]
    if missing:
        raise RuntimeError("Variables Snowflake manquantes : " + ", ".join(missing))
    return {key.removeprefix("SNOWFLAKE_").lower(): os.environ[key] for key in REQUIRED_ENV}


def sync(paths: Paths | None = None) -> None:
    """Replace two *dedicated demo tables* after validating each staging upload."""
    paths = paths or Paths()
    if not (paths.published / "manifest.json").is_file():
        raise RuntimeError("Exécute d'abord : python -m src.pipeline")
    config = config_from_environment()
    try:
        import snowflake.connector
        from snowflake.connector.pandas_tools import write_pandas
    except ImportError as exc:
        raise RuntimeError("Installe les dépendances de requirements-snowflake.txt") from exc

    from src.quality import validate_weather, validate_sites

    conn = snowflake.connector.connect(**config, session_parameters={"QUERY_TAG": "BREST_PORTFOLIO_DEMO"})
    try:
        with conn.cursor() as cursor:
            for table_name, (filename, schema_sql) in TABLES.items():
                frame = pd.read_csv(paths.published / filename).fillna("")
                if table_name == "BREST_WEATHER_DAILY":
                    frame = pd.read_csv(paths.published / filename)
                    validate_weather(frame)
                    frame["day"] = pd.to_datetime(frame["day"]).dt.date
                else:
                    validate_sites(frame)
                frame.columns = [key.upper() for key in frame.columns]
                stage_name = table_name + "_STAGING"
                cursor.execute(f"CREATE OR REPLACE TABLE {stage_name} ({schema_sql})")
                try:
                    success, _, row_count, _ = write_pandas(conn, frame, stage_name, quote_identifiers=False)
                    if not success or row_count != len(frame):
                        raise RuntimeError(f"Snowflake : chargement partiel {table_name}: {row_count}/{len(frame)}")
                    # Demo-only replacement. Do not reuse these names for production tables.
                    cursor.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {stage_name}")
                    print(f"{table_name}: {row_count} lignes")
                finally:
                    cursor.execute(f"DROP TABLE IF EXISTS {stage_name}")
    finally:
        conn.close()


if __name__ == "__main__":
    sync()
