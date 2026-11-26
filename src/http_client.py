"""Small HTTP transport. Retries are limited to transient errors."""
from __future__ import annotations

from typing import Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DataSourceError(RuntimeError):
    pass


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "BrestDataObservatory/3.0 (educational open-data project)"})
    retry = Retry(
        total=2,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(("GET",)),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def get_json(url: str, *, params: dict[str, Any], session: requests.Session) -> dict:
    try:
        response = session.get(url, params=params, timeout=(10, 40))
        response.raise_for_status()
        document = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise DataSourceError(f"GET {url}: {exc}") from exc
    if not isinstance(document, dict):
        raise DataSourceError(f"GET {url}: réponse JSON non objet")
    return document


def overpass_json(query: str, *, session: requests.Session, endpoints: tuple[str, ...]) -> tuple[dict, str]:
    """A public, read-only Overpass query. POST is not retried automatically."""
    last_error = ""
    for endpoint in endpoints:
        try:
            response = session.post(endpoint, data={"data": query}, timeout=(12, 75))
            response.raise_for_status()
            document = response.json()
            if not isinstance(document, dict) or not isinstance(document.get("elements"), list):
                raise ValueError("réponse Overpass sans elements")
            return document, endpoint
        except (requests.RequestException, ValueError) as exc:
            last_error = f"{endpoint}: {exc}"
    raise DataSourceError(f"Source des sites indisponible : {last_error}")
