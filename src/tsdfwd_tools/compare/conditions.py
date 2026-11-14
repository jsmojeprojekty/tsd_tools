"""Tabela warunkow zgodnosci TSD-FWD: odstep czasu, udzial GoF, zmiennosc D0 odcinka, aparat x okres kalibracji TSD,
jakosc polozenia FWD oraz warstwa przeciecia (dt 0-1 d, GoF >= 0,8, najwyzszy tercyl CV D0).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2bR9_lustro_warunki.py (stan c67f7fe / 2026-11-06). Zmiany wzgledem zrodla:
(a) ujemne dt NIE sa gubione — osobny przedzial '<0' (w zrodle 251 par z ujemnym dt wypadalo z tabeli);
(b) grupowanie aparat x okres kalibracji (`calib_interval`) zamiast roku TSD (`tsd_year` pozostaje mozliwe przez group_by);
(c) CV D0 odcinka liczone domyslnie na wartosciach par (jak w zrodle, odtwarza raport), opcja `cv_unit: stations` — na
    unikalnych stacjach FWD (bez powtorzen przy wielokrotnym parowaniu tej samej stacji).
Miara w kazdej warstwie: korelacja Pearsona logarytmow (r) pary FWD-TSD po korekcie do 20 C, n >= 10."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

MIN_N_LAYER = 10
DT_BINS = (("<0", None), ("0-1", None), ("2-30", None), (">30", None))


def r_of(fwd, tsd, idx=None, min_n: int = MIN_N_LAYER):
    f = np.asarray(fwd, float)
    t = np.asarray(tsd, float)
    if idx is not None:
        f, t = f[idx], t[idx]
    ok = np.isfinite(f) & np.isfinite(t) & (f > 0) & (t > 0)
    n = int(ok.sum())
    if n < min_n:
        return float("nan"), n
    try:
        return float(pearsonr(np.log(f[ok]), np.log(t[ok]))[0]), n
    except Exception:
        return float("nan"), n


def _num(series) -> np.ndarray:
    return pd.to_numeric(series, errors="coerce").to_numpy(float)


def dt_masks(dt_days) -> dict:
    """Przedzialy odstepu czasu [dni]: '<0' (ujemny), '0-1', '2-30' (czyli (1, 30]), '>30'."""
    dt = np.asarray(dt_days, float)
    fin = np.isfinite(dt)
    return {
        "<0": fin & (dt < 0),
        "0-1": fin & (dt >= 0) & (dt <= 1),
        "2-30": fin & (dt > 1) & (dt <= 30),
        ">30": fin & (dt > 30),
    }


def cv_by_corridor(fwd_raw, corridor, station=None, unit: str = "pairs") -> np.ndarray:
    """CV(D0 FWD) odcinka (korytarza) przypisany kazdej parze; NaN gdy < 3 skonczone wartosci. unit 'pairs': wszystkie
    wartosci par (jak w zrodle); 'stations': jedna wartosc na unikalna stacje FWD w odcinku."""
    fwd_raw = np.asarray(fwd_raw, float)
    corridor = np.asarray(corridor, object)
    vals = defaultdict(list)
    if unit == "stations":
        if station is None:
            raise ValueError("cv_unit: stations wymaga kolumny stacji FWD")
        seen = set()
        for c, s, v in zip(corridor, np.asarray(station, object), fwd_raw):
            if (c, s) in seen:
                continue
            seen.add((c, s))
            vals[c].append(v)
    else:
        for c, v in zip(corridor, fwd_raw):
            vals[c].append(v)
    cv = {}
    for c, lst in vals.items():
        v = np.array([x for x in lst if math.isfinite(x)])
        cv[c] = float(np.std(v, ddof=1) / np.mean(v)) if len(v) >= 3 and np.mean(v) != 0 else float("nan")
    return np.array([cv.get(c, float("nan")) for c in corridor], float)


def conditions_table(fwd_after, tsd_after, fwd_raw, meta: pd.DataFrame, group_by=("device", "calib_interval"),
                     cv_unit: str = "pairs", dt_col: str = "dt_days", gof_col: str = "gof_share",
                     corridor_col: str = "corridor", station_col: str = "station", era_col: str = "era",
                     fwd_date_col: str = "fwd_date", sigma_col: str = "sigma_long_fwd",
                     receiver_cutoff: str | None = None, min_n_group: int = MIN_N_LAYER) -> pd.DataFrame:
    """Zwraca tabele: layer_group, layer_value, n_candidates, r, n (+ median_sigma_long dla jakosci polozenia).
    meta: DataFrame o tej samej dlugosci co pary (kolumny wg nazw; brakujace warstwy pomijane)."""
    rows = []

    def add(group, value, idx, extra=None):
        r, n = r_of(fwd_after, tsd_after, idx)
        row = {"layer_group": group, "layer_value": value, "n_candidates": int(len(idx)), "r": r, "n": n}
        row.update(extra or {})
        rows.append(row)

    have = set(meta.columns)
    # --- odstep czasu ---
    if dt_col in have:
        for label, mask in dt_masks(_num(meta[dt_col])).items():
            add("dt_days", label, np.where(mask)[0])
    # --- udzial GoF >= 0,5 w oknie ---
    gof = _num(meta[gof_col]) if gof_col in have else None
    if gof is not None:
        for lo, hi, label in ((0.8, 1.01, ">=0.8"), (0.5, 0.8, "0.5-0.8"), (-0.01, 0.5, "<0.5")):
            add("gof_share_w5", label, np.where(np.isfinite(gof) & (gof >= lo) & (gof < hi))[0])
    # --- zmiennosc D0 FWD na odcinku, tercyle ---
    high_cv = set()
    cv = None
    if corridor_col in have:
        st = meta[station_col].to_numpy(object) if station_col in have else None
        cv = cv_by_corridor(fwd_raw, meta[corridor_col].to_numpy(object), st, cv_unit)
        finite = cv[np.isfinite(cv)]
        if len(finite) >= 3:
            t1, t2 = np.percentile(finite, [100.0 / 3, 200.0 / 3])
            for lo, hi, label in ((-1, t1, "niska (T1)"), (t1, t2, "srednia (T2)"), (t2, 10, "wysoka (T3)")):
                add("cv_d0_corridor_tercile", label, np.where(np.isfinite(cv) & (cv > lo) & (cv <= hi))[0],
                    {"tercile_bounds": f"{t1:.4f}/{t2:.4f}"})
            high_cv = set(np.where(np.isfinite(cv) & (cv > t2))[0].tolist())
    # --- jakosc polozenia FWD (aparat HWD / stary odbiornik przed i po wymianie) ---
    if receiver_cutoff and era_col in have and fwd_date_col in have:
        era = meta[era_col].to_numpy(object)
        date = meta[fwd_date_col].astype(str).str[:10].to_numpy(object)
        cat = np.where(era == "hwd", "HWD", np.where(date >= receiver_cutoff, f"stary_od_{receiver_cutoff}",
                                                       f"stary_przed_{receiver_cutoff}"))
        sigma = _num(meta[sigma_col]) if sigma_col in have else np.full(len(meta), np.nan)
        for c in ("HWD", f"stary_przed_{receiver_cutoff}", f"stary_od_{receiver_cutoff}"):
            idx = np.where(cat == c)[0]
            sig = sigma[idx][np.isfinite(sigma[idx])]
            add("fwd_location_quality", c, idx, {"median_sigma_long_fwd": float(np.median(sig)) if len(sig) else float("nan")})
    # --- aparat x okres kalibracji (lub inne kolumny) ---
    cols = [c for c in group_by if c in have]
    if len(cols) == len(group_by) and cols:
        keys = meta[cols].astype(str).agg("|".join, axis=1).to_numpy(object)
        for key in sorted(set(keys.tolist())):
            idx = np.where(keys == key)[0]
            if len(idx) >= min_n_group:
                add("x".join(cols), key, idx)
    # --- przeciecie: dt 0-1, GoF >= 0,8, najwyzszy tercyl CV ---
    if dt_col in have and gof is not None and high_cv:
        i_dt = set(np.where(dt_masks(_num(meta[dt_col]))["0-1"])[0].tolist())
        i_gof = set(np.where(np.isfinite(gof) & (gof >= 0.8))[0].tolist())
        inter = np.array(sorted(i_dt & i_gof & high_cv), dtype=int)
        add("intersection", "dt0-1_gof>=0.8_cv_T3", inter)
    return pd.DataFrame(rows)
