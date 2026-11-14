"""Testy regresji N4 (tryb pairs) wzgledem wynikow referencyjnych projektu bazy i DOKTORAT (tylko odczyt)."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.common.config_n4 import build_n4_config
from tsdfwd_tools.compare.agreement import within_session_corr
from tsdfwd_tools.compare.calibration import calibration_table
from tsdfwd_tools.compare.corrections import correct_pair_values
from tsdfwd_tools.compare.pipeline import run_n4

pytestmark = pytest.mark.reference

Z15_REL = Path("wymiana") / "wyniki" / "z15" / "Z15_temperatury_par.csv"
BETA_D0_PCT = 1.6041459432458258        # wartosc uzyta w zrodle (z bazy); pakiet: 1,60415 z CSV (roznica < 1e-5)


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def paths(local_paths, sql_root):
    z15 = Path(local_paths.get("doktorat_root", "")) / Z15_REL
    if not z15.is_file():
        pytest.skip(f"brak {z15}")
    tab = sql_root / "tabele"
    for name in ("e2b2_pairs.csv", "e2b2_null_values.csv", "z15_korekta_TSD_FWD_main.csv"):
        if not (tab / name).is_file():
            pytest.skip(f"brak {tab / name}")
    return {"z15": z15, "tab": tab}


@pytest.fixture(scope="module")
def result(paths, tmp_path_factory):
    out = tmp_path_factory.mktemp("n4_ref")
    cfg = build_n4_config({
        "input": {"pairs_csv": str(paths["z15"]), "meta_csv": str(paths["tab"] / "e2b2_pairs.csv"),
                  "null_pairs_csv": str(paths["tab"] / "e2b2_null_values.csv")},
        "correction": {"treatments": ["none", "main_after", "k02"], "main_treatment": "main_after"},
        "measures": {"n_boot": 1000},
        "uncertainty": {"replicates": 9999},
        "output": {"dir": str(out / "wyniki"), "overwrite": True},
    }, base_dir=out)
    return run_n4(cfg)


def _row(df, **kw):
    sel = df
    for k, v in kw.items():
        sel = sel[sel[k] == v]
    assert len(sel) == 1, kw
    return sel.iloc[0]


# T-N4-01 / T-N4-02: wiersze main_after / main_before z z15_korekta_TSD_FWD_main.csv
@pytest.mark.parametrize("variant, ours", [("main_after", "main_after"), ("main_before", "none")])
def test_main_rows_match_source(paths, result, variant, ours):
    ref = _row(_csv(paths["tab"] / "z15_korekta_TSD_FWD_main.csv"), variant=variant)
    got = _row(result["agreement"], variant=ours)
    assert got["n_pairs"] == 5511 and got["n_sessions"] == 36
    for k in ("median_ratio", "sd_log_ratio", "pearson_r", "spearman_rho", "ccc", "ba_bias_ratio", "deming_loglog_slope",
              "deming_loglog_intercept", "deming_linear_a", "deming_linear_b", "mad_log_ratio", "p90_abs_log_ratio"):
        assert got[k] == pytest.approx(float(ref[k]), abs=1e-4, rel=1e-5), k
    for k in ("median_ratio_lo", "median_ratio_hi", "deming_loglog_slope_lo", "deming_loglog_slope_hi"):
        assert got[k] == pytest.approx(float(ref[k]), abs=2e-4), k


def test_prompt_reference_values(result):
    got = _row(result["agreement"], variant="main_after")
    assert got["median_ratio"] == pytest.approx(1.6158, abs=0.01) and got["n_pairs"] == 5511 and got["n_sessions"] == 36
    before = _row(result["agreement"], variant="none")
    assert before["median_ratio"] == pytest.approx(1.40644, abs=1e-5) and before["lo" if False else "pearson_r"] == pytest.approx(0.611999, abs=1e-5)
    assert before["ccc"] == pytest.approx(0.424149, abs=1e-5) and got["ccc"] == pytest.approx(0.346871, abs=1e-5)


def test_pairs_have_flagged_t12(result):
    # korekta T12 poza 5-30 C jest flagowana (mnoznik policzony takze dla tych par — zastrzezenie raportu 7.3)
    pairs = result["pairs"]
    assert pairs["valid_pair"].all() and pairs["t12_outside_or_missing"].sum() > 0
    assert result["meta"]["n_t12_outside_or_missing"] == int(pairs["t12_outside_or_missing"].sum())
    assert "caveat" in result["conversion"].columns and result["conversion"]["caveat"].iloc[0]


# T-N4-03: r i rho w obrebie sesji (lustro P071)
def test_within_session_r_matches_lustro(paths, result):
    lustro = _csv(paths["tab"] / "e2bR9_lustro_warianty.csv")
    for tr, name in (("none", "none"), ("main_after", "main_after"), ("k02", "k02")):
        ref = _row(lustro, pairtype="real", variant="W5", treatment=name)
        got = _row(result["agreement"], variant=tr)
        assert got["r_within_session"] == pytest.approx(float(ref["r_within_session"]), abs=5e-4), tr
        assert got["rho_within_session"] == pytest.approx(float(ref["rho_within_session"]), abs=5e-3), tr
    assert _row(result["agreement"], variant="main_after")["r_within_session"] == pytest.approx(0.403, abs=2e-3)


# T-N4-04: pary zerowe (e2b2_null_values + Z15)
@pytest.mark.parametrize("null_type, lustro_type", [("shift_minus200", "null_shift_minus200"),
                                                    ("shift_plus200", "null_shift_plus200"),
                                                    ("permutation", "null_permutation")])
def test_null_pairs_global_measures(paths, result, null_type, lustro_type):
    ref = _row(_csv(paths["tab"] / "e2bR9_lustro_warianty.csv"), pairtype=lustro_type, variant="W5", treatment="main_after")
    got = _row(result["nulls"], pair_kind=null_type)
    assert got["n_pairs"] == int(ref["n"])
    assert got["median_ratio"] == pytest.approx(float(ref["median_ratio"]), abs=2e-3)
    assert got["pearson_r"] == pytest.approx(float(ref["pearson_r"]), abs=2e-3)


# T-N4-05: r w obrebie sesji dla par zerowych — wartosci raportu (lustro) odtwarzaja sie z e2b2_null_values + Z15
@pytest.mark.parametrize("null_type, expected", [("shift_minus200", 0.155242), ("shift_plus200", 0.13524),
                                                 ("permutation", 0.0962062)])
def test_null_pairs_within_session_r_report_values(result, null_type, expected):
    got = _row(result["nulls"], pair_kind=null_type)
    assert got["r_within_session"] == pytest.approx(expected, abs=2e-3)
    assert _row(result["agreement"], variant="main_after")["r_within_session"] - got["r_within_session"] > 0.24 - 0.2


@pytest.mark.parametrize("null_type, e2b2b_value", [
    pytest.param("shift_plus200", 0.141119, id="plus200"),
    pytest.param("shift_minus200", 0.118223, id="minus200",
                 marks=pytest.mark.xfail(reason="e2b2b_null_test_paired: inna definicja r w obrebie sesji — nieodtwarzalna", strict=False)),
    pytest.param("permutation", 0.0233381, id="permutation",
                 marks=pytest.mark.xfail(reason="e2b2b_null_test_paired: inna definicja r w obrebie sesji — nieodtwarzalna", strict=False)),
])
def test_null_pairs_within_session_r_uncorrected_e2b2b(paths, null_type, e2b2b_value):
    """Wartosci e2b2b dotycza par BEZ korekty temperaturowej; N4 odtwarza tylko przypadek +200 m."""
    z = _csv(paths["z15"])
    nd = _csv(paths["tab"] / "e2b2_null_values.csv")
    from tsdfwd_tools.compare.nulls import align_null
    tn = align_null(z, nd, null_type).to_numpy(float)
    r, _, _ = within_session_corr(z["fwd_d0"].to_numpy(float), tn, z["fwd_session_id"].to_numpy())
    assert r == pytest.approx(e2b2b_value, abs=2e-3)


def test_paired_bootstrap_null_deltas(result):
    d = result["null_delta"].set_index("null_type")
    assert (d["delta_r_lo"] > 0).all() and (d["delta_ccc_lo"] > 0).all()
    assert d.loc["permutation", "delta_r"] > d.loc["shift_plus200", "delta_r"]
    assert d.loc["shift_plus200", "within_session_r_true"] > d.loc["shift_plus200", "within_session_r_null"]


# T-N4-06: niepewnosc (W3: M0, WCU, CR2)
def test_multiplier_intervals_match_source(result):
    m = result["multiplier"].set_index("method")
    assert m.loc["M0_session_bootstrap", "point"] == pytest.approx(1.59782, abs=1e-4)
    assert (m.loc["M0_session_bootstrap", "lo"], m.loc["M0_session_bootstrap", "hi"]) == pytest.approx((1.53804, 1.65362), abs=0.01)
    assert (m.loc["M1_wild_cluster_webb", "lo"], m.loc["M1_wild_cluster_webb", "hi"]) == pytest.approx((1.53793, 1.6602), abs=0.01)
    assert (m.loc["M2_cr2", "lo"], m.loc["M2_cr2", "hi"]) == pytest.approx((1.53689, 1.66116), abs=0.01)
    p = float(re.search(r"WCR p=([0-9.]+)", m.loc["M1_wild_cluster_webb", "note"]).group(1))
    assert p == pytest.approx(0.9393, abs=0.01)
    assert float(re.search(r"dof=([0-9.]+)", m.loc["M2_cr2", "note"]).group(1)) == pytest.approx(20.5, abs=0.1)


# funkcja przeliczajaca, grupy aparat x rok (Tab. 6.4), pytania Q1-Q3
def test_conversion_groups_and_questions(paths, result):
    conv = result["conversion"].iloc[0]
    assert conv["form"] == "proportional" and conv["factor"] == pytest.approx(1.61584, abs=1e-4)
    assert (conv["factor_lo"], conv["factor_hi"]) == pytest.approx((1.5382, 1.68335), abs=2e-4)
    ref = _csv(paths["tab"] / "z15_korekta_TSD_FWD_groups.csv")
    for g in ("hwd_2024", "hwd_2026", "old_2024", "old_2025", "unconfirmed_2026"):
        for variant, ours in (("before", "none"), ("after", "main_after")):
            r = _row(ref, device_group=g, variant=variant)
            got = _row(result["groups"], group=g, variant=ours)
            assert got["n_pairs"] == int(r["n_pairs"]) and got["n_sessions"] == int(r["n_sessions"])
            assert got["median_ratio"] == pytest.approx(float(r["median_ratio"]), abs=1e-4), (g, variant)
    q = _csv(paths["tab"] / "z15_korekta_TSD_FWD_q1q3.csv").set_index("metric")
    ba = result["meta"]["before_after"]
    assert ba["q1_sd_log_diff"] == pytest.approx(float(q.loc["sd_log_ratio_diff_after_minus_before", "point"]), abs=1e-4)
    assert tuple(ba["q1_sd_log_diff_ci"]) == pytest.approx(
        (float(q.loc["sd_log_ratio_diff_after_minus_before", "ci_lo"]), float(q.loc["sd_log_ratio_diff_after_minus_before", "ci_hi"])), abs=2e-4)
    assert ba["q2_range_diff"] == pytest.approx(float(q.loc["group_range_diff_after_minus_before", "point"]), abs=1e-4)


# T-N4-07: tabela warunkow (lustro_warunki; W5)
def test_conditions_match_lustro(paths, result):
    ref = _csv(paths["tab"] / "e2bR9_lustro_warunki.csv")
    cond = result["conditions"]
    for group, value, got_group, got_value in (
            ("dt_days", "0-1", "dt_days", "0-1"), ("dt_days", "2-30", "dt_days", "2-30"), ("dt_days", ">30", "dt_days", ">30"),
            ("gof_share_w5", ">=0.8", "gof_share_w5", ">=0.8"), ("gof_share_w5", "0.5-0.8", "gof_share_w5", "0.5-0.8"),
            ("gof_share_w5", "<0.5", "gof_share_w5", "<0.5"),
            ("cv_d0_corridor_tercile", "niska (T1)", "cv_d0_corridor_tercile", "niska (T1)"),
            ("cv_d0_corridor_tercile", "wysoka (T3)", "cv_d0_corridor_tercile", "wysoka (T3)")):
        r = _row(ref, layer_group=group, layer_value=value)
        g = _row(cond, layer_group=got_group, layer_value=got_value)
        assert g["n"] == int(r["w5_n"]), (group, value)
        assert g["r"] == pytest.approx(float(r["w5_r"]), abs=2e-3), (group, value)
    inter = _row(cond, layer_group="intersection")
    assert inter["n"] == 99 and inter["r"] == pytest.approx(0.83682, abs=1e-3)
    assert _row(cond, layer_group="dt_days", layer_value="<0")["n"] == 251        # ujemne dt nie wypadaja z tabeli
    assert cond[cond.layer_group == "dt_days"]["n_candidates"].sum() == 5511
    assert (cond[cond.layer_group == "devicexcalib_interval"]["n_candidates"].sum() == 5511)


# T-N4-08: kalibracja (mnoznik W5, korekta k02) z ocena poza proba (z pominieciem sesji)
def test_calibration_multiplier_k02(paths):
    z = _csv(paths["z15"])
    f, t = correct_pair_values(z["fwd_d0"], z["d0_tsd"], z["fwd_t12_cal"], z["tsd_t12_cal"], "k02")
    tab = calibration_table(t, f, z["fwd_session_id"].to_numpy(), ("multiplier",), label="k02")
    ref = _csv(paths["tab"] / "e2bR9_lustro_kalibracja.csv")
    r_in = _row(ref, variant="W5", model="multiplier", scope="in_sample")
    r_out = _row(ref, variant="W5", model="multiplier", scope="leave_one_session_out")
    t_in = _row(tab, scope="in_sample")
    t_out = _row(tab, scope="leave_one_group_out")
    assert t_in["a"] == pytest.approx(float(r_in["a"]), abs=0.01) and t_in["a"] == pytest.approx(1.4222, abs=0.01)
    assert t_in["mae"] == pytest.approx(float(r_in["mae"]), abs=0.01) and t_out["mae"] == pytest.approx(float(r_out["mae"]), abs=0.01)
    assert t_in["median_abs_log_ratio"] == pytest.approx(float(r_in["median_abs_log_ratio"]), abs=0.01)
    assert t_out["median_abs_log_ratio"] == pytest.approx(float(r_out["median_abs_log_ratio"]), abs=0.01)
    assert t_in["n"] == 5511 and t_out["n"] == 5511


# T-N4-09: lambda d0 (z e2b2_lambda.csv)
def test_lambda_d0_constant_matches_source(paths):
    lam = _csv(paths["tab"] / "e2b2_lambda.csv")
    row = lam[lam["metric"] == "d0"].iloc[0]
    from tsdfwd_tools.common.config_n4 import LAMBDA_D0
    assert LAMBDA_D0 == pytest.approx(float(row["lambda_val"]), abs=1e-4) and LAMBDA_D0 == pytest.approx(0.11787, abs=1e-4)
    assert float(row["sigma_tsd"]) == pytest.approx(0.296408, abs=1e-5) and float(row["sigma_fwd"]) == pytest.approx(0.101763, abs=1e-5)
    assert math.isclose(float(row["sigma_fwd"]) ** 2 / float(row["sigma_tsd"]) ** 2, LAMBDA_D0, rel_tol=2e-3)
