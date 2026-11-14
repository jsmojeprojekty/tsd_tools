"""Wspolne fixtures. Testy @reference czytaja dane poza repozytorium (tylko do odczytu) wg tests/local_paths.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

TESTS = Path(__file__).resolve().parent
DATA = TESTS / "data"


@pytest.fixture(scope="session")
def local_paths() -> dict:
    p = TESTS / "local_paths.yaml"
    if not p.is_file():
        pytest.skip("brak tests/local_paths.yaml (testy @reference pominiete)")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


@pytest.fixture(scope="session")
def sql_root(local_paths) -> Path:
    root = local_paths.get("sql_tsd_fwd_root")
    if not root or not Path(root).is_dir():
        pytest.skip("brak sciezki sql_tsd_fwd_root w tests/local_paths.yaml")
    return Path(root)


@pytest.fixture(scope="session")
def drops_xlsx() -> Path:
    return DATA / "Drops50_1M_1.xlsx"


@pytest.fixture(scope="session")
def stations_xlsx() -> Path:
    return DATA / "stations50_1M_1.xlsx"
