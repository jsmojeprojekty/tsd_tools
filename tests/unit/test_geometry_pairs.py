"""Testy syntetyczne polozenia plyty FWD i parowania geometrycznego (N4, tryb geometry).

Odpowiadaja testom T1-T5 i T11 ze zrodla (C:\\projects\\sql_tsd_fwd\\bak\\test_e2b1.py, stan d89080a / 2026-10-18)."""

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.compare import fwd_position as FP
from tsdfwd_tools.compare import geo as G
from tsdfwd_tools.compare import pairing as PA


def test_fit_run_robust_recovers_a_and_eps_and_rejects_gross_errors():
    rng = np.random.default_rng(11)
    n = 40
    station_m = np.sort(rng.uniform(0, 2.0, n))               # km
    direction, factor = 1, 1000
    a_true, eps_true_ppm = 1234.5, 350.0
    y = a_true + direction * factor * (1 + eps_true_ppm * 1e-6) * station_m + rng.normal(0, 0.05, n)
    y[[3, 17, 33]] += np.array([25.0, -30.0, 40.0])
    fit = FP.fit_run_robust(station_m, y, direction, factor)
    assert abs(fit["a"] - a_true) < 0.3 and abs(fit["eps_ppm"] - eps_true_ppm) < 50 and fit["n_rejected"] == 3


def test_antenna_rule_table():
    assert FP.plate_offset("8002-367", "2025-06-01") == (5.5, "old", 1)
    assert FP.plate_offset("8002-367", "2025-10-09") == (0.0, "new", 1)          # od daty granicznej wlacznie
    assert FP.plate_offset("8082-119", "2022-08-31") == (1.0, "hwd", 1)
    assert FP.plate_offset("8002-369", "2024-01-01") == (1.0, "unconfirmed", 0)
    assert FP.plate_offset("XXXX", "2022-01-01") == (0.0, "unknown", 0)
    assert FP.plate_offset("8002-367", "") == (0.0, "new", 1)                      # brak daty: najpozniejsza regula (jak zrodlo)
    custom = [FP.AntennaRule("8002-367", 5.0, "old", 1, None, "2025-01-01"), FP.AntennaRule("8002-367", 0.0, "new", 1, "2025-01-01")]
    assert FP.plate_offset("8002-367", "2024-12-31", custom) == (5.0, "old", 1)
    assert FP.plate_offset("8002-367", "2025-01-01", custom) == (0.0, "new", 1)


def test_unit_factor_and_direction_reversed_session():
    station_m = np.linspace(0.0, 1.0, 20)
    s_ant = 500.0 - 1000.0 * station_m + np.random.default_rng(2).normal(0, 0.1, 20)    # maleje: kierunek -1
    f, d, ratio = FP.unit_factor(station_m, s_ant)
    assert (f, d) == (1000, -1) and ratio == pytest.approx(1000, rel=0.01)
    st = pd.DataFrame(dict(session_id=1, corridor_id=0, s_ant=s_ant, station_m=station_m))
    direction, factor, sess = FP.direction_from_data(st)
    assert (direction == -1).all() and (factor == 1000).all() and sess[1]["units"] == "km"
    f2, d2, _ = FP.unit_factor(station_m * 1000, s_ant)                                  # station_m w metrach
    assert (f2, d2) == (1, -1)


def test_split_runs_reset_dmi_failure_jump_and_turnaround():
    sm = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.0, 0.1, 0.2, 0.2, 0.3, 0.4, 0.4, 5.0, 5.1, 5.0])
    cid = np.zeros(len(sm), dtype=int)
    run = FP.split_runs(sm, cid, direction=1)
    assert run[0] == run[9] and run[10] != run[9] and run[13] != run[12] and run[17] != run[16] and run[19] != run[18]
    run2 = FP.split_runs(np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5]), np.array([0, 0, 0, 1, 1, 1]), direction=1)
    assert run2[3] != run2[2]                                                            # zmiana korytarza


