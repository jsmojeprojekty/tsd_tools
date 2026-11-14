"""Miary zgodnosci FWD (D0) i TSD (d0): iloraz, CCC Lina, Bland-Altman, Deming, korelacje (takze w obrebie sesji).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b2_agreement.py (ccc_from_logs, bland_altman_log, deming, ols, point_stats,
bootstrap_ci), e2bR9_lustro_warianty.py (session_demeaned_corr), z15_temp_correction.py (robust_extra), stan c67f7fe /
2026-10-19..2026-11-07. Zmiany: bez globalnego loggera i zapisu do baz.

Konwencja Deminga: x = TSD (zmienna z bledem), y = FWD; lambda = Var(blad FWD) / Var(blad TSD) na skali log
(raport 7.2); wariant liniowy z lambda przeskalowana mediana poziomow. Wszystkie miary na parach z dodatnimi
wartosciami po obu stronach."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from scipy.stats import pearsonr, spearmanr

from ..common.stats_basic import mad_robust_sd

BOOT_SEED_CI = 20261019      # domyslny seed bootstrap_ci w zrodle (e2b2_agreement.py)

POINT_KEYS = ("median_ratio", "sd_log_ratio", "pearson_r", "spearman_rho", "ccc", "ba_bias_ratio",
              "ba_loa_lo_ratio", "ba_loa_hi_ratio", "deming_loglog_slope", "deming_loglog_intercept",
              "deming_linear_a", "deming_linear_b", "ols_linear_a", "ols_linear_b")


def valid_pairs(fwd, tsd) -> np.ndarray:
    fwd = np.asarray(fwd, float)
    tsd = np.asarray(tsd, float)
    return np.isfinite(fwd) & np.isfinite(tsd) & (fwd > 0) & (tsd > 0)


def ccc_from_logs(x, y) -> float:
    """Wspolczynnik zgodnosci Lina (Lin 1989) na podanych (juz zlogarytmowanych) wartosciach."""
    if len(x) < 2:
        return float("nan")
    mx, my = np.mean(x), np.mean(y)
    vx, vy = np.var(x), np.var(y)
    sxy = np.mean((x - mx) * (y - my))
    denom = vx + vy + (mx - my) ** 2
    return float(2 * sxy / denom) if denom > 0 else float("nan")


def bland_altman_log(x_fwd_log, y_tsd_log):
    """Obciazenie i granice zgodnosci 95 % roznicy logarytmow (po exp: iloraz). Zwraca (bias, lo, hi, sd)."""
    d = x_fwd_log - y_tsd_log
    bias = float(np.mean(d))
    sd = float(np.std(d, ddof=1)) if len(d) > 1 else float("nan")
    return bias, bias - 1.96 * sd, bias + 1.96 * sd, sd


def deming(x, y, lam: float):
    """Regresja Deminga (Linnet 1993): x = TSD, y = FWD, lam = Var(blad_y)/Var(blad_x). Zwraca (nachylenie, wyraz wolny)."""
    n = len(x)
    if n < 3 or not math.isfinite(lam) or lam <= 0:
        return float("nan"), float("nan")
    mx, my = np.mean(x), np.mean(y)
    sxx = np.sum((x - mx) ** 2)
    syy = np.sum((y - my) ** 2)
    sxy = np.sum((x - mx) * (y - my))
    if sxy == 0:
        return float("nan"), float("nan")
    slope = ((syy - lam * sxx) + math.sqrt((syy - lam * sxx) ** 2 + 4 * lam * sxy ** 2)) / (2 * sxy)
    return float(slope), float(my - slope * mx)


def ols(x, y):
    if len(x) < 3 or np.std(x) == 0:
        return float("nan"), float("nan")
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def point_stats(fwd, tsd, lam_log: float) -> dict:
    """Miary punktowe; fwd, tsd juz przefiltrowane (skonczone, > 0)."""
    fwd = np.asarray(fwd, float)
    tsd = np.asarray(tsd, float)
    n = len(fwd)
    out = {"n": n}
    if n < 3:
        out.update({k: float("nan") for k in POINT_KEYS})
        return out
    lf, lt = np.log(fwd), np.log(tsd)
    logr = lf - lt
    out["median_ratio"] = float(np.exp(np.median(logr)))
    out["sd_log_ratio"] = float(np.std(logr, ddof=1))
    try:
        out["pearson_r"] = float(pearsonr(lf, lt)[0])
    except Exception:
        out["pearson_r"] = float("nan")
    try:
        out["spearman_rho"] = float(spearmanr(fwd, tsd)[0])
    except Exception:
        out["spearman_rho"] = float("nan")
    out["ccc"] = ccc_from_logs(lf, lt)
    bias, lo, hi, _ = bland_altman_log(lf, lt)
    out["ba_bias_ratio"] = float(np.exp(bias))
    out["ba_loa_lo_ratio"] = float(np.exp(lo))
    out["ba_loa_hi_ratio"] = float(np.exp(hi))
    out["deming_loglog_slope"], out["deming_loglog_intercept"] = deming(lt, lf, lam_log)
    med_fwd, med_tsd = float(np.median(fwd)), float(np.median(tsd))
    lam_lin = lam_log * (med_fwd / med_tsd) ** 2 if (math.isfinite(lam_log) and med_tsd > 0) else float("nan")
    out["deming_linear_a"], out["deming_linear_b"] = deming(tsd, fwd, lam_lin)
    out["ols_linear_a"], out["ols_linear_b"] = ols(tsd, fwd)
    return out


def robust_extra(fwd, tsd) -> dict:
    """Miary odporne obok SD: MAD (1,4826) i P90 |log-ilorazu|."""
    logr = np.log(np.asarray(fwd, float)) - np.log(np.asarray(tsd, float))
    return {"mad_log_ratio": mad_robust_sd(logr), "p90_abs_log_ratio": float(np.percentile(np.abs(logr), 90))}


def within_session_corr(fwd, tsd, session_ids):
    """r i rho w obrebie sesji FWD: logarytmy zdemeanowane po sesji (sesje z >= 2 parami), korelacja na resztach.
    Zwraca (r, rho, n)."""
    fwd = np.asarray(fwd, float)
    tsd = np.asarray(tsd, float)
    sess = np.asarray(session_ids)
    ok = valid_pairs(fwd, tsd)
    f, t, s = np.log(fwd[ok]), np.log(tsd[ok]), sess[ok]
    uniq = np.unique(s)
    if len(uniq) < 2:
        return float("nan"), float("nan"), int(ok.sum())
    fm, tm = f.copy(), t.copy()
    for u in uniq:
        m = s == u
        if m.sum() >= 2:
            fm[m] = f[m] - np.mean(f[m])
            tm[m] = t[m] - np.mean(t[m])
    try:
        r = float(pearsonr(fm, tm)[0])
        rho = float(spearmanr(fm, tm)[0])
    except Exception:
        r, rho = float("nan"), float("nan")
    return r, rho, int(ok.sum())


def bootstrap_ci(fwd, tsd, session_ids, lam_log: float, n_boot: int, seed: int = BOOT_SEED_CI) -> dict:
    """Bootstrap blokowy po sesjach FWD: losowanie unikalnych sesji ze zwracaniem (tyle, ile jest unikalnych),
    wszystkie ich pary razem; przedzialy percentylowe 2,5/97,5. Zwraca {miara: (lo, hi)}."""
    fwd = np.asarray(fwd, float)
    tsd = np.asarray(tsd, float)
    session_ids = np.asarray(session_ids)
    uniq = np.unique(session_ids)
    if len(uniq) < 3:
        return {k: (float("nan"), float("nan")) for k in POINT_KEYS}
    idx_by_sess = {s: np.nonzero(session_ids == s)[0] for s in uniq}
    rng = np.random.default_rng(seed)
    acc = defaultdict(list)
    for _ in range(n_boot):
        chosen = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_sess[s] for s in chosen])
        ps = point_stats(fwd[idx], tsd[idx], lam_log)
        for k in POINT_KEYS:
            acc[k].append(ps[k])
    out = {}
    for k in POINT_KEYS:
        v = np.array(acc[k], float)
        v = v[np.isfinite(v)]
        out[k] = ((float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) >= 10
                  else (float("nan"), float("nan")))
    return out


def agreement_row(fwd_raw, tsd_raw, session_ids, lam_log: float, n_boot: int, extra: dict | None = None,
                  seed: int = BOOT_SEED_CI) -> dict:
    """Wiersz miar z przedzialami (bootstrap po sesjach) dla par z dodatnimi wartosciami po obu stronach."""
    fwd_raw = np.asarray(fwd_raw, float)
    tsd_raw = np.asarray(tsd_raw, float)
    session_ids = np.asarray(session_ids)
    ok = valid_pairs(fwd_raw, tsd_raw)
    fwd, tsd, sess = fwd_raw[ok], tsd_raw[ok], session_ids[ok]
    pt = point_stats(fwd, tsd, lam_log)
    row = dict(extra or {})
    row["n_pairs"] = pt["n"]
    row["n_sessions"] = int(len(np.unique(sess))) if len(sess) else 0
    for k in POINT_KEYS:
        row[k] = pt[k]
    if pt["n"] >= 3:
        row.update(robust_extra(fwd, tsd))
        ci = bootstrap_ci(fwd, tsd, sess, lam_log, n_boot, seed)
        for k in POINT_KEYS:
            row[f"{k}_lo"], row[f"{k}_hi"] = ci[k]
        r_ws, rho_ws, n_ws = within_session_corr(fwd, tsd, sess)
    else:
        row.update({"mad_log_ratio": float("nan"), "p90_abs_log_ratio": float("nan")})
        for k in POINT_KEYS:
            row[f"{k}_lo"] = row[f"{k}_hi"] = float("nan")
        r_ws = rho_ws = float("nan")
        n_ws = 0
    row["r_within_session"] = r_ws
    row["rho_within_session"] = rho_ws
    return row
