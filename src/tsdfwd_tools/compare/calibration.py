"""Kalibracja przelicznika TSD -> FWD z ocena poza proba (z pominieciem sesji).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2bR9_lustro_kalibracja.py (fit_affine, fit_multiplier, errors, leave-one-session-out),
stan c67f7fe / 2026-11-06. Modele: mnoznik (bez wyrazu wolnego, a = sum(FWD*TSD)/sum(TSD^2), skala surowa) i funkcja
afiniczna FWD = a*TSD + b. Ocena: MAE [um] i mediana |ln(FWD/FWD_pred)|."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def fit_affine(tsd, fwd):
    tsd = np.asarray(tsd, float)
    fwd = np.asarray(fwd, float)
    ok = np.isfinite(tsd) & np.isfinite(fwd)
    if ok.sum() < 5:
        return float("nan"), float("nan")
    a, b = np.polyfit(tsd[ok], fwd[ok], 1)
    return float(a), float(b)


def fit_multiplier(tsd, fwd) -> float:
    tsd = np.asarray(tsd, float)
    fwd = np.asarray(fwd, float)
    ok = np.isfinite(tsd) & np.isfinite(fwd) & (tsd != 0)
    if ok.sum() < 5:
        return float("nan")
    return float(np.sum(fwd[ok] * tsd[ok]) / np.sum(tsd[ok] ** 2))


def errors(fwd_pred, fwd_true):
    """Zwraca (MAE, mediana |ln(prawda/prognoza)|, n)."""
    fwd_pred = np.asarray(fwd_pred, float)
    fwd_true = np.asarray(fwd_true, float)
    ok = np.isfinite(fwd_pred) & np.isfinite(fwd_true)
    if ok.sum() == 0:
        return float("nan"), float("nan"), 0
    mae = float(np.mean(np.abs(fwd_true[ok] - fwd_pred[ok])))
    ok2 = ok & (fwd_pred > 0) & (fwd_true > 0)
    if ok2.sum() == 0:
        return mae, float("nan"), int(ok.sum())
    return mae, float(np.median(np.abs(np.log(fwd_true[ok2] / fwd_pred[ok2])))), int(ok.sum())


def calibrate(tsd, fwd, groups, model: str = "multiplier", label: str = "") -> list:
    """Dopasowanie w probie i ocena z pominieciem grupy (sesji): leave-one-group-out.
    model: 'multiplier' | 'affine'. Zwraca liste wierszy (scope in_sample / leave_one_group_out)."""
    tsd = np.asarray(tsd, float)
    fwd = np.asarray(fwd, float)
    groups = np.asarray(groups)
    if model not in ("multiplier", "affine"):
        raise ValueError(f"nieznany model kalibracji: {model!r} (dozwolone: multiplier, affine)")
    if model == "multiplier":
        a = fit_multiplier(tsd, fwd)
        b = float("nan")
        pred_in = a * tsd
    else:
        a, b = fit_affine(tsd, fwd)
        pred_in = a * tsd + b
    mae_in, mlog_in, n_in = errors(pred_in, fwd)
    rows = [dict(variant=label, model=model, scope="in_sample", a=a, b=b, n=n_in, mae=mae_in,
                 median_abs_log_ratio=mlog_in)]
    pred_out = np.full(len(tsd), np.nan)
    for g in np.unique(groups):
        m_out = groups == g
        if model == "multiplier":
            a_g = fit_multiplier(tsd[~m_out], fwd[~m_out])
            if math.isfinite(a_g):
                pred_out[m_out] = a_g * tsd[m_out]
        else:
            a_g, b_g = fit_affine(tsd[~m_out], fwd[~m_out])
            if math.isfinite(a_g):
                pred_out[m_out] = a_g * tsd[m_out] + b_g
    mae_o, mlog_o, n_o = errors(pred_out, fwd)
    rows.append(dict(variant=label, model=model, scope="leave_one_group_out", a=float("nan"), b=float("nan"),
                     n=n_o, mae=mae_o, median_abs_log_ratio=mlog_o))
    return rows


def calibration_table(tsd, fwd, groups, models=("multiplier",), label: str = "") -> pd.DataFrame:
    rows = []
    for m in models:
        rows.extend(calibrate(tsd, fwd, groups, m, label))
    return pd.DataFrame(rows)
