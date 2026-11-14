"""Testy jednostkowe N2 layer_temp: parametry, czas/DST, klient Open-Meteo (atrapa HTTP), solver, kalibracja, flagi, konfiguracja, CLI."""

from __future__ import annotations

import json
import urllib.error

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_n2 import build_n2_config, effective_depth_cm, load_n2_config
from tsdfwd_tools.layer_temp import constants as C
from tsdfwd_tools.layer_temp.bells3 import bells3, sin18
from tsdfwd_tools.layer_temp.calibrate import calibrate_single_shot
from tsdfwd_tools.layer_temp.flags import LayerFlag, flags_to_text
from tsdfwd_tools.layer_temp.frame import at_time, build_frame, longwave_down
from tsdfwd_tools.layer_temp.meteo import (MeteoStore, MeteoUnavailable, cache_basename, fetch_open_meteo, om_utc_to_local,
                                           plan_windows, quantize)
from tsdfwd_tools.layer_temp.params import EXPECTED_BUILTIN_HASH, load_params
from tsdfwd_tools.layer_temp.predict import CellDay, layer_temperature, predict_at, run_survey
from tsdfwd_tools.layer_temp.solver import simulate_eb
from tsdfwd_tools.layer_temp.uncertainty import u95_for_hour

PARAMS = load_params()


# ------------------------------------------------------------------ pomocnicze: syntetyczne meteo

def make_om(start="2025-06-01", end="2025-07-20", *, cloud=20.0, temp_mean=18.0, temp_amp=7.0, swr_peak=850.0):
    """Godzinowe meteo w czasie lokalnym: dobowy przebieg temperatury, promieniowanie dzienne (sinus 5-21), staly wiatr."""
    idx = pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(hours=23), freq="1h").as_unit("ns")
    h = idx.hour.to_numpy() + idx.minute.to_numpy() / 60.0
    temp = temp_mean + temp_amp * np.sin(2 * np.pi * (h - 9) / 24)
    swr = np.where((h >= 5) & (h <= 21), swr_peak * np.clip(np.sin(np.pi * (h - 5) / 16), 0.0, None) ** 1.5, 0.0)
    return pd.DataFrame({"temperature_2m": temp, "dew_point_2m": temp - 8.0, "wind_speed_10m": 3.0,
                         "cloud_cover": cloud, "shortwave_radiation": swr, "snow_depth": 0.0}, index=idx)


def write_cache(cache_dir, om, lat=52.25, lon=21.0, start="2025-06-01", end="2025-07-20"):
    cache_dir.mkdir(parents=True, exist_ok=True)
    base = cache_dir / cache_basename(lat, lon, start, end)
    (cache_dir / (base.name + ".csv")).write_text(om.rename_axis("timestamp").to_csv(), encoding="utf-8")
    (cache_dir / (base.name + ".json")).write_text(
        json.dumps({"start": start, "end": end, "grid_lat": lat, "grid_lon": lon, "fetched_at": "2026-01-01T00:00:00"}), encoding="utf-8")


@pytest.fixture(scope="module")
def om_summer():
    return make_om()


@pytest.fixture(scope="module")
def ctx_noon(om_summer):
    t = pd.Timestamp("2025-07-10 12:00")
    return CellDay(om_summer, t.normalize(), t, PARAMS), t


# ------------------------------------------------------------------ T-N2-09: parametry zamrozone

def test_builtin_params_hash():
    """Dryf parametrow: hash sekcji `parameters` musi byc rowny wartosci zapisanej w kodzie."""
    assert PARAMS.hash == EXPECTED_BUILTIN_HASH


