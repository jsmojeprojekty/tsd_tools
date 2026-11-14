"""T-N1-07: odtworzenie wspolczynnikow z e2a3_final_k_profile.csv (scope lacznie) z wizyt e2a3_visits (tylko odczyt)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main

pytestmark = pytest.mark.reference

PACKAGED = Path(__file__).resolve().parents[2] / "src" / "tsdfwd_tools" / "data" / "e2a3_final_k_profile.csv"
INDICATORS = ["D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800", "SCI300", "BDI", "BCI"]


@pytest.fixture(scope="module")
def fitted(sql_root, tmp_path_factory):
    db = sql_root / "bazy" / "baza_analizy_e2a.db"
    if not db.is_file():
        pytest.skip(f"brak {db}")
    con = sqlite3.connect("file:" + db.as_posix() + "?mode=ro", uri=True)
    try:
        visits = pd.read_sql("SELECT * FROM e2a3_visits", con)
    finally:
        con.close()
    tmp = tmp_path_factory.mktemp("fit_ref")
    visits.to_csv(tmp / "e2a3_visits.csv", index=False)
    cfg = {
        "input": {"visits": str(tmp / "e2a3_visits.csv"), "point_col": "point_code", "date_col": "date",
                  "t_col": "t_mid_met", "exclude_if_true": ["excl_frost"], "require_true": ["has_met"]},
        "fit": {"indicators": INDICATORS, "n_boot": 500, "scope_label": "lacznie"},
        "output": {"dir": str(tmp / "out"), "overwrite": True},
    }
    p = tmp / "fit.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert main(["fwd_fit", "--config", str(p)]) == 0
    got = pd.read_csv(tmp / "out" / "e2a3_visits_coefficients.csv").set_index("indicator")
    ref = pd.read_csv(PACKAGED, encoding="utf-8-sig")
    ref = ref[ref["scope"] == "lacznie"].set_index("indicator")
    return got, ref


def test_all_indicators_present_and_n(fitted):
    got, ref = fitted
    assert list(got.index) == INDICATORS
    assert (got["n"] == 414).all() and (ref.loc[INDICATORS, "n"] == 414).all()


def test_point_estimates_match_source(fitted):
    got, ref = fitted
    for ind in INDICATORS:
        assert got.loc[ind, "beta_pct"] == pytest.approx(ref.loc[ind, "beta_pct"], abs=5e-5), ind
        assert got.loc[ind, "k_guide"] == pytest.approx(ref.loc[ind, "k_guide"], abs=3e-6), ind


@pytest.mark.parametrize("ind, beta_pct, k", [
    ("D0", 1.60415, 0.0161092), ("D300", 1.21602, 0.0123428), ("D900", 0.333874, 0.00328817),
    ("SCI300", 3.24407, 0.0301423), ("BDI", 2.8704, 0.0283985), ("BCI", 1.92233, 0.0187039)])
def test_prompt_values(fitted, ind, beta_pct, k):
    got, _ = fitted
    assert got.loc[ind, "beta_pct"] == pytest.approx(beta_pct, abs=5e-5)
    assert got.loc[ind, "k_guide"] == pytest.approx(k, abs=3e-6)


def test_bootstrap_intervals_close_to_source(fitted):
    """Przedzialy percentylowe (bootstrap po dniach, 500 replik, ten sam seed crc32) — tylko przy tej samej wersji
    numpy/scipy odtwarzaja sie dokladnie; tolerancja 0,01 pp wobec roznic solvera."""
    got, ref = fitted
    for ind in INDICATORS:
        assert got.loc[ind, "beta_lo"] == pytest.approx(ref.loc[ind, "beta_lo"], abs=0.01), ind
        assert got.loc[ind, "beta_hi"] == pytest.approx(ref.loc[ind, "beta_hi"], abs=0.01), ind
    assert (got.loc["D0", "beta_lo"], got.loc["D0", "beta_hi"]) == pytest.approx((1.51323, 1.72669), abs=0.005)


def test_fitted_file_used_by_n1(fitted, tmp_path, drops_xlsx, stations_xlsx):
    got, _ = fitted
    assert got.loc["D0", "beta_pct"] > 0
    coef = tmp_path / "coef.csv"
    got.reset_index().to_csv(coef, index=False)
    n1 = {"input": {"files": [str(drops_xlsx)], "stations_files": [str(stations_xlsx)]},
          "correction": {"variant": "B", "coefficient_set": "file", "coefficients_file": str(coef)},
          "output": {"dir": str(tmp_path / "n1"), "overwrite": True}}
    q = tmp_path / "n1.yaml"
    q.write_text(yaml.safe_dump(n1), encoding="utf-8")
    assert main(["fwd_tempcorr", "--config", str(q)]) == 0
    t = pd.read_csv(tmp_path / "n1" / "Drops50_1M_1_tempcorr.csv")
    import numpy as np
    assert (t["D0_20"] / t["D0"]).iloc[0] == pytest.approx(np.exp(got.loc["D0", "beta_pct"] / 100 * 2.0), abs=1e-9)
