import json

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.coefficients import load_coefficients, load_coefficients_file
from tsdfwd_tools.common.config import ConfigError, build_n1_config
from tsdfwd_tools.common.config_fit import build_fit_config
from tsdfwd_tools.fwd.fit import fit_beta, fit_indicator, fit_k, fit_table, group_keys, seed_for


def _synthetic(beta=0.016, n_points=6, n_days=24, seed=7, noise=0.01, nonlinear=False):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_points):
        level = rng.uniform(120, 300)
        for d in range(n_days):
            month = 4 + d % 6
            day = 1 + (d * 3) % 27
            date = f"2026-{month:02d}-{day:02d}"
            t = rng.uniform(6, 29)
            val = level * np.exp(beta * (t - 20.0)) * (1 + noise * rng.standard_normal())   # ugiecie rosnie z T
            rows.append({"point_code": f"P{p}", "date": date, "t_mid_met": t, "D0": val, "D300": val * 0.7})
    return pd.DataFrame(rows)


def test_fit_recovers_known_beta():
    v = _synthetic(beta=0.016)
    keys = group_keys(v["point_code"], v["date"])
    beta, n, ok = fit_beta(v["t_mid_met"], v["D0"], keys)
    assert ok and n == len(v)
    assert beta == pytest.approx(0.016, abs=6e-4)
    k, okk = fit_k(v["t_mid_met"], v["D0"], keys)
    assert okk and k == pytest.approx(0.016, abs=1.2e-3)       # beta ~ k blisko temperatury odniesienia


def test_fit_group_effect_is_absorbed():
    v = _synthetic(beta=0.012, noise=0.0)
    keys = group_keys(v["point_code"], v["date"])
    beta, _, ok = fit_beta(v["t_mid_met"], v["D0"], keys)
    assert ok and beta == pytest.approx(0.012, abs=1e-6)


def test_fit_indicator_bootstrap_is_reproducible_and_brackets_estimate():
    v = _synthetic()
    keys = group_keys(v["point_code"], v["date"])
    day = pd.to_datetime(v["date"]).dt.strftime("%Y-%m-%d").to_numpy()
    r1 = fit_indicator(v["t_mid_met"], v["D0"], keys, day, n_boot=60, seed_tag="x:D0")
    r2 = fit_indicator(v["t_mid_met"], v["D0"], keys, day, n_boot=60, seed_tag="x:D0")
    assert r1 == r2                                            # deterministyczny seed (crc32)
    assert r1["beta_lo"] < r1["beta_pct"] < r1["beta_hi"] and r1["note"] == ""
    assert seed_for("a", "b") == seed_for("a", "b") and seed_for("a", "b") != seed_for("a", "c")


def test_fit_too_few_data():
    v = _synthetic(n_points=1, n_days=5)
    res = fit_table(v, ["D0"], "point_code", "date", "t_mid_met", n_boot=10)
    assert res.loc[0, "note"] == "za malo danych" and np.isnan(res.loc[0, "beta_pct"])


def test_fit_table_filters_range_and_requires_columns():
    v = _synthetic()
    v.loc[0, "t_mid_met"] = 3.0          # poza 5 <= T < 30
    v.loc[1, "t_mid_met"] = 30.0         # gorna granica otwarta
    res = fit_table(v, ["D0", "d300"], "point_code", "date", "t_mid_met", n_boot=10)
    assert (res["n"] == len(v) - 2).all()
    assert res.set_index("indicator").loc["d300", "beta_pct"] == pytest.approx(
        res.set_index("indicator").loc["D0", "beta_pct"], abs=1e-3)      # D300 = const * D0
    with pytest.raises(ValueError):
        fit_table(v, ["D1800"], "point_code", "date", "t_mid_met", n_boot=10)
    with pytest.raises(ValueError):
        fit_table(v, ["D0"], "brak", "date", "t_mid_met")


def test_coefficients_file_roundtrip_and_scope(tmp_path):
    rows = []
    for scope, shift in (("A", 1.0), ("B", 2.0)):
        for ind in ["D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800"]:
            rows.append({"scope": scope, "indicator": ind, "beta_pct": shift, "k_guide": shift / 100})
    p = tmp_path / "coef.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    assert load_coefficients_file(p, "B").beta("D0") == pytest.approx(0.02)
    with pytest.raises(ValueError, match="podaj coefficients_scope"):
        load_coefficients_file(p)
    with pytest.raises(ValueError, match="brak zbioru"):
        load_coefficients_file(p, "C")
    assert load_coefficients("file", "A", path=p).k("D900") == pytest.approx(0.01)
    with pytest.raises(ValueError):
        load_coefficients("file")