def test_params_values_and_validation(tmp_path):
    assert PARAMS.alpha == pytest.approx(1.1180916449068726e-06)
    assert PARAMS.eb["h0"] == pytest.approx(13.703653335884345)
    assert PARAMS.a_default == 1.0 and PARAMS.a_bounds == (0.03, 1.0)
    assert len(PARAMS.beta50) == 5 and len(PARAMS.beta_ir) == 5
    bad = tmp_path / "p.json"
    bad.write_text(json.dumps({"parameters": {"alpha_m2_s": 1e-6}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_params(bad)
    doc = json.loads((__import__("importlib.resources", fromlist=["files"]).files("tsdfwd_tools.data") / "params_TN.json").read_text(encoding="utf-8"))
    doc["parameters"]["alpha_m2_s"] = 2e-6
    mod = tmp_path / "mod.json"
    mod.write_text(json.dumps(doc), encoding="utf-8")
    assert load_params(mod).hash != PARAMS.hash                      # zmiana parametru zmienia hash


# ------------------------------------------------------------------ T-N2-07: czas, DST, UTC

def test_om_utc_to_local_summer_and_winter_offsets():
    idx = pd.to_datetime(["2025-07-10 10:00", "2025-01-10 10:00"])
    out = om_utc_to_local(pd.DataFrame({"x": [1.0, 2.0]}, index=idx))
    assert list(out.index) == [pd.Timestamp("2025-01-10 11:00"), pd.Timestamp("2025-07-10 12:00")]      # +1 h zima, +2 h lato


def test_om_utc_to_local_autumn_double_hour_keeps_first():
    """2025-10-26: lokalna godzina 02:00 wystepuje dwa razy (CEST i CET) - zostaje pierwsze wystapienie (UTC 00:00)."""
    idx = pd.date_range("2025-10-25 22:00", "2025-10-26 03:00", freq="1h")
    out = om_utc_to_local(pd.DataFrame({"x": np.arange(len(idx), dtype=float)}, index=idx))
    assert out.index.is_unique
    assert out.loc[pd.Timestamp("2025-10-26 02:00"), "x"] == 2.0                     # UTC 00:00, nie 01:00
    assert out.loc[pd.Timestamp("2025-10-26 03:00"), "x"] == 4.0                     # UTC 02:00


def test_om_utc_to_local_spring_gap_has_no_row():
    """2025-03-30: godzina lokalna 02:00 nie istnieje - brak wiersza (interpolacja po czasie przy skladaniu cech)."""
    idx = pd.date_range("2025-03-29 23:00", "2025-03-30 03:00", freq="1h")
    out = om_utc_to_local(pd.DataFrame({"x": np.arange(len(idx), dtype=float)}, index=idx))
    assert pd.Timestamp("2025-03-30 02:00") not in out.index
    assert out.loc[pd.Timestamp("2025-03-30 03:00"), "x"] == 2.0                     # UTC 01:00


def test_quantize_and_cache_name():
    assert quantize(52.2676, 21.0246) == (52.25, 21.0)
    assert quantize(50.21, 19.17) == (50.2, 19.15)
    assert cache_basename(52.25, 21.0, "2025-06-01", "2025-07-20") == "om_p52.25_p21.00_2025m06m01_2025m07m20"


def test_plan_windows_merges_close_days():
    w = plan_windows([pd.Timestamp("2025-07-10 12:00"), pd.Timestamp("2025-07-12 08:00"), pd.Timestamp("2025-09-30")], 35)
    assert len(w) == 2
    assert w[0] == (pd.Timestamp("2025-06-05"), pd.Timestamp("2025-07-13"))
    assert w[1] == (pd.Timestamp("2025-08-26"), pd.Timestamp("2025-10-01"))


# ------------------------------------------------------------------ T-N2-08: tryb sieciowy (atrapa HTTP)

def fake_response(start_date, end_date):
    idx = pd.date_range(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(hours=23), freq="1h")
    n = len(idx)
    hourly = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in idx]}
    for k in C.OM_HOURLY:
        hourly[k] = [10.0 + i * 0.01 for i in range(n)]
    hourly["snow_depth"] = [None] * n                                              # brak wartosci -> NaN
    return {"latitude": 52.3, "longitude": 21.1, "elevation": 100.0, "hourly": hourly, "hourly_units": {"temperature_2m": "C"}}


class Recorder:
    def __init__(self, failures=()):
        self.calls, self.failures = [], list(failures)

    def __call__(self, url, params, timeout):
        self.calls.append((url, dict(params), timeout))
        if self.failures:
            raise self.failures.pop(0)
        return fake_response(params["start_date"], params["end_date"])


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "msg", {}, None)


