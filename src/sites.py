"""Named tourism points of interest around Brest from OpenStreetMap / Overpass."""
from __future__ import annotations

import math
from urllib.parse import urlparse
import pandas as pd
from src.config import SITE_COLUMNS

# Brest and surrounding area; it is not the official administrative boundary.
BBOX = (48.30, -4.69, 48.53, -4.20)  # south, west, north, east
CATEGORIES = {
    "museum": "Musées",
    "attraction": "Attractions",
    "viewpoint": "Points de vue",
    "gallery": "Galeries",
    "aquarium": "Aquariums",
    "zoo": "Parcs animaliers",
    "information": "Information touristique",
}


def overpass_query() -> str:
    south, west, north, east = BBOX
    bbox = f"{south},{west},{north},{east}"
    filt = "^(museum|attraction|viewpoint|gallery|aquarium|zoo|information)$"
    return f'''[out:json][timeout:50];
    (
      node["tourism"~"{filt}"]({bbox});
      way["tourism"~"{filt}"]({bbox});
      relation["tourism"~"{filt}"]({bbox});
    );
    out center;'''


def _public_url(candidate: object) -> str:
    if not isinstance(candidate, str) or not candidate.strip():
        return ""
    candidate = candidate.strip()
    if not candidate.startswith(("https://", "http://")):
        return ""
    parsed = urlparse(candidate)
    return candidate if parsed.hostname else ""


def normalize_sites(payload: dict) -> pd.DataFrame:
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise ValueError("La réponse Overpass ne contient pas une liste 'elements'")
    rows = []
    for item in elements:
        if not isinstance(item, dict):
            continue
        tags = item.get("tags") or {}
        if not isinstance(tags, dict):
            continue
        category = CATEGORIES.get(tags.get("tourism"))
        name = tags.get("name:fr") or tags.get("name")
        geometry = item.get("center") or item
        lat, lon = geometry.get("lat"), geometry.get("lon")
        kind, osm_id = item.get("type"), item.get("id")
        if (not category or not isinstance(name, str) or not name.strip()
                or kind not in ("node", "way", "relation") or not isinstance(osm_id, int)):
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        south, west, north, east = BBOX
        if not (south <= lat <= north and west <= lon <= east):
            continue
        rows.append({
            "site_id": f"{kind}/{osm_id}",
            "name": name.strip(),
            "category": category,
            "latitude": lat,
            "longitude": lon,
            "website": _public_url(tags.get("website") or tags.get("contact:website")),
            "osm_url": f"https://www.openstreetmap.org/{kind}/{osm_id}",
        })
    if not rows:
        raise ValueError("Aucun site touristique nommé avec coordonnées valides")
    df = pd.DataFrame(rows, columns=SITE_COLUMNS)
    return df.drop_duplicates(subset=["site_id"]).sort_values(["category", "name"]).reset_index(drop=True)
