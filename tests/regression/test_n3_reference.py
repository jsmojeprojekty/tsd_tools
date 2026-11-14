"""Testy regresji N3 wzgledem danych referencyjnych projektu bazy (tylko odczyt)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.tsd.constants import CHANNELS_9
from tsdfwd_tools.tsd.flags import TsdFlag
from tsdfwd_tools.tsd.integrals import p0_integrals, trapezoid_integrals
from tsdfwd_tools.tsd.io import read_b1510off
from tsdfwd_tools.tsd.uc_export import validate_uc_structure
from tsdfwd_tools.tsd.window import window_medians

pytestmark = pytest.mark.reference

B1510 = Path("baza_TSD_FWD_odcinki") / "TSD" / "B_1510off"


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _ro(db: Path) -> sqlite3.Connection:
    if not db.is_file():
        pytest.skip(f"brak {db}")
    return sqlite3.connect("file:" + db.as_posix() + "?mode=ro", uri=True)


# T-N3-01: calki P0 i T z 9 nachylen (mikroodcinki; e2a2_slopes.csv -> e2a2_autc_var.csv)
def test_integrals_match_e2a2_autc_var(sql_root):
    sl = _csv(sql_root / "tabele" / "e2a2_slopes.csv")
    au = _csv(sql_root / "tabele" / "e2a2_autc_var.csv")
    assert (sl["section_code"] == au["section_code"]).all() and (sl["point_k"] == au["point_k"]).all()
    s = sl[[f"slope_{c}" for c in CHANNELS_9]].to_numpy(float)
    p, t = p0_integrals(s), trapezoid_integrals(s)
    for ours, ref in (("a031", "p0_a031"), ("a061", "p0_a061"), ("a091", "p0_a091"), ("a0361", "p0_a0361"), ("a6191", "p0_a6191")):
        m = np.isfinite(p[ours]) & np.isfinite(au[ref])
        assert m.sum() > 1200
        assert np.abs(p[ours][m] - au[ref][m]).max() < 2e-3, ours            # roznica = zaokraglenie nachylen w CSV (6 cyfr)
    for ours, ref in (("t_a031", "t_a031"), ("t_a061", "t_a061"), ("t_a091", "t_a091"), ("t_a0361", "t_a0361"), ("t_a6191", "t_a6191")):
        m = np.isfinite(t[ours]) & np.isfinite(au[ref])
        assert np.abs(t[ours][m] - au[ref][m]).max() < 2e-3, ours
    # wiersz kontrolny: 1a, 2025-09-04, punkt 0
    k = int(np.where((sl.section_code == "1a") & (sl.series_date == "2025-09-04") & (sl.point_k == 0))[0][0])
    assert p["a031"][k] == pytest.approx(21.6023, abs=1e-3) and p["a061"][k] == pytest.approx(39.0758, abs=1e-3)
    assert p["a091"][k] == pytest.approx(41.5524, abs=1e-3) and p["a0361"][k] == pytest.approx(17.4735, abs=1e-3)
    assert p["a6191"][k] == pytest.approx(2.47669, abs=1e-3) and t["t_a031"][k] == pytest.approx(22.6437, abs=1e-3)
    assert t["t_a061"][k] == pytest.approx(39.7148, abs=1e-3)
    # mediany z promptu/raportu (wartosci kontrolne)
    assert np.nanmedian(p["a031"]) == pytest.approx(39.51, abs=0.01) and np.nanmedian(t["t_a031"]) == pytest.approx(35.69, abs=0.01)


# T-N3-07: parser pliku B_1510off 2020 (kontrola formatu: 86 kolumn, znak D, GPS)
def test_parser_reference_file_2020(sql_root):
    path = sql_root / B1510 / "T4202008060001.raw.sup.txt"
    if not path.is_file():
        pytest.skip(f"brak {path}")
    run = read_b1510off(path)
    d = run.data
    assert len(d) == 6103 and run.n_bad_rows == 0
    first = d.iloc[0]
    assert first["chainage_m"] == 0.0 and first["d0"] == pytest.approx(8342.0) and first["gof"] == pytest.approx(0.23790418)
    assert first["slope_0110"] == pytest.approx(1453.5559) and first["lat"] == pytest.approx(50.091676027) and first["lon"] == pytest.approx(19.813605221)
    assert run.date.isoformat() == "2020-08-06" and run.meta["GoodNess limit"] == "0.1500" and run.meta["Model type"] == "Asymmetrical model"
    assert run.file_flags & TsdFlag.FILE_YEAR_OUT_OF_RANGE and not run.file_flags & TsdFlag.FILE_NOT_RECALIBRATED


FILE_2025 = "T4202504230012.raw.sup.txt"


def test_parser_matches_database_rows(sql_root):
    path = sql_root / B1510 / FILE_2025
    if not path.is_file():
        pytest.skip(f"brak {path}")
    con = _ro(sql_root / "bazy" / "baza_odcinki_b1510off_v2.db")
    try:
        files = pd.read_sql("select file_id, filename, n_rows, n_bad_rows from b1510off_files", con)
        hit = files[files["filename"] == "T4202504230012"]
        assert len(hit) == 1
        fid = int(hit["file_id"].iloc[0])
        db = pd.read_sql(f"select * from b1510off_measurements where file_id = {fid} order by tsd_id", con)
    finally:
        con.close()
    run = read_b1510off(path)
    d = run.data
    assert len(d) == len(db) == int(hit["n_rows"].iloc[0]) and run.n_bad_rows == int(hit["n_bad_rows"].iloc[0])
    for ours, theirs in (("chainage_m", "chainage_b"), ("d0", "d_d0"), ("gof", "goodness_of_fit"), ("speed_ms", "speed_ms"),
                         ("temp_road", "temp_road"), ("temp_air", "temp_air")):
        assert np.allclose(d[ours].to_numpy(float), db[theirs].to_numpy(float), atol=1e-9, equal_nan=True), ours
    for c in CHANNELS_9:
        assert np.allclose(d[f"slope_{c}"].to_numpy(float), db[f"slope_{c}"].to_numpy(float), atol=1e-9, equal_nan=True), c


# T-N3-04 (czesc d0): okno W5 pary 5288 (10 wierszy B_1510off, 8 z waznym d0): mediana d0 = 153 (e2b2_tsd_values)
def test_window_d0_pair_5288(sql_root):
    con = _ro(sql_root / "bazy" / "baza_odcinki_b1510off_v2.db")
    try:
        db = pd.read_sql("select * from b1510off_measurements where tsd_id between 6867094 and 6867103 order by tsd_id", con)
    finally:
        con.close()
    ref = _csv(sql_root / "tabele" / "e2b2_tsd_values.csv").set_index("pair_id").loc[5288]
    d = pd.DataFrame({"chainage_m": db["chainage_b"].to_numpy(float), "d0_20": db["d_d0"].to_numpy(float),
                      "gof": db["goodness_of_fit"].to_numpy(float)})
    w = window_medians(d, [5.5], 4.5, ["d0_20"], min_rows=3)
    assert w.loc[0, "n_valid_d0"] == int(ref["n_d0_w5"]) == 8 and w.loc[0, "d0_20"] == pytest.approx(float(ref["d0_w5"]), abs=1e-6)
    assert w.loc[0, "gof_median"] == pytest.approx(float(ref["gof_w5"]), abs=1e-5)


# przebieg na prawdziwym pliku 2025: potok, kontrola jakosci, XML DSN
def test_real_file_pipeline_and_xml(sql_root, tmp_path):
    path = sql_root / B1510 / FILE_2025
    if not path.is_file():
        pytest.skip(f"brak {path}")
    cfg = {"input": {"tsd_files": [str(path)]}, "layer_temp": {"source": "constant", "constant_c": 15.0},
           "xml_uc": {"enabled": True, "kod_oddz": "WA", "rok": 2025, "droga": "50", "jezdnia": 1, "pas": 1, "km_start": 40.0},
           "output": {"dir": str(tmp_path / "out"), "rows_csv": True, "overwrite": True}}
    p = tmp_path / "n3.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert main(["tsd_network", "--config", str(p)]) == 0
    out = tmp_path / "out"
    uc = out / f"UC_{path.name.split('.')[0]}.xml"
    assert validate_uc_structure(uc) == []
    s = pd.read_csv(out / "summary.csv").iloc[0]
    assert s["n_rows"] == 1698 and s["gyro_gps_verdict"] == "OK" and s["date"] == "2025-04-23"
    assert 0.3 < s["n_valid_d0"] / s["n_rows"] < 0.7                               # wypelnienie d0 B_1510off 44-61 % (GoodNess limit 0,15)
    assert s["n_hampel_rejected"] / s["n_valid_d0"] < 0.2
    rows = pd.read_csv(out / f"{path.name.split('.')[0]}_rows.csv")
    ok = rows["a031"].notna()
    assert ok.mean() > 0.9 and (rows.loc[ok, "a0361"] - (rows.loc[ok, "a061"] - rows.loc[ok, "a031"])).abs().max() < 1e-9
    assert (rows["d0_20"].dropna() > 0).all()
