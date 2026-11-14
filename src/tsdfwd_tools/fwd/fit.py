"""Opcjonalny modul dopasowania wspolczynnikow korekty temperaturowej z wlasnych danych (wizyty punkt x miesiac).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a2b_beta.py (_prep_groups, qp_fit_nd, bootstrap_draws),
e2a3_beta.py (fit_k_profile), e2a3i_final.py (get_data, beta_with_ci, run_k_profile),
e2a3e_range.py (seed_for); stan c67f7fe / 2026-10-13..2026-10-26. Zmiany: bez zapisu do baz, wejscie jako DataFrame.

Model (raport PW.S-1063, 5.1): E[D] = exp(a_g + beta*(T - 20)), efekt staly grupy (punkt x miesiac), funkcja wiazaca log
na sredniej (quasi-Poisson), rownanie wynikowe X'(y - mu) = 0; postac liniowa (krajowa): D = a_g / (1 + k*(20 - T)) + eps,
a_g zamkniete WLS, k z minimalizacji RSS. beta = k w temperaturze odniesienia. Wizyty 5 <= T < 30 C.
Niepewnosc: bootstrap blokowy po dniach (cale dni losowane ze zwracaniem), refit w kazdej replice, przedzialy percentylowe.
Wspolczynniki dopasowane na danych uzytkownika nie zastepuja zestawu raportu — to narzedzie pomocnicze/kontrolne."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar, root

from ..common.stats_basic import seed_for

T_REF_C = 20.0
K_BOUNDS = (-0.08, 0.08)
FIT_RANGE_C = (5.0, 30.0)
MIN_N_FIT = 30


def _prep_groups(y, groups):
    """Filtruje do grup z suma y > 0; zwraca maske, indeks grupy (po filtrze) i sumy grup."""
    _, inv = np.unique(groups, return_inverse=True)
    s_g = np.bincount(inv, weights=y, minlength=int(inv.max()) + 1 if len(inv) else 0)
    keep = (s_g > 0)[inv]
    inv_f = inv[keep]
    _, inv2 = np.unique(inv_f, return_inverse=True)
    s_g2 = np.bincount(inv2, weights=y[keep])
    return keep, inv2, s_g2


def fit_beta(temp_c, y, groups, t_ref: float = T_REF_C):
    """Wspolczynnik beta [1/C] (log-link, efekt staly grupy). Zwraca (beta, n_uzytych, zbieznosc)."""
    x = (np.asarray(temp_c, float) - t_ref).reshape(-1, 1)
    y = np.asarray(y, float)
    keep, inv2, s_g2 = _prep_groups(y, np.asarray(groups))
    x2, y2 = x[keep], y[keep]
    if len(y2) < 20 or len(s_g2) < 2:
        return float("nan"), int(len(y2)), False

    def score(b):
        w = np.exp(x2 @ b)
        w_g = np.bincount(inv2, weights=w)
        mu = s_g2[inv2] / w_g[inv2] * w
        return x2.T @ (y2 - mu)

    try:
        res = root(score, x0=np.zeros(1), method="hybr", tol=1e-10)
        return float(res.x[0]), int(len(y2)), bool(res.success)
    except Exception:
        return float("nan"), int(len(y2)), False


def fit_k(temp_c, y, groups, k_bounds=K_BOUNDS, t_ref: float = T_REF_C):
    """Wspolczynnik k [1/C] postaci liniowej D = a_g / (1 + k*(T_ref - T)). Zwraca (k, zbieznosc)."""
    t = np.asarray(temp_c, float)
    d = np.asarray(y, float)
    _, inv = np.unique(np.asarray(groups), return_inverse=True)

    def rss(k):
        w = 1.0 / (1.0 + k * (t_ref - t))
        if np.any(w <= 0) or not np.all(np.isfinite(w)):
            return 1e18
        num = np.bincount(inv, weights=d * w)
        den = np.bincount(inv, weights=w * w)
        a_p = num / np.where(den > 0, den, 1.0)
        return float(np.sum((d - a_p[inv] * w) ** 2))

    res = minimize_scalar(rss, bounds=k_bounds, method="bounded", options=dict(xatol=1e-5))
    return float(res.x), bool(res.success)


def bootstrap_draws(universe, n_boot: int, seed: int):
    rng = np.random.default_rng(seed)
    return [rng.choice(universe, size=len(universe), replace=True) for _ in range(n_boot)]


def fit_indicator(temp_c, y, groups, day, n_boot: int = 500, seed_tag: str = "kprof",
                  k_bounds=K_BOUNDS, min_n: int = MIN_N_FIT) -> dict:
    """beta [%/C] i k z przedzialami percentylowymi 95 % (bootstrap blokowy po dniach). Zwraca slownik jak
    e2a3_final_k_profile.csv: beta_pct, beta_lo, beta_hi, k_guide, k_lo, k_hi, n, note."""
    t = np.asarray(temp_c, float)
    y = np.asarray(y, float)
    groups = np.asarray(groups)
    day = np.asarray(day)
    n = len(t)
    nan = float("nan")
    empty = dict(beta_pct=nan, beta_lo=nan, beta_hi=nan, k_guide=nan, k_lo=nan, k_hi=nan, n=n)
    if n < min_n:
        return {**empty, "note": "za malo danych"}
    b, _, ok = fit_beta(t, y, groups)
    k_hat, ok_k = fit_k(t, y, groups, k_bounds)
    if not ok:
        return {**empty, "k_guide": k_hat if ok_k else nan, "note": "model log-link nie zbiegl"}
    days_u = sorted(set(day.tolist()))
    draws = bootstrap_draws(np.array(days_u), n_boot, seed_for(seed_tag, "boot")) if len(days_u) >= 5 else []
    idx_by_day = {d: np.where(day == d)[0] for d in days_u}
    betas, ks = [], []
    for drawn in draws:
        idx = np.concatenate([idx_by_day.get(d, np.array([], dtype=int)) for d in drawn]) if len(drawn) \
            else np.array([], dtype=int)
        if len(idx) < min_n:
            continue
        try:
            br, _, okr = fit_beta(t[idx], y[idx], groups[idx])
            if okr:
                betas.append(br)
            kr, okkr = fit_k(t[idx], y[idx], groups[idx], k_bounds)
            if okkr:
                ks.append(kr)
        except Exception:
            continue
    thr = max(10, n_boot // 4)
    blo, bhi = np.percentile(betas, [2.5, 97.5]) if len(betas) > thr else (nan, nan)
    klo, khi = np.percentile(ks, [2.5, 97.5]) if len(ks) > thr else (nan, nan)
    return dict(beta_pct=b * 100.0, beta_lo=float(blo) * 100.0 if math.isfinite(blo) else nan,
                beta_hi=float(bhi) * 100.0 if math.isfinite(bhi) else nan,
                k_guide=k_hat if ok_k else nan, k_lo=float(klo), k_hi=float(khi), n=n,
                note="" if ok_k else "postac liniowa nie zbiegla")


def group_keys(point, date) -> np.ndarray:
    """Etykieta grupy punkt x miesiac ('punkt|MM'); date: napisy 'RRRR-MM-DD' lub daty."""
    month = pd.to_datetime(pd.Series(date)).dt.strftime("%m").to_numpy()
    return np.array([f"{p}|{m}" for p, m in zip(point, month)])


def fit_table(visits: pd.DataFrame, indicators, point_col: str, date_col: str, t_col: str,
              t_range_c=FIT_RANGE_C, n_boot: int = 500, scope_label: str = "lacznie",
              k_bounds=K_BOUNDS, min_n: int = MIN_N_FIT) -> pd.DataFrame:
    """Dopasowanie dla listy wskaznikow (kolumny wizyt, wielkosc liter dowolna). Wizyty 5 <= T < 30 C (domyslnie).
    Zwraca tabele w formacie e2a3_final_k_profile.csv (scope, indicator, beta_pct, beta_lo, beta_hi, k_guide, k_lo,
    k_hi, n, note). Seed bootstrapu: seed_for('kprof:<scope>:<wskaznik>', 'boot') jak w zrodle."""
    cols = {c.lower(): c for c in visits.columns}
    for need in (point_col, date_col, t_col):
        if need not in visits.columns:
            raise ValueError(f"brak kolumny {need!r} w danych wizyt (dostepne: {list(visits.columns)})")
    rows = []
    for ind in indicators:
        col = cols.get(str(ind).lower())
        if col is None:
            raise ValueError(f"brak kolumny wskaznika {ind!r} w danych wizyt")
        sub = visits[[point_col, date_col, t_col, col]].copy()
        sub[t_col] = pd.to_numeric(sub[t_col], errors="coerce")
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
        sub = sub[np.isfinite(sub[t_col]) & np.isfinite(sub[col])]
        sub = sub[(sub[t_col] >= t_range_c[0]) & (sub[t_col] < t_range_c[1])]
        t = sub[t_col].to_numpy(float)
        y = sub[col].to_numpy(float)
        key = group_keys(sub[point_col].to_numpy(), sub[date_col].to_numpy())
        day = pd.to_datetime(sub[date_col]).dt.strftime("%Y-%m-%d").to_numpy()
        res = fit_indicator(t, y, key, day, n_boot, f"kprof:{scope_label}:{ind}", k_bounds, min_n)
        rows.append(dict(scope=scope_label, indicator=ind, **res))
    return pd.DataFrame(rows)
