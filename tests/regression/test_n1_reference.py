"""Testy regresji N1 wzgledem zrodla (dane poza repozytorium, tylko odczyt; sciezki w tests/local_paths.yaml)."""

from __future__ import annotations

import hashlib
import math
import sqlite3
from pathlib import Path

import numpy as np
import pytest

from tsdfwd_tools.common.coefficients import load_coefficients
from tsdfwd_tools.common.constants import GEOPHONES
from tsdfwd_tools.common.rules import CorrectionForm, apply_correction
from tsdfwd_tools.fwd.diagnostics import band_mean, l20_error

pytestmark = pytest.mark.reference

# stale k regul R4 wpisane w zrodle (e2aR2_rules_R4.py: K_R4, zaokraglone z e2a3_final_k_profile.csv)
K_R4 = {"D0": 0.01611, "D300": 0.01234, "D600": 0.00703, "D900": 0.00329}
THAW_MONTHS = ("02", "03")
BANDS = {"15_20": (15.0, 20.0), "20_25": (20.0, 25.0), "25_30": (25.0, 30.0), "30_35": (30.0, 35.0)}


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_packaged_coefficients_identical_to_source(sql_root):
    src = sql_root / "tabele" / "e2a3_final_k_profile.csv"
    pkg = Path(__file__).resolve().parents[2] / "src" / "tsdfwd_tools" / "data" / "e2a3_final_k_profile.csv"
    assert _md5(src) == _md5(pkg)


def test_prompt_reference_coefficients():
    t = load_coefficients("e2a3_full")
    assert t.k("D0") == pytest.approx(0.0161092, abs=1e-7) and t.beta("D0") * 100 == pytest.approx(1.60415, abs=1e-5)
    assert t.k("D300") == pytest.approx(0.0123428, abs=1e-7) and t.beta("D300") * 100 == pytest.approx(1.21602, abs=1e-5)
    assert t.k("D900") == pytest.approx(0.00328817, abs=1e-8) and t.beta("D900") * 100 == pytest.approx(0.333874, abs=1e-6)


def _visits(sql_root):
    db = sql_root / "bazy" / "baza_analizy_e2a.db"
    if not db.is_file():
        pytest.skip(f"brak {db}")
    uri = "file:" + db.as_posix() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        cols = [c[1] for c in con.execute("PRAGMA table_info(e2a3_visits)")]
        return [dict(zip(cols, r)) for r in con.execute("SELECT * FROM e2a3_visits")]
    finally:
        con.close()


def _finite(x):
    return x is not None and math.isfinite(x)


def _band_rows(T, y, key, param):
    e, keep = l20_error(T, y, key, param, "linear")
    return {b: band_mean(T, e, keep, lo, hi, min_n=20) for b, (lo, hi) in BANDS.items()}


# T-N1-08: test pasm R4 (zbior `lacznie`, no_thaw): wlasny wskaznik D0, D300, D900 z k z tabeli (postac liniowa)
@pytest.mark.parametrize("ind, expected", [
    ("D0", {"15_20": (-0.224, 108), "20_25": (0.220, 110), "25_30": (-1.064, 49), "30_35": (-3.762, 25)}),
    ("D300", {"15_20": (-0.089, 108), "20_25": (0.087, 110), "25_30": (-0.231, 49), "30_35": (-1.358, 25)}),
    ("D900", {"15_20": (0.131, 108), "20_25": (-0.129, 110), "25_30": (0.563, 49), "30_35": (0.368, 25)}),
])
def test_r4_bands_own_indicator(sql_root, ind, expected):
    rows = [v for v in _visits(sql_root)
            if not v["excl_frost"] and v["has_met"] and _finite(v["t_mid_met"]) and _finite(v[ind])
            and v["month"] not in THAW_MONTHS]
    T = np.array([v["t_mid_met"] for v in rows])
    y = np.array([v[ind] for v in rows])
    key = np.array([f"{v['station_code']}|{v['point_code']}|{v['month']}" for v in rows])
    got = _band_rows(T, y, key, K_R4[ind])
    for band, (est, n) in expected.items():
        assert got[band][1] == n, f"{ind} {band}: n"
        assert got[band][0] == pytest.approx(est, abs=0.01), f"{ind} {band}"


