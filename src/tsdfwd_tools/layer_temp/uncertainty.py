"""Niepewnosc temperatury warstwy N2: u95 = 2*RMSE(pora doby) ze zbioru H v2, nie mniej niz dolna granica metody pomiaru.

Uwaga metodyczna: RMSE wg pory pochodzi ze zbioru eksploracyjnego H (n = 549); na niezaleznym zbiorze C blad jest wiekszy
(RMSE 2,73 C). Wartosc u95 jest heurystyka wewnetrzna narzedzia (Q-N2-5), a nie gwarantowanym przedzialem."""

from __future__ import annotations

import numpy as np

from .constants import RMSE_BY_HOUR_BIN, U95_MIN_C


def u95_for_hour(hour_dec: float) -> float:
    """u95 [C] dla godziny lokalnej 0-24 (biny 0-6, 6-12, 12-18, 18-24)."""
    if not np.isfinite(hour_dec):
        return float("nan")
    for (lo, hi), rmse in RMSE_BY_HOUR_BIN.items():
        if lo <= hour_dec < hi:
            return max(2.0 * rmse, U95_MIN_C)
    return max(2.0 * RMSE_BY_HOUR_BIN[(18, 24)], U95_MIN_C)
