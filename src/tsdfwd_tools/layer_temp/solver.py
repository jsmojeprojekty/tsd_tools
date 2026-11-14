"""Solver 1-D przewodnictwa ciepla z bilansem energii na powierzchni (siatka 1 cm, 0-50 cm, krok 10 min).

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\energy_balance_bc.py (simulate_eb: schemat niejawny, linearyzowane promieniowanie
wlasne), stan 2026-11-13. Test tozsamosci: tests/regression/test_n2_reference.py; testy fizyczne: tests/unit/test_n2_units.py.

Wezel 0 = powierzchnia (polowka komorki: pojemnosc cieplna), wezel NZ-1 = 50 cm (warunek Dirichleta z modelu dolnego BC).
Bilans powierzchni: a_sw*SW + eps*LW_dol + h*T_pow_powietrza = eps*sigma*Ts^4 + h*Ts + przewodzenie; h = h0 + h1*wiatr."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import solve_banded

from .constants import DT_S, DZ_M, EPS_SURF, KELVIN, NZ, SIGMA, SPINUP_STEPS
from .params import FrozenParams


def simulate_eb(sub: pd.DataFrame, bottom: pd.Series, params: FrozenParams, a_sw: float, spinup: int = SPINUP_STEPS) -> np.ndarray:
    """Macierz T[nt, NZ] w C dla ramki forsowania `sub` (10 min) i dolnego BC `bottom`; pierwsze `spinup` wierszy = NaN.
    Gdy ktorekolwiek wejscie jest nieskonczone, zwraca same NaN (flaga METEO_GAP/CALIB_NOSIM wyzej)."""
    n = len(sub)
    alpha = params.alpha
    eb = params.eb
    r = alpha * DT_S / DZ_M ** 2
    kc = alpha * eb["c_vol"]
    cap = eb["c_vol"] * DZ_M / (2 * DT_S)
    ab0 = np.zeros((3, NZ))
    ab0[0, 2:] = -r
    ab0[1, 1:-1] = 1 + 2 * r
    ab0[2, :-2] = -r
    ab0[1, -1] = 1.0
    sw = float(a_sw) * sub.swr.to_numpy(float)
    ta = sub.temperature_2m.to_numpy(float) + KELVIN
    ld = eb["svf"] * sub.ld.to_numpy(float) + (1 - eb["svf"]) * SIGMA * ta ** 4
    h = eb["h0"] + eb["h1"] * sub.wind_speed_10m.to_numpy(float)
    b = bottom.to_numpy(float) + KELVIN
    out = np.full((n, NZ), np.nan)
    if n <= spinup or not all(np.isfinite(x).all() for x in (sw, ta, ld, h, b)):
        return out
    z = np.linspace(0.0, 0.5, NZ)
    T = np.empty((n, NZ))
    T[0] = (ta[0] - KELVIN) + ((b[0] - KELVIN) - (ta[0] - KELVIN)) * z / 0.5 + KELVIN
    ab = ab0.copy()
    for i in range(1, n):
        ts = T[i - 1, 0]
        lw = 4 * EPS_SURF * SIGMA * ts ** 3
        ab[1, 0] = cap + lw + h[i] + kc / DZ_M
        ab[0, 1] = -kc / DZ_M
        rhs = T[i - 1].copy()
        rhs[0] = cap * ts + sw[i] + EPS_SURF * ld[i] + 3 * EPS_SURF * SIGMA * ts ** 4 + h[i] * ta[i]
        rhs[-1] = b[i]
        T[i] = solve_banded((1, 1), ab, rhs, check_finite=False)
    out[spinup:] = T[spinup:] - KELVIN
    return out
