"""Korekta obu stron pary do 20 C (raport 6.3, 7.2 p. 4): D0 FWD i d0 TSD tym samym wspolczynnikiem D0.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\z15_temp_correction.py (wariant main_after: wykladnicza beta D0 = 1,6041 %/C,
T12 z modelu po obu stronach), e2bR9_lustro_data.py (correct_pair, k02), stan c67f7fe / 2026-11-07.

Zabronione: normalizacja temperatura powierzchni (pirometru) — T musi byc temperatura warstwy (T12 z N2/modelu)."""

from __future__ import annotations

import numpy as np

from ..common.coefficients import load_coefficients
from ..common.constants import LEGACY_K, T_REF_C
from ..common.rules import CorrectionForm, apply_correction

TREATMENTS = ("none", "main_after", "k02")


def default_beta_pct() -> float:
    """beta D0 [%/C] z zestawu e2a3_full (scope lacznie)."""
    return load_coefficients("e2a3_full").beta("D0") * 100.0


def correct_pair_values(fwd, tsd, fwd_t12, tsd_t12, treatment: str = "main_after",
                        beta_pct: float | None = None, t_ref: float = T_REF_C):
    """Zwraca (D0_FWD,20, d0_TSD,20). none: bez korekty; main_after: exp[beta*(20-T12)] (beta D0, ta sama po obu
    stronach); k02: linia krajowa 1 + 0,02*(20-T12). Brak temperatury po ktorejs stronie = NaN po tej stronie."""
    fwd = np.asarray(fwd, float)
    tsd = np.asarray(tsd, float)
    if treatment == "none":
        return fwd.copy(), tsd.copy()
    if treatment == "main_after":
        b = (default_beta_pct() if beta_pct is None else beta_pct) / 100.0
        return (apply_correction(fwd, np.asarray(fwd_t12, float), CorrectionForm.EXPONENTIAL, b, t_ref),
                apply_correction(tsd, np.asarray(tsd_t12, float), CorrectionForm.EXPONENTIAL, b, t_ref))
    if treatment == "k02":
        k = LEGACY_K["public"]
        return (apply_correction(fwd, np.asarray(fwd_t12, float), CorrectionForm.LINEAR, k, t_ref),
                apply_correction(tsd, np.asarray(tsd_t12, float), CorrectionForm.LINEAR, k, t_ref))
    raise ValueError(f"nieznana korekta: {treatment!r} (dozwolone: {', '.join(TREATMENTS)})")
