"""Podstawowe narzedzia statystyczne wspolne dla narzedzi.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a3e_range.py (seed_for), e2b2_values.py (nmed, mad_robust_sd),
stan c67f7fe / 2026-10-19..2026-10-13."""

from __future__ import annotations

import zlib

import numpy as np


def seed_for(*parts) -> int:
    """Deterministyczny seed z nazw (crc32), zamiast hash() nieprzewidywalnego miedzy procesami."""
    return 1000 + (zlib.crc32("|".join(str(p) for p in parts).encode()) % 80000)


def nmed(x) -> float:
    """Mediana skonczonych wartosci (NaN gdy brak)."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.median(x)) if len(x) else float("nan")


def mad_robust_sd(x) -> float:
    """1,4826 * MAD wokol mediany (skonczone wartosci); NaN gdy mniej niz 2."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return float("nan")
    med = np.median(x)
    return float(1.4826 * np.median(np.abs(x - med)))