def test_fetch_request_parameters_and_local_time_slice():
    rec = Recorder()
    df, meta = fetch_open_meteo(52.25, 21.0, "2025-07-10", "2025-07-12", http_get=rec, sleep=lambda s: None)
    url, params, _ = rec.calls[0]
    assert url == "https://archive-api.open-meteo.com/v1/archive"
    assert params["timezone"] == "UTC" and params["wind_speed_unit"] == "ms"       # erratum czasu OM: nigdy Europe/Warsaw
    assert params["hourly"].split(",") == list(C.OM_HOURLY) and len(C.OM_HOURLY) == 6
    assert params["start_date"] == "2025-07-09" and params["end_date"] == "2025-07-13"       # [start-1 d, end+1 d] w UTC
    assert df.index.min() == pd.Timestamp("2025-07-10 00:00") and df.index.max() == pd.Timestamp("2025-07-12 23:00")
    assert meta["grid_lat"] == 52.3 and meta["api_timezone_param"] == "UTC" and meta["n_missing"]["snow_depth"] == len(df)
    # etykieta lokalna 00:00 pochodzi z UTC 22:00 dnia poprzedniego (lato, +2 h): pierwsza wartosc = indeks godziny 22 w odpowiedzi
    assert df["temperature_2m"].iloc[0] == pytest.approx(10.0 + 22 * 0.01)


def test_fetch_retries_on_429_then_succeeds():
    rec, waits = Recorder([http_error(429), http_error(429)]), []
    df, _ = fetch_open_meteo(52.25, 21.0, "2025-07-10", "2025-07-10", http_get=rec, sleep=waits.append)
    assert len(rec.calls) == 3 and waits == [C.RETRY_WAIT_S, C.RETRY_WAIT_S] and not df.empty


def test_fetch_gives_up_after_max_retries_and_on_server_error():
    rec, waits = Recorder([http_error(429)] * C.MAX_RETRY), []
    with pytest.raises(MeteoUnavailable):
        fetch_open_meteo(52.25, 21.0, "2025-07-10", "2025-07-10", http_get=rec, sleep=waits.append)
    assert len(rec.calls) == C.MAX_RETRY
    rec2 = Recorder([http_error(500)])
    with pytest.raises(MeteoUnavailable):
        fetch_open_meteo(52.25, 21.0, "2025-07-10", "2025-07-10", http_get=rec2, sleep=lambda s: None)
    assert len(rec2.calls) == 1


def test_store_offline_makes_no_requests(tmp_path):
    rec = Recorder()
    store = MeteoStore(tmp_path / "empty", offline=True, http_get=rec)
    with pytest.raises(MeteoUnavailable):
        store.get(52.25, 21.0, pd.Timestamp("2025-06-05"), pd.Timestamp("2025-07-10 12:00"))
    assert rec.calls == []


def test_store_downloads_once_and_reuses_cache(tmp_path):
    rec = Recorder()
    store = MeteoStore(tmp_path / "c", offline=False, http_get=rec, sleep=lambda s: None)
    lo, hi = pd.Timestamp("2025-06-05"), pd.Timestamp("2025-07-10 23:40")
    om, info = store.get(52.27, 21.02, lo, hi)
    assert len(rec.calls) == 1 and store.n_fetched == 1
    p = rec.calls[0][1]
    assert p["latitude"] == 52.25 and p["longitude"] == 21.0                      # zapytanie na siatce 0,05 st.
    assert p["end_date"] == "2025-07-12"                                           # dzien pomiaru + 1 (ogon po 23:00) + 1 d marginesu UTC
    assert info["grid_lat"] == 52.3 and pd.Timestamp("2025-07-11 05:00") in om.index        # dane po 23:00 dnia pomiaru sa dostepne
    store.get(52.27, 21.02, lo, hi)
    store2 = MeteoStore(tmp_path / "c", offline=True)                              # nowa instancja czyta z dysku (csv)
    store2.get(52.27, 21.02, lo, hi)
    assert len(rec.calls) == 1