# SCI300 z ugiec SKORYGOWANYCH (D0_20 - D300_20; populacja: D0, D300, D600, D900 wszystkie > 0)
def test_r4_bands_sci300_from_corrected_deflections(sql_root):
    rows = [v for v in _visits(sql_root)
            if not v["excl_frost"] and v["has_met"] and _finite(v["t_mid_met"])
            and all(_finite(v[d]) and v[d] > 0 for d in ("D0", "D300", "D600", "D900"))
            and v["month"] not in THAW_MONTHS]
    T = np.array([v["t_mid_met"] for v in rows])
    d0_20 = apply_correction([v["D0"] for v in rows], T, CorrectionForm.LINEAR, K_R4["D0"])
    d300_20 = apply_correction([v["D300"] for v in rows], T, CorrectionForm.LINEAR, K_R4["D300"])
    key = np.array([f"{v['station_code']}|{v['point_code']}|{v['month']}" for v in rows])
    got = _band_rows(T, d0_20 - d300_20, key, 0.0)     # korekta juz wbudowana w roznice (param = 0)
    expected = {"15_20": (-0.683, 108), "20_25": (0.671, 110), "25_30": (-6.021, 49), "30_35": (-18.525, 24)}
    for band, (est, n) in expected.items():
        assert got[band][1] == n, band
        assert got[band][0] == pytest.approx(est, abs=0.01), band


def test_no_references_below_10c(sql_root):
    """Stacje nie pozwalaja zweryfikowac korekty ponizej 10-15 C: pasma bez referencji 15-25 C w grupie."""
    rows = [v for v in _visits(sql_root)
            if not v["excl_frost"] and v["has_met"] and _finite(v["t_mid_met"]) and _finite(v["D0"])
            and v["month"] not in THAW_MONTHS]
    T = np.array([v["t_mid_met"] for v in rows])
    y = np.array([v["D0"] for v in rows])
    key = np.array([f"{v['station_code']}|{v['point_code']}|{v['month']}" for v in rows])
    e, keep = l20_error(T, y, key, K_R4["D0"], "linear")
    assert not keep[(T < 10.0)].any()


# MDB (Dynatest): odczyt tylko do odczytu przez ODBC; test pomijany bez sterownika
def test_mdb_end_to_end(sql_root, tmp_path):
    pyodbc = pytest.importorskip("pyodbc")
    if "Microsoft Access Driver (*.mdb, *.accdb)" not in pyodbc.drivers():
        pytest.skip("brak sterownika ODBC Access")
    mdb = sql_root / "baza_TSD_FWD_odcinki" / "FWD" / "2020-Pomiary" / "A-4_Stalexport_Węzły" / "MOP" / "MOP_Kepinica.mdb"
    if not mdb.is_file():
        pytest.skip(f"brak {mdb}")
    from tsdfwd_tools.cli.main import main
    import pandas as pd
    import yaml

    cfg = {"input": {"files": [str(mdb)], "format": "mdb"},
           "temperature": {"source": "constant", "constant_c": 22.0},
           "correction": {"variant": "B"},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    p = tmp_path / "mdb.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert main(["fwd_tempcorr", "--config", str(p)]) == 0
    t = pd.read_csv(tmp_path / "out" / "MOP_Kepinica_tempcorr.csv")
    assert len(t) == 10                      # 10 stacji w sesji
    first = t.iloc[0]
    # zrzut 1 i 2 w pliku: D1 = 404,8 / 398,7 kN 57,54 / 57,38 (normalizacja 50 kN)
    expected_d0 = np.mean([404.79998779296875 * 50 / 57.540000915527344, 398.70001220703125 * 50 / 57.38000106811523])
    assert first["D0"] == pytest.approx(expected_d0, abs=1e-3)
    assert first["D0_20"] == pytest.approx(first["D0"] * math.exp(0.0160415 * (20.0 - 22.0)), abs=1e-3)
    assert not (t[list(GEOPHONES)].isna().any().any())     # uklad geofonow 0..1800 dopasowany po x1..x9
