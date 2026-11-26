from __future__ import annotations

import json
import pandas as pd
import pytest

from src.http_client import DataSourceError, get_json, overpass_json
from src.storage import write_csv, write_json, read_json


class Response:
    def __init__(self, obj=None, error=None):
        self.obj = obj
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.obj


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)

    def get(self, *_args, **_kwargs):
        return next(self.responses)

    def post(self, *_args, **_kwargs):
        return next(self.responses)


def test_get_json_success():
    assert get_json("https://example.org", params={}, session=Session([Response({"daily": {}})])) == {"daily": {}}


def test_get_json_error_body():
    with pytest.raises(DataSourceError):
        get_json("https://example.org", params={}, session=Session([Response([1, 2, 3])]))


def test_overpass_fallback_between_endpoints():
    assert overpass_json("test", session=Session([Response([]), Response({"elements": []})]),
                         endpoints=("https://a", "https://b"))[1] == "https://b"


def test_atomic_file_writers(tmp_path):
    write_json(tmp_path / "test.json", {"example": 1})
    assert read_json(tmp_path / "test.json") == {"example": 1}
    table = pd.DataFrame({"test": [1, 2]})
    write_csv(tmp_path / "test.csv", table)
    assert pd.read_csv(tmp_path / "test.csv").test.tolist() == [1, 2]
    assert not list(tmp_path.glob("*.part"))