def test_n1_config_file_requires_path():
    with pytest.raises(ConfigError, match="coefficients_file"):
        build_n1_config({"input": {"files": ["a.xlsx"]}, "correction": {"coefficient_set": "file"}})


def test_fit_config_validation():
    with pytest.raises(ConfigError, match="visits"):
        build_fit_config({})
    with pytest.raises(ConfigError, match="t_range_c"):
        build_fit_config({"input": {"visits": "v.csv"}, "fit": {"t_range_c": [30, 5]}})
    with pytest.raises(ConfigError, match="nieznane klucze"):
        build_fit_config({"input": {"visits": "v.csv", "zly": 1}})


def test_cli_fit_then_use_coefficients_in_n1(tmp_path, drops_xlsx, stations_xlsx):
    v = _synthetic(beta=0.016, noise=0.005)
    # kolumny wskaznikow wymagane dla pelnej listy: uzywamy tylko D0 i D300 w tym tescie
    v["excl_frost"] = 0
    v["has_met"] = 1
    v.loc[0, "has_met"] = 0
    v.to_csv(tmp_path / "wizyty.csv", index=False)
    cfg = {"input": {"visits": str(tmp_path / "wizyty.csv"), "exclude_if_true": ["excl_frost"],
                     "require_true": ["has_met"]},
           "fit": {"indicators": ["D0", "D300"], "n_boot": 20},
           "output": {"dir": str(tmp_path / "fit"), "overwrite": True}}
    p = tmp_path / "fit.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert main(["fwd_fit", "--config", str(p)]) == 0
    out = pd.read_csv(tmp_path / "fit" / "wizyty_coefficients.csv")
    assert list(out["indicator"]) == ["D0", "D300"] and out["n"].iloc[0] == len(v) - 1
    meta = json.loads((tmp_path / "fit" / "wizyty_coefficients_meta.json").read_text(encoding="utf-8"))
    assert meta["input"]["n_rows"] == len(v) and meta["input"]["n_rows_after_filters"] == len(v) - 1
    assert main(["fwd_fit", "--config", str(p)]) == 0           # overwrite: true
    assert main(["fwd_fit", "--config", str(tmp_path / "brak.yaml")]) == 1
    # plik wspolczynnikow z fit (tylko D0, D300) nie ma wszystkich czujnikow -> N1 zglasza blad
    n1 = {"input": {"files": [str(drops_xlsx)], "stations_files": [str(stations_xlsx)]},
          "correction": {"variant": "B", "coefficient_set": "file",
                         "coefficients_file": str(tmp_path / "fit" / "wizyty_coefficients.csv"),
                         "coefficients_scope": "lacznie"},
          "output": {"dir": str(tmp_path / "n1"), "overwrite": True}}
    q = tmp_path / "n1.yaml"
    q.write_text(yaml.safe_dump(n1), encoding="utf-8")
    assert main(["fwd_tempcorr", "--config", str(q)]) == 1


def test_n1_with_custom_coefficient_file(tmp_path, drops_xlsx, stations_xlsx):
    rows = [{"scope": "moje", "indicator": g, "beta_pct": 2.0, "k_guide": 0.02}
            for g in ["D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800"]]
    pd.DataFrame(rows).to_csv(tmp_path / "moje.csv", index=False)
    n1 = {"input": {"files": [str(drops_xlsx)], "stations_files": [str(stations_xlsx)]},
          "correction": {"variant": "B", "coefficient_set": "file", "coefficients_file": str(tmp_path / "moje.csv")},
          "output": {"dir": str(tmp_path / "n1"), "overwrite": True}}
    q = tmp_path / "n1.yaml"
    q.write_text(yaml.safe_dump(n1), encoding="utf-8")
    assert main(["fwd_tempcorr", "--config", str(q)]) == 0
    t = pd.read_csv(tmp_path / "n1" / "Drops50_1M_1_tempcorr.csv")
    assert (t["D0_20"] / t["D0"]).iloc[0] == pytest.approx(np.exp(0.02 * 2.0), abs=1e-9)      # T=18 C
    assert t["coef_set"].iloc[0] == "file:moje"
