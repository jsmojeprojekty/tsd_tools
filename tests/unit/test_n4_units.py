import json
import math

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_n4 import build_n4_config
from tsdfwd_tools.common.stats_basic import mad_robust_sd, nmed, seed_for
from tsdfwd_tools.compare.agreement import (bland_altman_log, bootstrap_ci, ccc_from_logs, deming, point_stats,
                                            valid_pairs, within_session_corr)
from tsdfwd_tools.compare.calibration import calibrate, errors, fit_affine, fit_multiplier
from tsdfwd_tools.compare.conditions import conditions_table, cv_by_corridor, dt_masks, r_of
from tsdfwd_tools.compare.corrections import correct_pair_values, default_beta_pct
from tsdfwd_tools.compare.nulls import align_null, paired_bootstrap_null
from tsdfwd_tools.compare.uncertainty import (cr2_interval, iso_week_of, multiplier_intervals,
                                              paired_session_bootstrap, wcr_test, wcu_dual_ci)


def _synthetic_pairs(n_sess=12, per_sess=30, a=1.6, noise=0.25, seed=3, session_sd=0.3):
    rng = np.random.default_rng(seed)
    rows = []
    pid = 0
    for s in range(1, n_sess + 1):
        offset = rng.normal(0, session_sd)
        for _ in range(per_sess):
            truth = np.exp(rng.normal(4.8, 0.5) + offset)
            tsd = truth * np.exp(rng.normal(0, noise))
            fwd = a * truth * np.exp(rng.normal(0, noise))
            rows.append({"pair_id": pid, "fwd_session_id": s, "fwd_d0": fwd, "d0_tsd": tsd,
                         "fwd_t12_cal": rng.uniform(6, 14), "tsd_t12_cal": rng.uniform(18, 29),
                         "device_group": f"g{s % 3}", "dt_days": rng.integers(-2, 60), "win5_gof05_share": rng.uniform(0, 1),
                         "corridor_id": f"c{s % 4}", "fwd_station_id": pid, "device": "D1" if s % 2 else "D2",
                         "calib_interval": "K1" if s < 7 else "K2"})
            pid += 1
    return pd.DataFrame(rows)


# --- podstawy statystyczne (T-N4-10: testy syntetyczne) ---
def test_deming_recovers_truth_with_known_lambda():
    rng = np.random.default_rng(1)
    x_true = rng.uniform(4, 6, 4000)
    sx, sy = 0.10, 0.18
    x = x_true + rng.normal(0, sx, 4000)
    y = 1.3 * x_true - 0.15 + rng.normal(0, sy, 4000)
    slope, intercept = deming(x, y, (sy / sx) ** 2)
    assert slope == pytest.approx(1.3, abs=0.05) and intercept == pytest.approx(-0.15, abs=0.25)


def test_ccc_and_bland_altman_bias():
    rng = np.random.default_rng(2)
    x = rng.normal(5, 1, 20000)
    y = x + 2.0
    assert ccc_from_logs(x, y) == pytest.approx(2 * np.var(x) / (2 * np.var(x) + 4), abs=1e-3)
    bias, lo, hi, sd = bland_altman_log(y, x)
    assert bias == pytest.approx(2.0, abs=1e-9) and sd == pytest.approx(0.0, abs=1e-9)
    assert ccc_from_logs(x[:1], y[:1]) != ccc_from_logs(x[:1], y[:1])    # NaN dla n < 2


def test_point_stats_known_ratio_and_small_n():
    tsd = np.linspace(50, 400, 200)
    stats = point_stats(1.6 * tsd, tsd, 0.12)
    assert stats["median_ratio"] == pytest.approx(1.6) and stats["sd_log_ratio"] == pytest.approx(0.0, abs=1e-12)
    assert stats["deming_loglog_slope"] == pytest.approx(1.0, abs=1e-9) and stats["pearson_r"] == pytest.approx(1.0)
    assert math.isnan(point_stats(tsd[:2], tsd[:2], 0.12)["median_ratio"])
    assert list(valid_pairs([1, -1, np.nan, 2], [1, 1, 1, 0])) == [True, False, False, False]


def test_within_session_corr_ignores_session_levels():
    rng = np.random.default_rng(4)
    rows = []
    for s in range(10):
        level = rng.normal(0, 3.0)                 # duze roznice poziomu miedzy sesjami (wspolne dla obu stron)
        for _ in range(40):
            shared = rng.normal(0, 1.0)
            rows.append((s, np.exp(level + shared + rng.normal(0, 0.3)), np.exp(level + shared + rng.normal(0, 0.3))))
    s, f, t = (np.array(c) for c in zip(*rows))
    r_ws, rho_ws, n = within_session_corr(f, t, s)
    assert n == 400 and 0.8 < r_ws < 0.99
    assert within_session_corr(f, t, np.ones(len(f)))[0] != within_session_corr(f, t, np.ones(len(f)))[0]   # 1 sesja -> NaN


