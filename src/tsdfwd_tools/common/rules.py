"""Postacie korekty temperaturowej ugiec do temperatury odniesienia.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2aR2_rules.py (apply_rule), e2aR4_indices.py (apply_f),
stan c67f7fe / 2026-10-26. Zmiana wzgledem zrodla: postac jest typem wyliczeniowym; nieznana wartosc
zglasza wyjatek (w zrodle kazda wartosc inna niz 'guideline' dawala ciche przejscie na postac wykladnicza).

Konwencja: D_20 = D_T * f(T). LINEAR: f = 1 + k*(T_ref - T); EXPONENTIAL: f = exp(beta*(T_ref - T)).
Dla T < T_ref f > 1 (ugiecie w niskiej temperaturze jest mniejsze, po korekcie rosnie).
"""

from __future__ import annotations

import enum

import numpy as np

from .constants import T_REF_C


class CorrectionForm(enum.Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"

    @classmethod
    def parse(cls, value) -> "CorrectionForm":
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError as exc:
            raise ValueError(f"nieznana postac korekty: {value!r} (dozwolone: linear, exponential)") from exc


def factor(temp_c, form: CorrectionForm, param, t_ref: float = T_REF_C) -> np.ndarray:
    """Mnoznik korekty f(T); param = k [1/C] (LINEAR) lub beta [1/C] (EXPONENTIAL)."""
    form = CorrectionForm.parse(form)
    temp = np.asarray(temp_c, dtype=float)
    if form is CorrectionForm.LINEAR:
        return 1.0 + param * (t_ref - temp)
    return np.exp(param * (t_ref - temp))


def apply_correction(y, temp_c, form: CorrectionForm, param, t_ref: float = T_REF_C) -> np.ndarray:
    """Ugiecie sprowadzone do temperatury odniesienia: y * f(T)."""
    return np.asarray(y, dtype=float) * factor(temp_c, form, param, t_ref)