# ------------------------------------------------------------------ T-N2-06: solver i kalibracja

def _const_frame(n_days=20, ta=15.0, wind=3.0, sw=0.0, cloud=30.0):
    idx = pd.date_range("2025-06-01", periods=n_days * 144, freq="10min").as_unit("ns")
    f = pd.DataFrame({"temperature_2m": ta, "dew_point_2m": ta - 6.0, "wind_speed_10m": wind, "cloud_cover": cloud, "swr": sw}, index=idx)
    f["ld"] = longwave_down(f.dew_point_2m, f.temperature_2m, f.cloud_cover)
    return f


def test_solver_steady_state_profile_and_surface_energy_balance():
    f = _const_frame(sw=400.0)
    bottom = pd.Series(12.0, index=f.index)
    T = simulate_eb(f, bottom, PARAMS, 0.7)
    assert np.isnan(T[:C.SPINUP_STEPS]).all() and np.isfinite(T[C.SPINUP_STEPS:]).all()
    last = T[-1]
    assert np.max(np.abs(T[-1] - T[-2])) < 1e-4                                       # stan ustalony
    assert last[-1] == pytest.approx(12.0, abs=1e-9)                                  # dolny BC (Dirichlet)
    lin = last[0] + (last[-1] - last[0]) * np.linspace(0, 1, C.NZ)
    assert np.max(np.abs(last - lin)) < 1e-3                                          # profil liniowy (przewodzenie stacjonarne)
    ts, t1 = last[0] + C.KELVIN, last[1] + C.KELVIN
    h = PARAMS.eb["h0"] + PARAMS.eb["h1"] * 3.0
    kc = PARAMS.alpha * PARAMS.eb["c_vol"]
    ta_k = 15.0 + C.KELVIN
    ld = float(f.ld.iloc[-1])
    resid = 0.7 * 400.0 + C.EPS_SURF * ld + h * ta_k - (C.EPS_SURF * C.SIGMA * ts ** 4 + h * ts + kc / C.DZ_M * (ts - t1))
    assert abs(resid) < 1e-3                                                          # bilans energii powierzchni [W/m2]


def test_solver_without_forcing_stays_at_bottom_temperature_isothermal():
    """Brak slonca, bottom = powietrze = temperatura poczatkowa: profil izotermiczny nie dryfuje (bilans radiacyjny ~ 0 dla ld = eps*sigma*T^4)."""
    idx = pd.date_range("2025-06-01", periods=10 * 144, freq="10min").as_unit("ns")
    f = pd.DataFrame({"temperature_2m": 10.0, "wind_speed_10m": 0.0, "swr": 0.0}, index=idx)
    f["ld"] = C.SIGMA * (10.0 + C.KELVIN) ** 4 / C.EPS_SURF * C.EPS_SURF            # LW = sigma*T^4: promieniowanie nieba rowne emisji
    T = simulate_eb(f, pd.Series(10.0, index=idx), PARAMS, 1.0)
    assert np.nanmax(np.abs(T - 10.0)) < 0.05


def test_solver_nonfinite_input_returns_nan():
    f = _const_frame(n_days=5)
    f.loc[f.index[300], "temperature_2m"] = np.nan
    assert np.isnan(simulate_eb(f, pd.Series(12.0, index=f.index), PARAMS, 1.0)).all()


def test_surface_temperature_increases_with_a_sw_at_noon(ctx_noon):
    ctx, t = ctx_noon
    assert ctx.value_at(1.0, t, 0) > ctx.value_at(0.5, t, 0) > ctx.value_at(0.03, t, 0) + 5.0


def test_calibration_round_trip_recovers_a_sw(ctx_noon):
    ctx, t = ctx_noon
    a_true = 0.55
    target = ctx.value_at(a_true, t, 0)
    cal = calibrate_single_shot(lambda a: ctx.value_at(a, t, 0), target, 1.0)
    assert cal.flag == "ok" and cal.a_sw == pytest.approx(a_true, abs=2e-3)
    # to samo przez interfejs wysokiego poziomu: odczyt pirometru = Ts + korekta IR w chwili t
    ir = target + at_time(ctx.index, ctx.delta, t)
    res = predict_at(ctx, t, ir, 0.12)
    assert res.calib_flag == "ok" and res.a_sw == pytest.approx(a_true, abs=2e-3)
    assert res.ts_sim == pytest.approx(target, abs=2e-3) and res.ir_masa == pytest.approx(target, abs=1e-9)