def test_bootstrap_ci_reproducible_and_needs_three_sessions():
    df = _synthetic_pairs(n_sess=8)
    a = bootstrap_ci(df.fwd_d0, df.d0_tsd, df.fwd_session_id, 0.12, 80)
    b = bootstrap_ci(df.fwd_d0, df.d0_tsd, df.fwd_session_id, 0.12, 80)
    assert a == b and a["median_ratio"][0] < 1.6 < a["median_ratio"][1]
    few = df[df.fwd_session_id <= 2]
    assert math.isnan(bootstrap_ci(few.fwd_d0, few.d0_tsd, few.fwd_session_id, 0.12, 50)["median_ratio"][0])


def test_stats_basic():
    assert seed_for("a", "b") == seed_for("a", "b") != seed_for("a", "c")
    assert nmed([1, np.nan, 3]) == 2.0 and math.isnan(nmed([]))
    assert mad_robust_sd([1, 2, 3, 4, 100]) == pytest.approx(1.4826 * 1.0)


# --- niepewnosc przy malej liczbie klastrow ---
def test_cr2_and_wild_bootstrap_on_constant_model():
    df = _synthetic_pairs(n_sess=10, per_sess=25, a=1.5)
    lr = np.log(df.fwd_d0 / df.d0_tsd).to_numpy()
    cl = df.fwd_session_id.to_numpy()
    X = np.ones((len(lr), 1))
    p, lo, hi, se, dof = cr2_interval(X, lr, cl, 0, 0.05)
    assert lo < math.log(1.5) < hi and 1 < dof <= 10 + 1e-6 and p == pytest.approx(lr.mean())
    pt, lo90, hi90, lo95, hi95 = wcu_dual_ci(X, lr, cl, 0, 400, 7)
    assert lo95 < pt < hi95 and lo90 > lo95 and hi90 < hi95
    assert wcu_dual_ci(X, lr, cl, 0, 400, 7) == (pt, lo90, hi90, lo95, hi95)
    assert wcr_test(X, lr, cl, 0, 400, 8, math.log(1.5))["p_value"] > 0.05
    assert wcr_test(X, lr, cl, 0, 400, 8, math.log(3.0))["p_value"] < 0.01


def test_multiplier_intervals_rows_and_iso_week():
    df = _synthetic_pairs(n_sess=8)
    lr = np.log(df.fwd_d0 / df.d0_tsd).to_numpy()
    rows = multiplier_intervals(lr, df.fwd_session_id.to_numpy(), 200, "t", seed_for, 1.6)
    assert [r["method"] for r in rows] == ["M0_session_bootstrap", "M1_wild_cluster_webb", "M2_cr2"]
    assert all(r["lo"] < r["point"] < r["hi"] for r in rows) and "dof=" in rows[2]["note"]
    assert iso_week_of("2026-05-19") == "2026-W21"


def test_paired_session_bootstrap_identity_and_improvement():
    df = _synthetic_pairs(n_sess=12)
    f, t = df.fwd_d0.to_numpy(), df.d0_tsd.to_numpy()
    same = paired_session_bootstrap(f, t, f, t, df.device_group, df.fwd_session_id, 60)
    assert same["q1_sd_log_diff"] == pytest.approx(0.0, abs=1e-12) and same["q1_sd_log_diff_ci"] == (0.0, 0.0)
    shrunk = paired_session_bootstrap(f, t, f, f / 1.6, df.device_group, df.fwd_session_id, 60)   # po korekcie: zero rozrzutu
    assert shrunk["q1_sd_log_diff"] < 0


# --- korekta ---
def test_correct_pair_values():
    f, t = np.array([100.0]), np.array([60.0])
    fn, tn = correct_pair_values(f, t, [10.0], [30.0], "none")
    assert (fn, tn) == (f, t) or (fn[0] == 100.0 and tn[0] == 60.0)
    fm, tm = correct_pair_values(f, t, [10.0], [30.0], "main_after")
    b = default_beta_pct() / 100
    assert fm[0] == pytest.approx(100 * math.exp(b * 10)) and tm[0] == pytest.approx(60 * math.exp(-b * 10))
    fk, tk = correct_pair_values(f, t, [10.0], [30.0], "k02")
    assert fk[0] == pytest.approx(120.0) and tk[0] == pytest.approx(48.0)
    assert math.isnan(correct_pair_values(f, t, [np.nan], [30.0], "main_after")[0][0])      # brak T -> NaN
    with pytest.raises(ValueError):
        correct_pair_values(f, t, [10.0], [30.0], "guideline")
    assert default_beta_pct() == pytest.approx(1.60415, abs=1e-5)


