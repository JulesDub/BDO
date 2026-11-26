"""Fail-fast checks. Record measured quality, never silently repair invalid facts."""
from __future__ import annotations

import pandas as pd
from src.config import WEATHER_COLUMNS, SITE_COLUMNS
from src.sites import BBOX


class DataQualityError(ValueError):
    pass


def validate_weather(df: pd.DataFrame) -> dict:
    if df.empty or list(df.columns) != list(WEATHER_COLUMNS):
        raise DataQualityError("Schéma météo absent ou colonnes incorrectes")
    if df[["day", "dataset"]].isna().any().any() or df.duplicated(["day", "dataset"]).any():
        raise DataQualityError("Clés météo nulles ou dupliquées")
    if not set(df["dataset"].dropna().unique()).issubset({"history", "forecast"}):
        raise DataQualityError("Valeur dataset météo inattendue")
    if pd.to_datetime(df["day"], format="%Y-%m-%d", errors="coerce").isna().any():
        raise DataQualityError("Date météo invalide")
    numeric_cols = ["temp_max_c", "temp_min_c", "rain_mm", "wind_kmh", "outdoor_score"]
    for name in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[name]):
            raise DataQualityError(f"{name} doit être numérique")
    if (df["rain_mm"].dropna() < 0).any() or (df["wind_kmh"].dropna() < 0).any():
        raise DataQualityError("Précipitations ou vent négatifs")
    if (df["temp_max_c"].dropna().abs() > 70).any() or (df["temp_min_c"].dropna().abs() > 70).any():
        raise DataQualityError("Température hors bornes plausibles")
    if (df["temp_min_c"] > df["temp_max_c"]).fillna(False).any():
        raise DataQualityError("Température minimale supérieure à la maximale")
    if ((df["outdoor_score"] < 0) | (df["outdoor_score"] > 100)).fillna(False).any():
        raise DataQualityError("Score météo hors intervalle")
    if df.groupby("dataset").size().reindex(["history", "forecast"], fill_value=0).eq(0).any():
        raise DataQualityError("Historique ou prévisions absents")
    missing = int(df[numeric_cols].isna().sum().sum())
    completeness = round(100 * (1 - missing / (len(df) * len(numeric_cols))), 2)
    return {"status": "passed", "rows": int(len(df)), "duplicate_keys": 0,
            "missing_measurements": missing, "measurement_completeness_pct": completeness,
            "history_rows": int((df.dataset == "history").sum()),
            "forecast_rows": int((df.dataset == "forecast").sum())}


def validate_sites(df: pd.DataFrame) -> dict:
    if df.empty or list(df.columns) != list(SITE_COLUMNS):
        raise DataQualityError("Schéma des sites absent ou incorrect")
    if df.site_id.isna().any() or df.site_id.duplicated().any():
        raise DataQualityError("Identifiants des sites nuls ou dupliqués")
    if df.name.isna().any() or df.category.isna().any():
        raise DataQualityError("Un site n'a pas de nom ou de catégorie")
    for name in ("latitude", "longitude"):
        if not pd.api.types.is_numeric_dtype(df[name]) or df[name].isna().any():
            raise DataQualityError(f"Coordonnées invalides : {name}")
    south, west, north, east = BBOX
    if not df.latitude.between(south, north).all() or not df.longitude.between(west, east).all():
        raise DataQualityError("Site géographique situé hors de l'emprise étudiée")
    return {"status": "passed", "rows": int(len(df)), "duplicate_ids": 0,
            "categories": int(df.category.nunique()),
            "named_records_pct": round(100 * df.name.notna().mean(), 2),
            "website_pct": round(100 * df.website.fillna("").ne("").mean(), 2)}
