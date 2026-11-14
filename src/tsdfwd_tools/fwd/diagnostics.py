"""Diagnostyka bledu normalizacji temperaturowej (test zakresu na wizytach stacji pomiarowych).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a3f_range.py (l20_error, band_mean), stan c67f7fe / 2026-10-13.
Tylko estymator punktowy (bez bootstrapu, CI i werdyktow rownowaznosci — to element badawczy raportu).

Blad: e = 100 * (ln D20 - srednia ln D20 wizyt 15-25 C w tej samej grupie), gdzie ln D20 = ln D + ln f(T);
referencja grupy wymaga co najmniej min_group_ref wizyt 15-25 C. Dla T < 10 C stacje nie maja referencji w tym samym
miesiacu — test pasmowy nie weryfikuje korekty w tym zakresie."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from ..common.rules import CorrectionForm, factor

MIN_GROUP_REF = 2
MIN_N_BAND = 20


def l20_error(T, y, group_key, param, form, min_group_ref: int = MIN_GROUP_REF):
    """Zwraca (e [%], maska waznosci). T [C], y [um] (znormalizowane), group_key: etykieta grupy (punkt x miesiac)."""
    T = np.asarray(T, dtype=float)
    y = np.asarray(y, dtype=float)
    group_key = np.asarray(group_key)
    f_t = factor(T, CorrectionForm.parse(form), param)
    valid = np.isfinite(f_t) & (f_t > 0) & np.isfinite(y) & (y > 0)
    l20 = np.full(len(T), np.nan)
    l20[valid] = np.log(y[valid]) + np.log(f_t[valid])
    maskr = valid & (T >= 15.0) & (T <= 25.0)
    ref_sum, ref_cnt = defaultdict(float), defaultdict(int)
    for g, v in zip(group_key[maskr], l20[maskr]):
        ref_sum[g] += v
        ref_cnt[g] += 1
    ref = {g: ref_sum[g] / ref_cnt[g] for g in ref_sum if ref_cnt[g] >= min_group_ref}
    keep = valid & np.array([g in ref for g in group_key])
    e = np.full(len(T), np.nan)
    idxk = np.where(keep)[0]
    if len(idxk):
        e[idxk] = 100.0 * (l20[idxk] - np.array([ref[group_key[i]] for i in idxk]))
    return e, keep


def band_mean(T, e, keep, lo: float, hi: float, min_n: int = MIN_N_BAND):
    """Sredni blad [%] w pasmie [lo, hi) (hi = inf: bez gornej granicy) i liczba obserwacji; NaN gdy n < min_n."""
    T = np.asarray(T, dtype=float)
    m = ((T >= lo) & (T < hi) if math.isfinite(hi) else (T >= lo)) & np.asarray(keep)
    n = int(m.sum())
    return (float(np.mean(np.asarray(e)[m])) if n >= min_n else float("nan")), n