def test_calibrate_single_shot_branches():
    lin = lambda a: 10.0 + 20.0 * a                                                    # noqa: E731
    assert calibrate_single_shot(lin, 20.0, 1.0).a_sw == pytest.approx(0.5, abs=1e-3)
    assert calibrate_single_shot(lin, 40.0, 1.0).flag == "bound_hi" and calibrate_single_shot(lin, 40.0, 1.0).a_sw == 1.0
    assert calibrate_single_shot(lin, 5.0, 1.0).flag == "bound_lo" and calibrate_single_shot(lin, 5.0, 1.0).a_sw == 0.03
    gate = calibrate_single_shot(lambda a: 10.0 + 0.5 * a, 10.3, 1.0)
    assert gate.flag == "gate" and gate.a_sw == 1.0                                    # |Ts(1) - Ts(0,03)| < 1 C
    assert calibrate_single_shot(lambda a: float("nan"), 20.0, 1.0).flag == "nosim"


# ------------------------------------------------------------------ flagi i niepewnosc

def test_flags_night_ir_missing_calib_off_depth_season_tail(om_summer):
    t = pd.Timestamp("2025-07-10 03:30")                                               # >= 6 h po zachodzie: SW_ma6 < 5 W/m2
    ctx = CellDay(om_summer, t.normalize(), t, PARAMS)
    r = predict_at(ctx, t, 12.0, 0.12)
    assert r.flags & LayerFlag.NIGHT and r.calib_flag in ("gate", "bound_hi", "bound_lo", "ok")
    r_none = predict_at(ctx, t, float("nan"), 0.12)
    assert r_none.flags & LayerFlag.IR_MISSING and r_none.value == r_none.value_uncal and r_none.calib_flag == "none"
    r_off = predict_at(ctx, t, 12.0, 0.12, calibration="none")
    assert r_off.flags & LayerFlag.CALIB_OFF and r_off.value == r_off.value_uncal
    assert predict_at(ctx, t, 12.0, 0.07).flags & LayerFlag.DEPTH_NOT_VALIDATED
    r_deep = predict_at(ctx, t, 12.0, 0.60)
    assert r_deep.flags & LayerFlag.DEPTH_OUT_OF_RANGE and np.isnan(r_deep.value)
    assert not predict_at(ctx, t, 12.0, 0.10).flags & LayerFlag.DEPTH_NOT_VALIDATED          # 10 cm zwalidowane
    # poza sezonem i ogon (po ostatniej godzinie danych)
    om_w = make_om("2025-01-01", "2025-02-20")
    tw = pd.Timestamp("2025-02-20 23:40")
    rw = predict_at(CellDay(om_w, tw.normalize(), tw, PARAMS), tw, 3.0, 0.12)
    assert rw.flags & LayerFlag.OUT_OF_SEASON and rw.flags & LayerFlag.TAIL_EXTRAPOLATED
    assert "OUT_OF_SEASON" in flags_to_text(rw.flags)


def test_flag_snow_and_position():
    om = make_om()
    om["snow_depth"] = 0.05
    t = pd.Timestamp("2025-07-10 12:00")
    r = predict_at(CellDay(om, t.normalize(), t, PARAMS), t, 30.0, 0.12, lat=40.0, lon=10.0)
    assert r.flags & LayerFlag.SNOW and r.flags & LayerFlag.POSITION_OUT_OF_POLAND


def test_meteo_gap_flag_when_raw_data_missing(om_summer):
    om = om_summer.copy()
    om.loc["2025-07-09 10:00":"2025-07-09 14:00", "temperature_2m"] = np.nan
    t = pd.Timestamp("2025-07-10 12:00")
    r = predict_at(CellDay(om, t.normalize(), t, PARAMS), t, 30.0, 0.12)
    assert r.flags & LayerFlag.METEO_GAP and np.isfinite(r.value)                     # luka wewnetrzna: interpolacja, ale flaga


