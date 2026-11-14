"""Ocena jakosci temperatury FWD (wpis operatora przenoszony na kolejne stacje).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e0_fwd_temp.py (classify_session, placeholder_runs), stan c67f7fe /
2026-10-08. Zmiany: wejscie to DataFrame jednej sesji (czas w sekundach epoki), bez wspolrzednych i bez zapisu do baz;
wiek wpisu liczony w sekundach (bez odleglosci).

Statusy kanalu temperatury: entry_first / entry_change (pomiar: pierwsza niepusta wartosc sesji lub zmiana wartosci),
carried (wartosc bez zmiany), entry_possible (bez zmiany, ale odstep od poprzedniej stacji > max(150 s, 3*P90 odstepow
zwyklych): mozliwy wpis), missing (brak)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.constants import PLACEHOLDER_TEMPS_C, PLACEHOLDER_TOL_C
from ..common.flags import Flag

GAP_FACTOR = 3.0
GAP_MIN_S = 150.0
GAP_QUANTILE = 0.90
MIN_REGULAR_GAPS = 5
TEMP_EPS = 1e-6
PLACEHOLDER_MIN_H = 1.0
PLACEHOLDER_NULL_NEAR = 3


def _differs(a: float, b: float) -> bool:
    return abs(a - b) > TEMP_EPS


def classify_session(values, t_s, gap_factor: float = GAP_FACTOR, gap_min_s: float = GAP_MIN_S,
                     gap_q: float = GAP_QUANTILE, min_regular: int = MIN_REGULAR_GAPS) -> dict:
    """values: temperatura wpisu wg kolejnosci stacji (NaN = brak); t_s: czas w sekundach (NaN = brak).
    Zwraca slownik: status (lista), age_s (wiek wpisu pewnego), gap_threshold_s."""
    n = len(values)
    status = [None] * n
    prev_val = None
    gaps = [np.nan] * n
    for i in range(n):
        if i > 0 and np.isfinite(t_s[i]) and np.isfinite(t_s[i - 1]):
            gaps[i] = t_s[i] - t_s[i - 1]
        v = values[i]
        if not np.isfinite(v):
            status[i] = "missing"
        elif prev_val is None:
            status[i] = "entry_first"
        elif _differs(v, prev_val):
            status[i] = "entry_change"
        else:
            status[i] = "carried"
        if np.isfinite(v):
            prev_val = v
    regular = [g for s, g in zip(status, gaps) if s == "carried" and np.isfinite(g)]
    p90 = float(np.quantile(regular, gap_q)) if len(regular) >= min_regular else None
    thr = max(gap_min_s, gap_factor * p90) if p90 is not None else gap_min_s
    for i in range(n):
        if status[i] == "carried" and np.isfinite(gaps[i]) and gaps[i] > thr:
            status[i] = "entry_possible"
    age = [np.nan] * n
    last_t = None
    for i in range(n):
        if status[i] in ("entry_first", "entry_change"):
            last_t = t_s[i]
        if status[i] != "missing" and last_t is not None and np.isfinite(t_s[i]) and np.isfinite(last_t):
            age[i] = t_s[i] - last_t
    return {"status": status, "age_s": age, "gap_threshold_s": thr}


def placeholder_runs(values, t_s, placeholders=PLACEHOLDER_TEMPS_C, tol: float = PLACEHOLDER_TOL_C,
                     near: int = PLACEHOLDER_NULL_NEAR) -> list:
    """Ciagi stacji z wartoscia zastepcza (NULL-e pominiete, ciag przerywa inna wartosc).
    Zwraca liste (wartosc, i_od, i_do, czas [h], n_null_blisko)."""
    n = len(values)
    out = []
    i = 0
    while i < n:
        v = values[i]
        ph = next((p for p in placeholders if np.isfinite(v) and abs(v - p) <= tol), None)
        if ph is None:
            i += 1
            continue
        j = i
        k = i + 1
        while k < n and (not np.isfinite(values[k]) or abs(values[k] - ph) <= tol):
            if np.isfinite(values[k]):
                j = k
            k += 1
        ts = [t_s[m] for m in range(i, j + 1) if np.isfinite(values[m]) and np.isfinite(t_s[m])]
        dur = (max(ts) - min(ts)) / 3600.0 if len(ts) > 1 else 0.0
        lo, hi = max(0, i - near), min(n - 1, j + near)
        n_null = sum(1 for m in range(lo, hi + 1) if not np.isfinite(values[m]))
        out.append((ph, i, j, dur, n_null))
        i = j + 1
    return out


def assess_temperature(stations: pd.DataFrame, column: str = "asphalt_temp", placeholders=PLACEHOLDER_TEMPS_C,
                       max_age_min: float | None = 60.0) -> pd.DataFrame:
    """Status i flagi temperatury dla kazdej sesji; zwraca DataFrame (indeks jak stations) z kolumnami
    t_status, t_age_min, flag_mask. Wymaga kolumn: session_id, time, <column>."""
    out = pd.DataFrame(index=stations.index, columns=["t_status", "t_age_min", "flag_mask"])
    out["flag_mask"] = 0
    out["t_age_min"] = np.nan
    out["t_status"] = "missing"
    sentinel_col = f"{column}_sentinel"
    for _, grp in stations.groupby("session_id", sort=False):
        grp = grp.sort_values("time", kind="stable")
        values = grp[column].to_numpy(dtype=float)
        t_s = (grp["time"] - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy(dtype=float)
        res = classify_session(values, t_s)
        runs = [r for r in placeholder_runs(values, t_s, placeholders) if r[3] > PLACEHOLDER_MIN_H and r[4] > 0]
        ph_idx = set()
        for _, i0, i1, _, _ in runs:
            ph_idx.update(range(i0, i1 + 1))
        for pos, idx in enumerate(grp.index):
            mask = 0
            st = res["status"][pos]
            if st == "missing":
                mask |= int(Flag.T_MISSING)
            elif st == "carried":
                mask |= int(Flag.T_CARRIED)
            elif st == "entry_possible":
                mask |= int(Flag.T_ENTRY_POSSIBLE)
            if pos in ph_idx and np.isfinite(values[pos]):
                mask |= int(Flag.T_PLACEHOLDER)
            if sentinel_col in grp and bool(grp.iloc[pos][sentinel_col]):
                mask |= int(Flag.T_SENTINEL)
            age = res["age_s"][pos]
            if np.isfinite(age):
                out.at[idx, "t_age_min"] = age / 60.0
                if max_age_min is not None and st in ("carried", "entry_possible") and age / 60.0 > max_age_min:
                    mask |= int(Flag.T_STALE)
            out.at[idx, "t_status"] = st
            out.at[idx, "flag_mask"] = mask
    out["flag_mask"] = out["flag_mask"].astype(np.int64)
    out["t_age_min"] = out["t_age_min"].astype(float)
    return out
