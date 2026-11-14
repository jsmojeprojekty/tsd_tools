"""Mediany w oknie wzdluz przejazdu (+-5 m, dopuszczalnie 10 m) i agregacja do 50/100 m.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a_autc_1b.py (window_medians: |s - s_punkt| <= half, przedzial domkniety),
e2b2_values.py (mediana CALEK w oknie, nie calka z mediany; MIN_WINDOW_N), e1_sref.py (biny = floor(s/10 m)), stan c67f7fe /
2026-10-19. GoF >= 0,5 jest ATRYBUTEM okna (udzial i mediana), nie filtrem wiersza (raport 6.2). Wspolrzedna: pikietaz pliku
(chainage_m) albo wspolrzedna korytarza, gdy dostarczona (kolumna `s_corridor_m`)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .constants import GOF_MIN


def _stats(sub: pd.DataFrame, value_cols, d0_col: str, gof_col: str, gof_min: float, min_rows: int) -> dict:
    d0 = sub[d0_col].to_numpy(float)
    n_valid = int((np.isfinite(d0) & (d0 > 0)).sum())
    gof = sub[gof_col].to_numpy(float)
    gfin = np.isfinite(gof)
    row = {"n_rows": int(len(sub)), "n_valid_d0": n_valid,
           "gof_share_ge05": float(np.mean(gof[gfin] >= gof_min)) if gfin.any() else float("nan"),
           "gof_median": float(np.nanmedian(gof)) if gfin.any() else float("nan")}
    ok = n_valid >= min_rows
    for c in value_cols:
        v = sub[c].to_numpy(float)
        row[c] = float(np.nanmedian(v)) if ok and np.isfinite(v).any() else float("nan")
    row["window_ok"] = bool(ok)
    return row


def window_medians(df: pd.DataFrame, centers, half_m: float, value_cols, pos_col: str = "chainage_m",
                   d0_col: str = "d0_20", gof_col: str = "gof", gof_min: float = GOF_MIN, min_rows: int = 3) -> pd.DataFrame:
    """Dla kazdego srodka okna: mediany kolumn `value_cols` z wierszy |pos - srodek| <= half_m (domkniete), liczba wierszy,
    liczba wierszy z waznym d0, udzial GoF >= gof_min i mediana GoF. Mediany puste (NaN), gdy waznych d0 < min_rows."""
    pos = df[pos_col].to_numpy(float)
    order = np.argsort(pos, kind="stable")
    d = df.iloc[order].reset_index(drop=True)
    pos = d[pos_col].to_numpy(float)
    rows = []
    for c in np.asarray(centers, float):
        lo = np.searchsorted(pos, c - half_m, side="left")
        hi = np.searchsorted(pos, c + half_m, side="right")
        row = {"center_m": float(c)}
        row.update(_stats(d.iloc[lo:hi], value_cols, d0_col, gof_col, gof_min, min_rows))
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_bins(df: pd.DataFrame, step_m: float, value_cols, pos_col: str = "chainage_m", d0_col: str = "d0_20",
                   gof_col: str = "gof", gof_min: float = GOF_MIN, min_rows: int = 3) -> pd.DataFrame:
    """Agregacja do przedzialow [k*step, (k+1)*step): bin = floor(pos/step); mediany jak w oknie."""
    pos = df[pos_col].to_numpy(float)
    ok = np.isfinite(pos)
    d = df[ok]
    bin_id = np.floor(d[pos_col].to_numpy(float) / step_m).astype(int)
    rows = []
    for b in np.unique(bin_id):
        sub = d[bin_id == b]
        row = {"bin_id": int(b), "s_from_m": float(b * step_m), "s_to_m": float((b + 1) * step_m)}
        row.update(_stats(sub, value_cols, d0_col, gof_col, gof_min, min_rows))
        rows.append(row)
    return pd.DataFrame(rows)