# --- warunki ---
def test_dt_masks_keep_negative_bin_and_cover_all_integers():
    dt = np.array([-3, 0, 1, 2, 30, 31, np.nan])
    m = dt_masks(dt)
    assert m["<0"].tolist() == [True] + [False] * 6 and m["0-1"].sum() == 2 and m["2-30"].sum() == 2 and m[">30"].sum() == 1
    covered = sum(v.astype(int) for v in m.values())
    assert covered.tolist() == [1, 1, 1, 1, 1, 1, 0]           # kazda skonczona wartosc w dokladnie jednym przedziale


def test_cv_units_pairs_vs_stations_and_r_of():
    fwd = np.array([100, 100, 100, 100, 200.0, 200, 300])
    cv_p = cv_by_corridor(fwd, ["a"] * 7, None, "pairs")
    cv_s = cv_by_corridor(fwd, ["a"] * 7, [1, 1, 1, 1, 2, 2, 3], "stations")
    assert cv_p[0] != cv_s[0] and cv_s[0] == pytest.approx(np.std([100, 200, 300], ddof=1) / 200)
    with pytest.raises(ValueError):
        cv_by_corridor(fwd, ["a"] * 7, None, "stations")
    assert math.isnan(r_of(fwd, fwd, None, min_n=10)[0])


def test_conditions_table_layers_and_negative_dt():
    df = _synthetic_pairs(n_sess=12)
    f, t = correct_pair_values(df.fwd_d0, df.d0_tsd, df.fwd_t12_cal, df.tsd_t12_cal, "main_after")
    meta = df.rename(columns={"win5_gof05_share": "gof_share", "corridor_id": "corridor", "fwd_station_id": "station"})
    tab = conditions_table(f, t, df.fwd_d0, meta, ("device", "calib_interval"))
    assert set(tab["layer_group"]) >= {"dt_days", "gof_share_w5", "cv_d0_corridor_tercile", "devicexcalib_interval"}
    dt_rows = tab[tab.layer_group == "dt_days"].set_index("layer_value")
    assert "<0" in dt_rows.index and dt_rows["n_candidates"].sum() == len(df)       # nic nie wypada z tabeli
    assert tab[tab.layer_group == "devicexcalib_interval"]["n_candidates"].sum() == len(df)
    no_meta = conditions_table(f, t, df.fwd_d0, df[["pair_id"]])
    assert no_meta.empty


# --- kalibracja ---
def test_calibration_multiplier_and_affine():
    rng = np.random.default_rng(5)
    tsd = rng.uniform(50, 300, 600)
    fwd = 1.5 * tsd * np.exp(rng.normal(0, 0.05, 600))
    groups = np.repeat(np.arange(12), 50)
    assert fit_multiplier(tsd, fwd) == pytest.approx(1.5, abs=0.02)
    a, b = fit_affine(tsd, 2.0 * tsd + 10)
    assert a == pytest.approx(2.0) and b == pytest.approx(10.0)
    rows = calibrate(tsd, fwd, groups, "multiplier", "x")
    assert rows[0]["scope"] == "in_sample" and rows[1]["scope"] == "leave_one_group_out"
    assert rows[1]["mae"] >= rows[0]["mae"] - 1e-9 and rows[1]["n"] == 600
    assert calibrate(tsd, fwd, groups, "affine")[0]["b"] == pytest.approx(0, abs=15)
    with pytest.raises(ValueError):
        calibrate(tsd, fwd, groups, "kwadratowy")
    assert errors([np.nan], [1.0]) == (float("nan"), float("nan"), 0) or errors([np.nan], [1.0])[2] == 0


# --- pary zerowe ---
def test_align_null_and_paired_bootstrap():
    df = _synthetic_pairs(n_sess=10)
    rng = np.random.default_rng(6)
    nd = pd.DataFrame({"pair_id": df.pair_id, "null_type": "shift_plus200",
                       "d0_w5": rng.permutation(df.d0_tsd.to_numpy()), "d0_valid_w5": 1})
    nd.loc[0, "d0_valid_w5"] = 0
    aligned = align_null(df, nd, "shift_plus200")
    assert math.isnan(aligned.iloc[0]) and aligned.iloc[1] == nd.d0_w5.iloc[1]
    assert align_null(df, nd, "permutation").isna().all()
    res = paired_bootstrap_null(df.fwd_d0, df.d0_tsd, aligned, df.fwd_session_id, 80, 11)
    assert res["delta_r"] > 0.3 and res["delta_r_lo"] > 0 and res["r_null"] < res["r_true"]


