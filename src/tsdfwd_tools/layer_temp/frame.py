"""Ramka forsowania 10-minutowa: interpolacja meteo, promieniowanie dlugofalowe, cechy dolnego warunku brzegowego, korekta IR.

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\energy_balance_bc.py (longwave), operational_bc.py (cechy, dolny BC t50,
korekta IR do 'masy'), z14lite_validate.py (network_frame), stan 2026-11-13. Test tozsamosci: tests/regression/test_n2_reference.py."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import KELVIN, SIGMA, STEP
from .params import FrozenParams

STEPS_PER_DAY = 144


def longwave_down(dew_c, air_c, cloud_pct):
    """Promieniowanie dlugofalowe z nieba [W/m2]: emisyjnosc pogodnego nieba (Brunt, e z punktu rosy) i zachmurzenie."""
    e = 6.112 * np.exp(17.62 * dew_c / (243.12 + dew_c))
    ec = 0.605 + 0.048 * np.sqrt(e)
    cc = cloud_pct / 100.0
    return (cc + (1 - cc) * ec) * SIGMA * (air_c + KELVIN) ** 4


def make_index(day_start: pd.Timestamp, t_end: pd.Timestamp) -> pd.DatetimeIndex:
    """Siatka 10 min od poczatku historii do chwili `t_end` zaokraglonej w gore (jednostka ns - wymagana przez np.interp)."""
    return pd.date_range(pd.Timestamp(day_start), pd.Timestamp(t_end).ceil("10min"), freq=STEP).as_unit("ns")


def build_frame(om: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Meteo godzinowe -> siatka 10 min. Temperatura/punkt rosy/wiatr/zachmurzenie: interpolacja liniowa po czasie;
    promieniowanie krotkofalowe (srednia z poprzedzajacej godziny) przesuniete o -30 min i interpolowane, obciete do >= 0.
    Po ostatniej godzinie danych wartosc jest utrzymywana (flaga TAIL_EXTRAPOLATED ustawiana w predict)."""
    om = om.copy()
    om.index = pd.DatetimeIndex(om.index).as_unit("ns")
    inst = om[["temperature_2m", "dew_point_2m", "wind_speed_10m", "cloud_cover"]]
    i10 = inst.reindex(inst.index.union(index)).interpolate(method="time").reindex(index)
    rad = om["shortwave_radiation"].copy()
    rad.index = rad.index - pd.Timedelta(minutes=30)
    r10 = rad.reindex(rad.index.union(index)).interpolate(method="time").reindex(index).clip(lower=0.0)
    f = i10.assign(swr=r10)
    f["ld"] = longwave_down(f.dew_point_2m, f.temperature_2m, f.cloud_cover)
    doy = index.day_of_year
    f["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    f["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    ta = f["temperature_2m"]
    f["ma7"] = ta.rolling(7 * STEPS_PER_DAY, min_periods=6 * STEPS_PER_DAY).mean()
    f["ma30"] = ta.rolling(30 * STEPS_PER_DAY, min_periods=25 * STEPS_PER_DAY).mean()
    f["sw_ma6"] = f["swr"].rolling(36, min_periods=18).mean()
    if "snow_depth" in om:
        sn = om["snow_depth"]
        f["snow_depth"] = sn.reindex(sn.index.union(index)).interpolate(method="time").reindex(index)
    else:
        f["snow_depth"] = np.nan
    return f


def bottom_t50(f: pd.DataFrame, params: FrozenParams) -> pd.Series:
    """Dolny warunek brzegowy: temperatura na 50 cm z OLS (stala, sezon sin/cos, srednie kroczace 7 i 30 d temperatury powietrza)."""
    b = params.beta50
    return b[0] + b[1] * f.doy_sin + b[2] * f.doy_cos + b[3] * f.ma7 + b[4] * f.ma30


def delta_ir(f: pd.DataFrame, params: FrozenParams) -> pd.Series:
    """Korekta odczytu pirometru do temperatury 'masy' (powierzchnia - zaniżenie/zawyzenie IR wg promieniowania, wiatru, nocy)."""
    b = params.beta_ir
    swr = f.swr / 1000.0
    night = (f.swr < 5.0).astype(float)
    cn = (1 - f.cloud_cover / 100.0) * night
    return b[0] + b[1] * swr + b[2] * swr * f.wind_speed_10m + b[3] * cn + b[4] * cn * f.wind_speed_10m


def at_time(index: pd.DatetimeIndex, values, t) -> float:
    """Interpolacja liniowa serii (indeks ns) w chwili t; NaN poza zakresem waznych wartosci."""
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    if not ok.any():
        return float("nan")
    return float(np.interp(pd.Timestamp(t).as_unit("ns").value, index[ok].asi8, v[ok], left=np.nan, right=np.nan))
