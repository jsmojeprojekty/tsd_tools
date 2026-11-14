"""Korekta temperaturowa d0 TSD (B_1510off) do 20 C: wykladnicza, beta D0 = 1,60 %/C, zakres T12 5-30 C.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\z15_temp_correction.py / e2bR9_lustro_data.py (correct_pair, BETA_D0_PCT), stan c67f7fe /
2026-11-07. Zasady (raport 6.1, 7.3 p. 2-3): T = temperatura warstwy na 12 cm w chwili przejazdu (z modelu N2), NIGDY odczyt
pirometru (Temp Road) ani temperatura powierzchni; ta sama beta co D0 FWD; poza zakresem 5-30 C wyniki oznaczane. Dotyczy
WYLACZNIE d0 przeliczonego bez czujnika 1,51 m (dla d0 eksportu nominalnego delta-beta = -1,78 %/C — korekta bledna)."""

from __future__ import annotations

import numpy as np

from ..common.coefficients import load_coefficients
from ..common.constants import T_REF_C
from ..common.rules import CorrectionForm, apply_correction
from .flags import TsdFlag

RANGE_C = (5.0, 30.0)


def default_beta_pct() -> float:
    return load_coefficients("e2a3_full").beta("D0") * 100.0


def correct_d0(d0_um, t12_c, beta_pct: float | None = None, range_c=RANGE_C, t_ref: float = T_REF_C):
    """Zwraca (d0_20 [um], maska flag TsdFlag). T12 < dolnej granicy: d0_20 = NaN (korekta bez zastosowania);
    T12 > gornej granicy: korekta wykonana i oznaczona; brak T12: d0_20 = NaN i T_MISSING."""
    d0 = np.asarray(d0_um, float)
    t = np.asarray(t12_c, float)
    beta = (default_beta_pct() if beta_pct is None else beta_pct) / 100.0
    lo, hi = float(range_c[0]), float(range_c[1])
    finite = np.isfinite(t)
    below = finite & (t < lo)
    above = finite & (t > hi)
    flags = np.zeros(len(d0), dtype=np.int64)
    flags[~finite] |= int(TsdFlag.T_MISSING)
    flags[below] |= int(TsdFlag.T_BELOW_5C)
    flags[above] |= int(TsdFlag.T_ABOVE_RANGE)
    use = finite & ~below
    d20 = np.where(use, apply_correction(d0, np.where(use, t, t_ref), CorrectionForm.EXPONENTIAL, beta, t_ref), np.nan)
    return d20, flags


def to_fwd_scale(d0_20, multiplier: float = 1.62):
    """D0_FWD,20 = m * d0_TSD,20 (mnoznik; wazny dla wartosci odcinkowych >= 100 m; domyslnie 1,62 [1,54; 1,68])."""
    return np.asarray(d0_20, float) * multiplier
