from datetime import date
import pandas as pd
import pytest
from src.config import Paths
from src.pipeline import run_pipeline
from src.storage import read_json


def test_complete_etl_offline(tmp_path, weather_api_payload, osm_api_payload):
    pytest.importorskip("duckdb")
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    sql_dir.joinpath("models.sql").write_text((Paths().model_sql).read_text(encoding="utf-8"), encoding="utf-8")
    result = run_pipeline(
        today=date(2026, 11, 18), paths=Paths(tmp_path),
        weather_fetcher=lambda _url, _params: weather_api_payload,
        sites_fetcher=lambda: (osm_api_payload, "https://example.org/overpass"),
    )
    assert result["status"] == "success"
    assert (tmp_path / "data" / "local" / "observatory.duckdb").exists()
    assert (tmp_path / "data" / "published" / "weather_monthly.csv").exists()
    assert len(pd.read_csv(tmp_path / "data" / "published" / "sites.csv")) == 2
    assert read_json(tmp_path / "data" / "published" / "manifest.json")["quality"]["sites"]["rows"] == 2


def test_failed_sites_not_published(tmp_path, weather_api_payload):
    def unavailable():
        raise RuntimeError("Overpass indisponible")
    with pytest.raises(RuntimeError):
        run_pipeline(
            today=date(2026, 11, 18), paths=Paths(tmp_path),
            weather_fetcher=lambda _url, _params: weather_api_payload,
            sites_fetcher=unavailable,
        )
    assert not (tmp_path / "data" / "published" / "manifest.json").exists()
