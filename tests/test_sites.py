import pytest
from src.sites import normalize_sites, overpass_query
from src.quality import validate_sites, DataQualityError


def test_parse_osm_geometry_and_category(osm_api_payload):
    sites = normalize_sites(osm_api_payload)
    assert len(sites) == 2
    assert set(sites.category) == {"Musées", "Points de vue"}
    assert sites.site_id.is_unique
    assert validate_sites(sites)["website_pct"] == 50.0


def test_deduplicate_sites(osm_api_payload):
    osm_api_payload["elements"].append(osm_api_payload["elements"][0])
    assert len(normalize_sites(osm_api_payload)) == 2


def test_unnamed_sites_do_not_become_fake_names():
    with pytest.raises(ValueError):
        normalize_sites({"elements": [{"type": "node", "id": 1, "lat": 48.4, "lon": -4.5,
                                       "tags": {"tourism": "museum"}}]})


def test_out_of_bounds_rejected(osm_api_payload):
    frame = normalize_sites(osm_api_payload)
    frame.loc[0, "latitude"] = 70.0
    with pytest.raises(DataQualityError):
        validate_sites(frame)


def test_query_is_geographically_bounded():
    query = overpass_query()
    assert "48.3,-4.69,48.53,-4.2" in query
    assert "out center" in query