def test_layers_and_windows():
    assert PA.layer_of(0.5, 0.8) == "A" and PA.layer_of(1.5, 2.0) == "B" and PA.layer_of(0.1, 4.9) == "C"
    assert PA.layer_of(3.0, 6.0) == "X" and PA.layer_of(None, 1.0) == "X" and PA.layer_of(float("nan"), 1.0) == "X"
    s = np.arange(11.0)
    tsd_id = np.arange(100, 111)
    lat = np.array([0.2] * 6 + [0.8] * 5)
    gof = np.array([0.9, 0.9, 0.9, 0.2, 0.2, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
    w = PA.window_stats(s, tsd_id, lat, gof, 5.0, 1.0)
    assert w["n"] == 3 and (w["tsd_id_min"], w["tsd_id_max"]) == (104, 106)
    assert PA.window_stats(s, tsd_id, lat, gof, 5.0, 5.0)["n"] == 11
    assert PA.nearest_row(s, 5.4) == 5
    w0 = PA.window_stats(s, tsd_id, lat, gof, 100.0, 1.0)
    assert w0["n"] == 0 and w0["tsd_id_min"] is None


def test_null_pairs_shift_and_permutation_reproducible():
    s = np.arange(0.0, 2001.0)
    pr = dict(s=s, tsd_id=np.arange(len(s)), lat=np.full(len(s), 0.3), gof=np.full(len(s), 0.9))
    cand = pd.DataFrame([dict(pair_id=1, s_fwd=1000.0, corridor_id=7, pass_id=42)])
    out = PA.build_null_pairs(cand, {42: pr})
    assert {"shift_plus200", "shift_minus200", "permutation"} == set(out["null_type"])
    assert (out["pass_id"] == 42).all() and (out["corridor_id"] == 7).all()
    assert (np.abs(out["center_s"] - 1000.0) >= 5.0).all()
    assert out.loc[out.null_type == "shift_plus200", "center_s"].iloc[0] == pytest.approx(1200.0)
    assert out.loc[out.null_type == "shift_minus200", "center_s"].iloc[0] == pytest.approx(800.0)
    perm = out.loc[out.null_type == "permutation", "center_s"].iloc[0]
    assert abs(perm - 1000.0) >= PA.NULL_PERM_MIN_M - 1e-6
    again = PA.build_null_pairs(cand, {42: pr})
    assert again.loc[again.null_type == "permutation", "center_s"].iloc[0] == perm


def test_window_value_needs_three_valid_rows():
    s = np.arange(0.0, 21.0)
    d0 = np.full(21, 200.0)
    d0[8:13] = np.nan                                                # w oknie +-1 m wokol 10 same NaN
    v, n, ok = PA.window_value(s, d0, 10.0, 5.0)
    assert ok and n == 6 and v == 200.0                              # okno +-5 m: wiersze 5..15 bez 8..12
    v1, n1, ok1 = PA.window_value(s, d0, 10.0, 1.0)
    assert not ok1 and n1 == 0 and np.isnan(v1)
    d0b = np.where(np.arange(21) % 2 == 0, 100.0, 300.0)
    v2, n2, ok2 = PA.window_value(s, d0b, 10.0, 1.0)                 # wiersze 9, 10, 11: 300, 100, 300 -> mediana 300
    assert ok2 and n2 == 3 and v2 == 300.0


def test_eps_short_zero_variant_in_compute_positions():
    rng = np.random.default_rng(55)
    direction, factor = 1, 1000
    sm_short = np.array([0.0, 0.02, 0.04, 0.06])
    y_short = 100.0 + direction * factor * sm_short + rng.normal(0, 0.1, 4)
    fit = FP.fit_run_robust(sm_short, y_short, direction, factor, force_eps_zero=True)
    assert fit["eps_ppm"] == 0.0 and fit["slope"] == pytest.approx(direction * factor)

    def station_frame(session, sm, y, first_id):
        return pd.DataFrame(dict(session_id=session, station_id=first_id + np.arange(len(sm)), station_m=sm, corridor_id=0,
                                 direction=direction, factor=factor, s_plate_gps=y, era="new",
                                 time=[f"{i:02d}" for i in range(len(sm))]))

    p = FP.PositionParams(sigma_era={k: 0.1 for k in ("new", "old", "hwd", "hwd_cautious", "unconfirmed", "unknown")})
    _, runs_short = FP.compute_positions(station_frame(1, sm_short, y_short, 0), p)
    assert len(runs_short) == 1 and runs_short[0]["eps_forced_zero"] == 1 and runs_short[0]["eps_ppm"] == 0.0
    sm_long = np.linspace(0.0, 1.5, 15)
    y_long = 200.0 + direction * factor * (1 + 500e-6) * sm_long + rng.normal(0, 0.05, 15)
    res, runs_long = FP.compute_positions(station_frame(2, sm_long, y_long, 100), p)
    assert runs_long[0]["eps_forced_zero"] == 0 and abs(runs_long[0]["eps_ppm"] - 500.0) < 50
    assert (res["pos_source"] == "dmi").all() and np.isfinite(res["s_fwd"]).all()


def _meridian_run(n, lat0=50.0, step_m=1.0):
    lat = lat0 + np.arange(n) * (step_m / 111200.0)
    return np.arange(n, dtype=float) * step_m, lat, np.full(n, 19.0)


def test_end_to_end_axis_stations_pairs_and_values():
    """TSD jedzie wzdluz poludnika 19 E; stacje FWD stoja na osi co 100 m (station_m w km), jedna z nich 1,2 m w bok."""
    chain, lat, lon = _meridian_run(2500)
    run = G.prepare_run(chain, lat, lon)
    corrs, assigned, info = G.build_axis({"t1": run})
    assert info["n_corridors"] == 1
    cid, s_gps, lat_m, _ = assigned["t1"]
    ok = cid >= 0
    # stacje FWD: wspolrzedne anteny = punkty toru GPS (lag TSD dotyczy tylko TSD); jazda zgodnie z pikietazem
    pos = np.arange(300.0, 2200.0, 100.0)
    st_lat = np.interp(pos, chain, lat)
    st_lon = np.full(len(pos), 19.0)
    st_lon[5] += 1.2 / (111200.0 * np.cos(np.radians(50.0)))           # 1,2 m na wschod (prawo od kierunku na polnoc)
    stations = pd.DataFrame(dict(station_id=np.arange(len(pos)), session_id=1, station_m=(pos - 300.0) / 1000.0,
                                 lat=st_lat, lon=st_lon, time=[f"2025-07-01T10:{i:02d}:00" for i in range(len(pos))],
                                 device="8082-119", date="2025-07-01", heading_deg=0.0))
    plate, sess, runs = FP.fwd_plate_positions(corrs, stations)
    assert (plate["lane_match"] == "same").all() and sess.loc[0, "direction"] == 1 and sess.loc[0, "units"] == "km"
    assert (plate["pos_source"] == "dmi").all() and runs.loc[0, "fit_valid"] == 1
    # plyta HWD 1,0 m wstecz od anteny: s_fwd = s_ant - 1
    assert np.nanmax(np.abs(plate["s_fwd"] - (plate["s_ant"] - 1.0))) < 0.5
    assert plate.loc[5, "lat_ant"] == pytest.approx(-1.2, abs=0.1)     # na prawo od kierunku jazdy: lateral ujemny (+ = lewo)
    # pary z przejazdem TSD w tym samym roku
    ix = np.nonzero(ok)[0]
    pass_rows = {1: dict(s=s_gps[ix], tsd_id=ix, lat=lat_m[ix], gof=np.full(len(ix), 0.9), d0=np.full(len(ix), 180.0))}
    passes = pd.DataFrame([dict(pass_id=1, file_id=1, corridor_id=int(cid[ix[0]]), date="2025-07-20")])
    cand = PA.build_candidates(plate, passes, pass_rows)
    assert len(cand) == len(pos) and (cand["same_year"] == 1).all() and (cand["dt_days"] == 19.0).all()
    assert (cand["win5_n"] >= 9).all()
    assert cand.loc[5, "layer"] == "B"                                  # |dlat| ~ 1,2 m: ponad 1,0 (nie A), do 1,75 (B)
    assert (cand.drop(index=5)["layer"] == "A").all()
    nulls = PA.build_null_pairs(cand, pass_rows)
    assert len(nulls) >= 2 * len(cand)
    vals = PA.pair_values(cand, pass_rows)
    assert vals["window_ok"].all() and (vals["value"] == 180.0).all()