def test_u95_by_hour_bins():
    assert u95_for_hour(9.0) == pytest.approx(2 * 1.378)
    assert u95_for_hour(14.5) == pytest.approx(2 * 1.889)
    assert u95_for_hour(3.0) == pytest.approx(2 * 2.167) and u95_for_hour(23.5) == pytest.approx(2 * 2.167)
    assert u95_for_hour(9.0) >= C.U95_MIN_C and np.isnan(u95_for_hour(float("nan")))


# ------------------------------------------------------------------ BELLS3

def test_bells3_sin18_window_saturation_and_wrap():
    assert sin18(8.0, 15.5, 11.0) == -1.0                                              # okno 05:00-11:00 -> -1
    assert sin18(14.0, 15.5, 11.0) == pytest.approx(np.sin(2 * np.pi * (14.0 - 15.5) / 18))
    assert sin18(2.0, 15.5, 11.0) == pytest.approx(np.sin(2 * np.pi * (26.0 - 15.5) / 18))      # po polnocy +24 h
    assert sin18(np.array([8.0, 14.0]), 15.5, 11.0).shape == (2,)


def test_bells3_value():
    ir, t1d, hour = 40.0, 18.0, 14.0
    s155, s135 = sin18(hour, 15.5, 11.0), sin18(hour, 13.5, 9.0)
    logd = np.log10(120.0) - 1.25
    expect = 0.95 + 0.892 * ir + logd * (-0.448 * ir + 0.621 * t1d + 1.83 * s155) + 0.042 * ir * s135
    assert bells3(ir, t1d, hour, 120.0) == pytest.approx(expect)


# ------------------------------------------------------------------ interfejs wysokiego poziomu i seria

def _survey(rows):
    return pd.DataFrame(rows, columns=["measured_at_local", "latitude", "longitude", "t_surface", "t_air"])


def test_run_survey_matches_single_calls_and_is_causal(tmp_path, om_summer):
    write_cache(tmp_path / "cache", om_summer)
    store = MeteoStore(tmp_path / "cache", offline=True)
    df = _survey([["2025-07-10 09:15:00", 52.26, 21.01, 28.0, 20.0], ["2025-07-10 13:40:00", 52.26, 21.01, 44.0, 24.0],
                  ["2025-07-12 15:05:00", 52.26, 21.01, 41.0, 25.0]])
    both = run_survey(df, store, PARAMS, with_bells3=True)
    for k in range(3):
        one = layer_temperature(df.measured_at_local[k], 52.26, 21.01, df.t_surface[k], depth_m=0.12, meteo=store, with_bells3=True)
        assert both.t_layer[k] == pytest.approx(one.value, abs=1e-9) and both.a_sw[k] == pytest.approx(one.a_sw, abs=1e-9)
        assert both.bells3_c[k] == pytest.approx(one.bells3, abs=1e-9)
    only_first = run_survey(df.iloc[:1], store, PARAMS)
    assert only_first.t_layer.iloc[0] == pytest.approx(both.t_layer.iloc[0], abs=1e-9)         # wynik nie zalezy od pozniejszych chwil doby
    assert {"t_layer", "t_layer_uncal", "u95", "a_sw", "ts_sim", "ir_masa", "calib_flag", "qc_flags", "grid_lat", "grid_lon", "sw_ma6"} <= set(both)
    assert (both.u95 > 2.2).all() and (both.grid_lat == 52.25).all()


def test_run_survey_without_meteo_gives_nan_and_flags(tmp_path):
    store = MeteoStore(tmp_path / "none", offline=True)
    res = run_survey(_survey([["2025-07-10 12:00:00", 52.26, 21.01, 30.0, 20.0]]), store, PARAMS)
    assert np.isnan(res.t_layer.iloc[0]) and res.calib_flag.iloc[0] == "nosim"
    assert res.qc_flags.iloc[0] & LayerFlag.METEO_GAP and res.qc_flags.iloc[0] & LayerFlag.CALIB_NOSIM