# --- konfiguracja i potok ---
def test_n4_config_validation():
    with pytest.raises(ConfigError, match="pairs_csv"):
        build_n4_config({})
    with pytest.raises(ConfigError, match="geometry"):
        build_n4_config({"mode": "geometry", "input": {"pairs_csv": "x.csv"}})
    with pytest.raises(ConfigError):
        build_n4_config({"input": {"pairs_csv": "x.csv"}, "correction": {"treatments": ["guideline"]}})
    with pytest.raises(ConfigError, match="nieznane klucze"):
        build_n4_config({"input": {"pairs_csv": "x.csv", "columns": {"zly": "a"}}})
    cfg = build_n4_config({"input": {"pairs_csv": "x.csv"}, "correction": {"treatments": ["none"],
                                                                         "main_treatment": "main_after"}})
    assert "main_after" in cfg.correction.treatments


def _write_cfg(tmp_path, pairs_csv, **over):
    cfg = {"tool": "tsd_fwd_compare", "mode": "pairs", "input": {"pairs_csv": str(pairs_csv)},
           "measures": {"n_boot": 60}, "uncertainty": {"replicates": 200},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    for k, v in over.items():
        cfg[k] = {**cfg.get(k, {}), **v}
    p = tmp_path / "n4.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_cli_n4_end_to_end_synthetic(tmp_path):
    df = _synthetic_pairs(n_sess=12)
    df.loc[3, "fwd_t12_cal"] = 2.0                                  # T12 poza zakresem: flaga, nie usuniecie
    df.loc[4, "tsd_t12_cal"] = np.nan                               # brak T12
    df.to_csv(tmp_path / "pairs.csv", index=False)
    nulls = pd.DataFrame({"pair_id": df.pair_id, "null_type": "shift_plus200",
                          "d0_w5": np.random.default_rng(1).permutation(df.d0_tsd.to_numpy()), "d0_valid_w5": 1})
    nulls.to_csv(tmp_path / "nulls.csv", index=False)
    cfg = _write_cfg(tmp_path, tmp_path / "pairs.csv", input={"null_pairs_csv": str(tmp_path / "nulls.csv")})
    assert main(["tsd_fwd_compare", "--config", str(cfg)]) == 0
    out = tmp_path / "out"
    for name in ("agreement.csv", "agreement_groups.csv", "agreement_ci.csv", "conditions.csv", "calibration.csv",
                 "null_checks.csv", "null_delta.csv", "conversion.csv", "pairs_corrected.csv", "meta.json", "report.html"):
        assert (out / name).is_file(), name
    ag = pd.read_csv(out / "agreement.csv").set_index("variant")
    assert ag.loc["none", "n_pairs"] == len(df) and ag.loc["main_after", "n_pairs"] == len(df) - 1    # tylko para bez T12 wypada; T12 < 5 C flagowane
    assert 1.2 < ag.loc["none", "median_ratio"] < 2.2
    pc = pd.read_csv(out / "pairs_corrected.csv")
    assert pc.loc[3, "t12_outside_or_missing"] and pc.loc[4, "t12_outside_or_missing"] and pc["valid_pair"].all()
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["n_t12_outside_or_missing"] >= 2 and "geometryczne" in meta["note"]
    assert main(["tsd_fwd_compare", "--config", str(cfg), "--strict"]) == 2
    assert main(["n4", "--config", str(cfg), "--dry-run", "--out-dir", str(tmp_path / "x")]) == 0
    assert not (tmp_path / "x").exists()


def test_cli_n4_errors(tmp_path):
    df = _synthetic_pairs(n_sess=6)
    df.drop(columns=["fwd_t12_cal"]).to_csv(tmp_path / "pairs.csv", index=False)
    cfg = _write_cfg(tmp_path, tmp_path / "pairs.csv")
    assert main(["tsd_fwd_compare", "--config", str(cfg)]) == 1                      # brak wymaganej kolumny
    assert main(["tsd_fwd_compare", "--config", str(_write_cfg(tmp_path, tmp_path / "brak.csv"))]) == 1
    assert main(["tsd_fwd_compare", "--config", str(tmp_path / "brak.yaml")]) == 1


def test_t12_csv_join_and_column_mapping(tmp_path):
    df = _synthetic_pairs(n_sess=6)
    df[["pair_id", "fwd_t12_cal", "tsd_t12_cal"]].rename(columns={"fwd_t12_cal": "tf", "tsd_t12_cal": "tt"}).to_csv(
        tmp_path / "t12.csv", index=False)
    df.drop(columns=["fwd_t12_cal", "tsd_t12_cal"]).to_csv(tmp_path / "pairs.csv", index=False)
    cfg = _write_cfg(tmp_path, tmp_path / "pairs.csv", input={"t12_csv": str(tmp_path / "t12.csv"),
                                                              "columns": {"fwd_t12": "tf", "tsd_t12": "tt"}})
    assert main(["tsd_fwd_compare", "--config", str(cfg)]) == 0
