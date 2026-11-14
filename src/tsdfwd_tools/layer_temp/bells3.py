"""BELLS3 (FHWA-RD-98-085, rownanie 5) - komparator opcjonalny. Tylko wspolczynniki oryginalne; BELLS3_BT i BELLS3_O nie sa uzywane.

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\baselines_e3.py (BELLS3_COEF, sin18, prev_day_air_mean, bells3_predict) oraz
z14lite_validate.py (bells3_from_parts), stan 2026-11-13. Test tozsamosci: tests/regression/test_n2_reference.py (T-N2-04)."""

from __future__ import annotations

import numpy as np
import pandas as pd

BELLS3_COEF = {"b0": 0.95, "b1": 0.892, "b2": -0.448, "b3": 0.621, "b4": 1.83, "b5": 0.042}


def sin18(hours_dec, phase: float, window_start: float):
    """Sinus BELLS w cyklu 18 h z oknem waznosci i saturacja -1 poza nim (window_start: 11,0 dla -15,5; 9,0 dla -13,5)."""
    shape = np.shape(hours_dec)
    h = np.atleast_1d(np.asarray(hours_dec, dtype=float)).copy()
    wrap_end = window_start - 6.0
    h[h < wrap_end] += 24.0
    out = np.sin(2.0 * np.pi * (h - phase) / 18.0)
    out[(h >= wrap_end) & (h < window_start)] = -1.0
    return out.reshape(shape)


def prev_day_air_mean(temp_2m: pd.Series) -> pd.Series:
    """T(1-day): (min+max)/2 temperatury powietrza dnia poprzedniego (seria 10-minutowa), przypisana do kazdego wiersza."""
    daily = temp_2m.groupby(temp_2m.index.date).agg(["min", "max"])
    mean = (daily["min"] + daily["max"]) / 2.0
    mean.index = pd.to_datetime(mean.index)
    prev = mean.shift(1, freq="D")
    return pd.Series(temp_2m.index.normalize().map(prev), index=temp_2m.index)


def bells3(ir, t1d, hours_dec, depth_mm: float = 120.0, coef=BELLS3_COEF):
    """Temperatura warstwy wg BELLS3 [C] dla odczytu pirometru `ir` [C], sredniej T(1-day), godziny dziesietnej i glebokosci [mm]."""
    s155 = sin18(hours_dec, 15.5, 11.0)
    s135 = sin18(hours_dec, 13.5, 9.0)
    logd = np.log10(depth_mm) - 1.25
    return (coef["b0"] + coef["b1"] * ir + logd * (coef["b2"] * ir + coef["b3"] * t1d + coef["b4"] * s155)
            + coef["b5"] * ir * s135)
