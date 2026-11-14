"""Wyrownanie przejazdow profilem (N4, tryb geometry): testy syntetyczne T8 ze zrodla (bak\\test_e1.py, stan d89080a / 2026-10-18)
oraz zrodla wyrownania i przyczyny braku wyrownania."""

import numpy as np
import pytest

from tsdfwd_tools.compare import align as A


def test_xcorr_pearson_matches_direct_computation():
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=60), rng.normal(size=80)
    a[5] = np.nan
    b[[7, 30]] = np.nan
    lags, r, n = A.xcorr_pearson(a, b)
    for L in (-10, 0, 7, 25):
        i = np.arange(len(a))
        j = i + L
        ok = (j >= 0) & (j < len(b)) & np.isfinite(a[i]) & np.isfinite(b[np.clip(j, 0, len(b) - 1)])
        x, y = a[i][ok], b[j[ok]]
        k = int(np.where(lags == L)[0][0])
        assert n[k] == ok.sum() and r[k] == pytest.approx(np.corrcoef(x, y)[0, 1], abs=1e-9)


def test_parabola_peak_and_curve_peak():
    lags = np.arange(-5, 6, dtype=float)
    r = 1.0 - 0.05 * (lags - 1.3) ** 2
    d, rp, fl = A.curve_peak(r, lags)
    assert fl == "ok" and d == pytest.approx(1.3, abs=1e-9) and rp == pytest.approx(1.0)
    assert A.curve_peak(np.arange(5.0), np.arange(5.0))[2] == "edge"
    assert A.curve_peak(np.full(5, np.nan), np.arange(5.0))[2] == "nan"


def test_synthetic_alignment_recovers_shift_and_drift():
    r = A.synthetic_alignment(20260927, 8000, 2.3, 0.8, 0.3)
    assert r["n_used"] == r["n_blocks"] >= 7 and r["err_rms_inner"] < 0.07 and r["err_max_inner"] < 0.15 and r["err_max_all"] < 0.6
    res = [A.synthetic_alignment(seed, 4000, 1.3, 0.0, 0.1) for seed in range(20)]
    rms = np.array([x.get("err_rms_inner", np.nan) for x in res])
    bias = np.array([x.get("err_mean_inner", np.nan) for x in res])
    assert np.isfinite(rms).all() and rms.max() < 0.08 and abs(bias.mean()) < 0.05


def _two_passes(n=6000, seed=3):
    rng = np.random.default_rng(seed)
    pad = 300
    base = np.cumsum(rng.normal(size=n + 2 * pad))
    base = base - A.running_median_nan(base)
    grid = np.arange(-pad, n + pad, dtype=float)
    s_true_ref = np.arange(0.0, n)
    s_true_run = np.arange(0.0, n - 40) + 0.37
    delta_true = lambda s: 1.7 + 0.6 * s / 1000.0                    # noqa: E731
    s_gps_run = s_true_run - delta_true(s_true_run)
    sd = np.std(base)
    p_ref = dict(pass_id=0, s=s_true_ref, prof=np.interp(s_true_ref, grid, base) + 0.2 * sd * rng.normal(size=n))
    p_run = dict(pass_id=1, s=s_gps_run, prof=np.interp(s_true_run, grid, base) + 0.2 * sd * rng.normal(size=len(s_true_run)))
    return p_ref, p_run, s_true_run, s_gps_run, delta_true, n


def test_align_corridor_recovers_delta_and_common_sref():
    p_ref, p_run, s_true_run, s_gps_run, delta_true, n = _two_passes()
    rows = []
    cen = A.align_corridor([p_ref, p_run], float(n), rows)
    cs, Ls = p_run["fn"]
    inner = (s_gps_run >= cs[0]) & (s_gps_run <= cs[-1])
    rec = np.interp(s_gps_run, cs, Ls)
    assert p_ref["align_ref"] == "reference" and p_run["align_ref"] == "profile_ref"
    assert np.abs(rec - delta_true(s_true_run))[inner].max() < 0.12 and cen == pytest.approx(np.median(Ls) / 2, abs=1e-9)
    s_ref_run = s_gps_run + rec - cen
    assert np.abs(s_ref_run - (s_true_run - cen))[inner].max() < 0.12     # to samo miejsce fizyczne = ten sam s_ref (rama GPS odniesienia)
    assert {"pass_id", "round", "s_center", "delta_m", "r", "flag", "n_pairs", "used"} <= set(rows[0])
    sref, src, note = A.apply_alignment(p_run, cen)
    assert note is None and set(src) <= {"profile", "profile_extrap"} and "profile" in set(src)
    sref_r, src_r, _ = A.apply_alignment(p_ref, cen)
    assert set(src_r) == {"reference"} and np.allclose(sref_r, p_ref["s"] - cen)


def test_no_alignment_sources_and_notes():
    p_ref, p_run, *_ , n = _two_passes()
    flat = dict(pass_id=2, s=np.arange(0.0, 3000.0), prof=np.full(3000, np.nan))                # brak profilu
    short = dict(pass_id=3, s=np.arange(0.0, 300.0), prof=np.random.default_rng(0).normal(size=300))   # < 500 wspolnych probek
    cen = A.align_corridor([p_ref, p_run, flat, short], float(n))
    sref, src, note = A.apply_alignment(flat, cen)
    assert note == "no_profile" and set(src) == {"gps"} and np.array_equal(sref, flat["s"])
    assert A.apply_alignment(short, cen)[2] == "short"
    noise_pass = dict(pass_id=4, s=np.arange(0.0, 6000.0), prof=np.random.default_rng(9).normal(size=6000))   # profil bez wspolnej struktury
    A.align_corridor([p_ref, noise_pass], float(n))
    assert A.apply_alignment(noise_pass, 0.0)[2] == "no_block_r08" and noise_pass["align_ref"] == "gps"


def test_resample_requires_neighbours_within_gap():
    s = np.array([0.0, 1.0, 2.0, 10.0, 11.0])
    v = np.array([0.0, 1.0, 2.0, 10.0, 11.0])
    out = A.resample(s, v, np.array([0.5, 1.5, 5.0, 10.5, 12.0]))
    assert out[0] == pytest.approx(0.5) and np.isnan(out[2]) and out[3] == pytest.approx(10.5) and np.isnan(out[4])