# ------------------------------------------------------------------ konfiguracja i CLI

def _cfg_dict(tmp_path):
    return {"input": {"survey_csv": str(tmp_path / "s.csv")}, "meteo": {"cache_dir": str(tmp_path / "cache"), "offline": True},
            "output": {"dir": str(tmp_path / "out")}}


def test_config_validation(tmp_path):
    cfg = build_n2_config(_cfg_dict(tmp_path))
    assert effective_depth_cm(cfg) == 12.0
    d = _cfg_dict(tmp_path)
    d["model"] = {"thickness_cm": 24}
    assert effective_depth_cm(build_n2_config(d)) == 12.0
    for patch, key in [({"model": {"calibration": "x"}}, "calibration"), ({"model": {"depth_cm": 70}}, "gleboko"),
                       ({"meteo": {"cache_dir": None}}, "cache_dir"), ({"meteo": {"history_days": 20}}, "history_days"),
                       ({"qc": {"season_months": [13]}}, "season"), ({"input": {"time_basis": "utc"}}, "time_basis"),
                       ({"nieznany": 1}, "nieznane")]:
        bad = _cfg_dict(tmp_path)
        for k, v in patch.items():
            if isinstance(v, dict):
                bad.setdefault(k, {}).update(v)
            else:
                bad[k] = v
        with pytest.raises(ConfigError):
            build_n2_config(bad)
    with pytest.raises(ConfigError):
        build_n2_config({"meteo": {"cache_dir": "x"}})                                   # brak survey_csv


def test_example_config_parses():
    from pathlib import Path
    cfg = load_n2_config(Path(__file__).resolve().parents[2] / "configs" / "n2_example.yaml")
    assert cfg.model.calibration == "single_shot_ir_mass" and cfg.meteo.history_days == 35


def test_cli_end_to_end_offline(tmp_path, om_summer):
    import yaml
    from tsdfwd_tools.cli.main import main
    write_cache(tmp_path / "cache", om_summer)
    pd.DataFrame({"measured_at_local": ["2025-07-10 09:15:00", "2025-07-10 13:40:00", "2025-07-10 13:41:00"],
                  "latitude": [52.26, 52.26, np.nan], "longitude": [21.01, 21.01, 21.01], "t_surface": [28.0, 44.0, 40.0],
                  "t_air": [20.0, 24.0, 24.0], "chainage_m": [0, 10, 20]}).to_csv(tmp_path / "s.csv", index=False)
    d = _cfg_dict(tmp_path)
    d["input"]["passthrough"] = ["chainage_m"]
    d["comparators"] = {"bells3": True}
    cfg_path = tmp_path / "n2.yaml"
    cfg_path.write_text(yaml.safe_dump(d), encoding="utf-8")
    assert main(["layer_temp", "--config", str(cfg_path), "--dry-run"]) == 0
    assert not (tmp_path / "out").exists()
    assert main(["n2", "--config", str(cfg_path)]) == 0
    out = pd.read_csv(tmp_path / "out" / "layer_temp.csv")
    assert len(out) == 3 and out.t_layer.notna().sum() == 2 and out.chainage_m.tolist() == [0, 10, 20]
    assert {"id", "depth_cm", "t12_c", "flags_text", "bells3_c", "t_layer_uncal"} <= set(out)
    assert out.t12_c.equals(out.t_layer) and "METEO_GAP" in out.flags_text.iloc[2]
    meta = json.loads((tmp_path / "out" / "layer_temp_meta.json").read_text(encoding="utf-8"))
    assert meta["params"]["hash_sha256"] == EXPECTED_BUILTIN_HASH and meta["meteo"]["n_requests_made"] == 0
    assert "2,73" in meta["accuracy_note"]
    assert main(["layer_temp", "--config", str(cfg_path)]) == 1                         # plik istnieje, bez overwrite
    assert main(["layer_temp", "--config", str(cfg_path), "--out-dir", str(tmp_path / "out2"), "--strict"]) == 2   # NaN -> kod 2
