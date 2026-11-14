"""Filtr Hampela na d0 z odrzutem calej czaszy.

zrodlo: C:\\WORK\\DOKTORAT\\tsd_2_xml\\tsd_pipeline.py (_hampel_col, smooth_bowl; WIN = 21, HAMPEL_K = 3,0), stan 2026-07-01.
Jedna, jawnie zdefiniowana implementacja (w projekcie bazy istnieje druga, przyblizona — e2bR9_lustro_data — NIE uzywana):
mediana kroczaca okna (centrowana, min_periods = 1), MAD PRAWDZIWY okna (mediana |x - mediana okna|), prog = k * 1,4826 * MAD,
outlier = |x - mediana| > prog ORAZ prog > 0. Okno podawane w metrach (przeliczane na wiersze wg kroku pikietazu): 10 m przy
kroku 1 m = 21 wierszy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import HAMPEL_K, MAD_SCALE


def window_rows(window_m: float, step_m: float) -> int:
    """Liczba wierszy okna (nieparzysta) dla szerokosci +-window_m: 2*round(window_m/step)+1."""
    return 2 * int(round(window_m / step_m)) + 1


def hampel_outliers(values, rows: int = 21, k: float = HAMPEL_K) -> np.ndarray:
    """Maska outlierow (True) dla szeregu `values` (NaN nigdy outlierem)."""
    s = pd.Series(np.asarray(values, float))
    med = s.rolling(rows, center=True, min_periods=1).median()
    mad = s.rolling(rows, center=True, min_periods=1).apply(
        lambda w: np.nanmedian(np.abs(w - np.nanmedian(w))), raw=True)
    thr = k * MAD_SCALE * mad
    out = (np.abs(s - med) > thr) & (thr > 0) & s.notna()
    return out.to_numpy(dtype=bool)
