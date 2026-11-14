"""Estymator lambdy (Q-N4-5): sigma_TSD z par przejazdow, sigma_FWD z powtorzen stacji, lambda = sigma_FWD^2 / sigma_TSD^2."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_n4 import load_n4_config
from tsdfwd_tools.compare import lambda_est as L
from tsdfwd_tools.compare.pipeline import run_n4


def _passes(n_pass=4, km=5.0, sigma=0.3, dates=None, conc_from=None, seed=0):
    """Przejazdy po jednym korytarzu; d0 = profil * exp(blad binu 10 m ~ N(0, sigma)), 10 wierszy na bin."""
    rng = np.random.default_rng(seed)
    s = np.arange(0.0, km * 1000.0)
    base = 150.0 + 40.0 * np.sin(s / 700.0)
    rows, dts, corr = {}, {}, {}
    for k in range(n_pass):
        e = rng.normal(0, sigma, int(km * 100))
        rows[k + 1] = dict(s=s, d0=base * np.exp(e[(s // 10).astype(int)]),
                           **({"conc": (s >= conc_from).astype(float)} if conc_from else {}))
        dts[k + 1] = (dates or ["2025-07-01"] * n_pass)[k]
        corr[k + 1] = 0
    return rows, dts, corr


def test_tsd_sigma_recovers_noise_from_pairs_in_the_same_day():
    rows, dts, corr = _passes(sigma=0.3)
    r = L.tsd_repeat_sigma(L.tsd_bin_table(rows, dts, corr, L.LambdaParams()))
    # roznica dwoch bledow ma wariancje 2 sigma^2; sigma = MAD(diff)/sqrt(2)
    assert r["sigma"] == pytest.approx(0.3, rel=0.08) and r["n_pairs"] == 6 * 500


def test_tsd_pairs_respect_day_limit_and_concrete():
    rows, dts, corr = _passes(n_pass=3, dates=["2025-07-01", "2025-07-02", "2025-07-05"])
    r = L.tsd_repeat_sigma(L.tsd_bin_table(rows, dts, corr, L.LambdaParams()))
    assert r["n_pairs"] == 500                                             # tylko para z odstepem 1 dnia; 4 dni odpada
    rows, dts, corr = _passes(n_pass=2, conc_from=2500.0)
    p = L.LambdaParams()
    assert L.tsd_repeat_sigma(L.tsd_bin_table(rows, dts, corr, p), p)["n_pairs"] == 250        # beton (> 2500 m) pominiety
    p2 = L.LambdaParams(exclude_concrete=False)
    assert L.tsd_repeat_sigma(L.tsd_bin_table(rows, dts, corr, p2), p2)["n_pairs"] == 500
    few = {1: dict(s=np.array([0.0, 3.0, 6.0]), d0=np.array([100.0, 100.0, 100.0])),      # 3 punkty w binie < 5: bin niepokryty
           2: dict(s=np.array([1.0, 4.0, 7.0]), d0=np.array([120.0, 120.0, 120.0]))}
    tab = L.tsd_bin_table(few, {1: "2025-07-01", 2: "2025-07-01"}, {1: 0, 2: 0}, p)
    assert tab["n"].max() == 3 and L.tsd_repeat_sigma(tab, p)["n_pairs"] == 0


def test_tsd_time_column_overrides_date_noon():
    rows, dts, corr = _passes(n_pass=2, dates=["2025-07-01", "2025-07-03"])
    t0 = float(np.datetime64("2025-07-01T10:00:00", "s").astype("int64"))
    for pid, shift in ((1, 0.0), (2, 3600.0)):                              # dwa przejazdy w odstepie 1 h (w danych: daty 2 dni)
        rows[pid]["t"] = np.full(len(rows[pid]["s"]), t0 + shift)
    r = L.tsd_repeat_sigma(L.tsd_bin_table(rows, dts, corr, L.LambdaParams()))
    assert r["n_pairs"] == 500


def _fwd(n_sessions=4, n_win=300, sigma=0.1, seed=1, **over):
    rng = np.random.default_rng(seed)
    recs = []
    for k in range(n_sessions):
        off = rng.normal(0, 0.15)                                           # przesuniecie poziomu sesji (usuwane: mu_ij)
        for w in range(n_win):
            recs.append(dict(station=k * 10000 + w, corridor=0, s=w * 10.0 + 5.0, session=k + 1, device="8002-367",
                             date=f"2025-0{k + 1}-10", temp=15.0 + 0.1 * k, ld0=np.log(200.0) + off + rng.normal(0, sigma), conc=0))
    df = pd.DataFrame(recs)
    for c, v in over.items():
        df[c] = v
    return df


def test_fwd_sigma_within_recovers_noise_and_removes_session_offsets():
    r = L.fwd_repeat_sigma(_fwd(sigma=0.1))
    assert r["sigma_within"] == pytest.approx(0.1, rel=0.1) and r["n_session_pairs"] == 6 and r["n_pairs"] == 6 * 300
    assert r["sigma_total"] > r["sigma_within"] * 1.0                      # poziom sesji zwieksza sigma_total


def test_fwd_pair_selection_rules():
    base = L.LambdaParams()
    assert L.fwd_repeat_sigma(_fwd(date="2023-05-01"), base)["n_pairs"] == 0                       # przed 2024: pominiete
    assert L.fwd_repeat_sigma(_fwd(date="2023-05-01"), L.LambdaParams(fwd_from_date=None))["n_pairs"] > 0
    df = _fwd()
    df["temp"] = np.where(df["session"] % 2 == 0, 25.0, 15.0)                                       # |dT| >= 3 miedzy parzystymi i nieparzystymi
    assert L.fwd_repeat_sigma(df, base)["n_session_pairs"] == 2                                      # zostaja pary 1-3 i 2-4
    df = _fwd()
    df["device"] = np.where(df["session"] % 2 == 0, "8082-119", "8002-367")
    assert L.fwd_repeat_sigma(df, base)["n_session_pairs"] == 2                                      # tylko ten sam aparat
    assert L.fwd_repeat_sigma(_fwd(conc=1), base)["n_pairs"] == 0                                    # beton pominiety
    assert L.fwd_repeat_sigma(_fwd(n_sessions=1), base)["n_pairs"] == 0                              # jedna sesja: brak powtorzen
    assert np.isnan(L.fwd_repeat_sigma(_fwd(temp=np.nan), base)["sigma_within"])                     # brak temperatury


def test_lambda_end_to_end_on_synthetic_repeats():
    rows, dts, corr = _passes(sigma=0.3)
    res = L.estimate_lambda(rows, dts, corr, _fwd(sigma=0.1))
    assert res["lambda_d0"] == pytest.approx((0.1 / 0.3) ** 2, rel=0.25)
    assert res["lambda_d0"] == pytest.approx(L.lambda_from_sigmas(res["sigma_fwd"], res["sigma_tsd"]))
    assert np.isnan(L.lambda_from_sigmas(0.1, 0.0)) and np.isnan(L.lambda_from_sigmas(float("nan"), 0.3))


def test_sigma_decomp_matches_hand_computation():
    d = np.array([0.1, 0.12, 0.08, -0.2, -0.22, -0.18, 0.5])
    pair = np.array([1, 1, 1, 2, 2, 2, 3])                                 # pary z jednym oknem (3) sa pomijane w "within"
    r = L.sigma_decomp(d, pair, 3)
    res = np.array([0.0, 0.02, -0.02, 0.0, -0.02, 0.02])
    assert r["sigma_within_mad"] == pytest.approx(1.4826 * np.median(np.abs(res - np.median(res))) / np.sqrt(2))
    assert r["sigma_total_mad"] == pytest.approx(1.4826 * np.median(np.abs(d - np.median(d))) / np.sqrt(2))


# --- integracja z trybem geometry ---
def _geometry_inputs(tmp_path):
    n = 2600
    chain = np.arange(n, dtype=float)
    lat = 50.0 + chain / 111200.0
    rng = np.random.default_rng(5)
    base = 100.0 + 10.0 * np.sin(chain / 300.0)
    paths = []
    for name, f in (("T4202507200001_rows.csv", 1.0), ("T4202507210002_rows.csv", 1.1)):
        e = rng.normal(0, 0.2, n // 10 + 1)
        pd.DataFrame(dict(chainage_m=chain, lat=lat, lon=19.0, d0=f * base * np.exp(e[(chain // 10).astype(int)]), gof=0.9, t12_c=20.0,
                          speed_kmh=72.0)).to_csv(tmp_path / name, index=False)
        paths.append(tmp_path / name)
    recs, sid = [], 0
    for k in range(6):
        for i in range(10):
            pos = 300.0 + 200.0 * i                                         # te same polozenia we wszystkich sesjach
            sid += 1
            recs.append(dict(station_id=sid, session_id=k + 1, station_m=(pos - 300.0) / 1000.0, latitude=50.0 + (pos + 1.0) / 111200.0,
                             longitude=19.0, measured_at=f"2025-07-01T10:{i:02d}:00", device="8082-119", date="2025-07-01",
                             D0=2.0 * (100.0 + 10.0 * np.sin(pos / 300.0)) * np.exp(rng.normal(0, 0.05)), t_mid_c=20.0, t_surface=22.0))
    pd.DataFrame(recs).to_csv(tmp_path / "stations.csv", index=False)
    return paths, tmp_path / "stations.csv"


def _cfg(tmp_path, paths, st, **lam):
    cfg = {"tool": "tsd_fwd_compare", "mode": "geometry",
           "geometry": {"tsd_rows": [str(p) for p in paths], "fwd_stations_csv": str(st), "lambda_est": lam},
           "measures": {"n_boot": 30}, "uncertainty": {"replicates": 49}, "null_checks": {"n_boot": 30},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_geometry_mode_estimates_lambda_and_can_apply_it(tmp_path):
    paths, st = _geometry_inputs(tmp_path)
    assert main(["tsd_fwd_compare", "--config", str(_cfg(tmp_path, paths, st, enabled=True))]) == 0
    out = tmp_path / "out"
    lam = pd.read_csv(out / "lambda_estimate.csv").iloc[0]
    assert lam["n_pairs_tsd"] > 250 and lam["n_pairs_fwd"] > 100 and lam["lambda_d0"] > 0
    assert lam["sigma_tsd"] == pytest.approx(0.2, rel=0.3) and lam["sigma_fwd"] == pytest.approx(0.05, rel=0.4)
    assert bool(lam["used_in_analysis"]) is False
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["lambda_source"] == "config" and meta["geometry"]["lambda_estimate"]["lambda_d0"] == pytest.approx(lam["lambda_d0"])

    res = run_n4(load_n4_config(_cfg(tmp_path, paths, st, enabled=True, apply=True)), dry_run=True)
    assert res["meta"]["lambda_source"] == "estimate" and res["meta"]["lambda_d0_used"] == pytest.approx(lam["lambda_d0"])


def test_lambda_requires_surface_temperature_and_enabled_flag(tmp_path):
    paths, st = _geometry_inputs(tmp_path)
    df = pd.read_csv(st).drop(columns="t_surface")
    df.to_csv(st, index=False)
    with pytest.raises(ConfigError, match="temperatury powierzchni"):
        run_n4(load_n4_config(_cfg(tmp_path, paths, st, enabled=True)), dry_run=True)
    with pytest.raises(ConfigError, match="enabled"):
        load_n4_config(_cfg(tmp_path, paths, st, apply=True))
