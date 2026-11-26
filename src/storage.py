"""Atomic, UTF-8 output files; manifest is written last by the pipeline."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
import pandas as pd


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".part", dir=path.parent, delete=False) as stream:
        name = stream.name
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    try:
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", newline="", encoding="utf-8", suffix=".part", dir=path.parent, delete=False) as stream:
        name = stream.name
        frame.to_csv(stream, index=False)
    try:
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Le document {path.name} n'est pas un objet JSON")
    return payload
