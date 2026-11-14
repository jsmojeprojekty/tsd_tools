"""Wybor zrzutu, normalizacja do obciazenia odniesienia i przypisanie czujnikow (D1..D9 -> D0..D1800).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b2_values.py (load_fwd_values: srednia zrzutow nieosadczych d_i*50/F;
match_geophone_indices, is_standard_layout), stan c67f7fe / 2026-10-19."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..common.constants import (
    GEOPHONES,
    GEOPHONE_OFFSETS_MM,
    LOAD_REF_KN,
    OFFSET_TOL_MM,
    STANDARD_LAYOUT_MM,
)
from ..common.flags import Flag
from .io import D_COLS


def normalize_load(d_um, force_kn, ref_kn: float = LOAD_REF_KN) -> np.ndarray:
    """Ugiecie sprowadzone do sily odniesienia: D * ref / F."""
    return np.asarray(d_um, dtype=float) * ref_kn / np.asarray(force_kn, dtype=float)


def is_standard_layout(x_mm) -> bool:
    return x_mm is not None and all(
        x is not None and abs(x - s) <= OFFSET_TOL_MM for x, s in zip(x_mm, STANDARD_LAYOUT_MM))


def geophone_columns(x_mm, mode: str = "by_x") -> dict:
    """Odwzorowanie nazwa czujnika -> kolumna zrzutu ('d1'..'d9').

    mode 'standard_layout' lub brak polozen w pliku: uklad standardowy (D1..D9 = 0, 200, 300, 450, 600, 900,
    1200, 1500, 1800 mm). mode 'by_x': dopasowanie po polozeniach x1..x9 sesji (tolerancja 1 mm); brak
    dopasowania = czujnik nieobecny (klucz pominiety)."""
    if mode == "standard_layout" or x_mm is None:
        return dict(zip(GEOPHONES, D_COLS))
    out = {}
    for name, target in zip(GEOPHONES, GEOPHONE_OFFSETS_MM):
        for i, x in enumerate(x_mm, 1):
            if x is not None and abs(float(x) - target) <= OFFSET_TOL_MM:
                out[name] = f"d{i}"
                break
    return out


def select_drops(drops: pd.DataFrame, rule: str = "mean_nonseating", ref_kn: float = LOAD_REF_KN) -> pd.DataFrame:
    """Jedna wartosc ugiec na stacje [um, znormalizowane do ref_kn], kolumny d1..d9, force_kn (srednia uzytych
    zrzutow), n_drops, flag_mask. Zrzuty z sila <= 0 i ugiecia <= 0 sa pomijane (jak w zrodle)."""
    rows = []
    for station_id, grp in drops.groupby("station_id", sort=True):
        grp = grp.sort_values("drop_id", kind="stable")
        if rule == "mean_nonseating":
            used = grp[grp["non_seating"] & (grp["force_kn"] > 0)]
        elif rule == "last_nonseating":
            nonseat = grp[grp["non_seating"] & (grp["force_kn"] > 0)]
            used = nonseat.tail(1)
        elif rule == "second_drop":
            second = grp.iloc[1:2]
            used = second[second["non_seating"] & (second["force_kn"] > 0)]
        else:
            raise ValueError(f"nieznana regula zrzutu: {rule!r}")
        row = {"station_id": int(station_id), "n_drops": int(len(used)), "flag_mask": 0}
        if used.empty:
            row.update({c: np.nan for c in D_COLS})
            row["force_kn"] = np.nan
            row["flag_mask"] = int(Flag.NO_NONSEATING_DROP)
        else:
            force = used["force_kn"].to_numpy(dtype=float)
            row["force_kn"] = float(force.mean())
            for col in D_COLS:
                d = used[col].to_numpy(dtype=float)
                ok = np.isfinite(d) & (d > 0)
                row[col] = float((d[ok] * ref_kn / force[ok]).mean()) if ok.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index("station_id")


def to_geophones(norm_d: pd.DataFrame, session_of_station: pd.Series, sessions: dict,
                 mode: str = "by_x") -> pd.DataFrame:
    """Kolumny d1..d9 -> D0..D1800 wg ukladu czujnikow sesji stacji; dodaje kolumne flag_mask (GEOPHONE_MISSING)."""
    out = pd.DataFrame(np.nan, index=norm_d.index, columns=list(GEOPHONES), dtype=float)
    flag = np.zeros(len(norm_d), dtype=np.int64)
    cache = {}
    for pos, (sid, row) in enumerate(norm_d.iterrows()):
        sess = int(session_of_station.get(sid, 1)) if sid in session_of_station.index else 1
        if sess not in cache:
            cache[sess] = geophone_columns((sessions.get(sess) or {}).get("x_mm"), mode)
        mapping = cache[sess]
        for name in GEOPHONES:
            col = mapping.get(name)
            if col is None:
                flag[pos] |= int(Flag.GEOPHONE_MISSING)
            else:
                out.at[sid, name] = row[col]
    out["flag_mask"] = flag
    return out
