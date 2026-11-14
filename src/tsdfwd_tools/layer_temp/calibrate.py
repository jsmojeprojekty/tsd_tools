"""Kalibracja jednorazowa wspolczynnika pochlaniania a_sw do odczytu pirometru ('masa', po korekcie IR).

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\z14b_single_shot.py (brentq po a_sw, bramka identyfikowalnosci), stan 2026-11-13.
Test tozsamosci: tests/regression/test_n2_reference.py. Kalibracja tylko zmniejsza a_sw (a <= 1): 44 % obserwacji zbioru H
trafia na gorna granice (flaga CALIB_BOUND_HI, Q-N2-6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import brentq

from .constants import A_HI, A_LO, GATE_C, XTOL


@dataclass(frozen=True)
class Calibration:
    a_sw: float
    flag: str                      # ok | gate | bound_lo | bound_hi | nosim
    ts_lo: float
    ts_hi: float


def calibrate_single_shot(ts_of_a: Callable[[float], float], target: float, a_default: float, bounds=(A_LO, A_HI),
                          gate_c: float = GATE_C, xtol: float = XTOL) -> Calibration:
    """Szuka a_sw, dla ktorego temperatura powierzchni symulacji w chwili pomiaru rowna sie `target`.

    ts_of_a(a) - temperatura powierzchni modelu [C] w chwili pomiaru dla wspolczynnika a.
    Bramka: |Ts(a_hi) - Ts(a_lo)| < gate_c -> kalibracja nieidentyfikowalna (noc, zachmurzenie), a_sw domyslne.
    Brak zmiany znaku miedzy granicami -> granica o mniejszym bledzie (bound_lo / bound_hi)."""
    lo, hi = bounds
    ts_lo, ts_hi = ts_of_a(lo), ts_of_a(hi)
    if not (np.isfinite(ts_lo) and np.isfinite(ts_hi) and np.isfinite(target)):
        return Calibration(a_default, "nosim", ts_lo, ts_hi)
    if abs(ts_hi - ts_lo) < gate_c:
        return Calibration(a_default, "gate", ts_lo, ts_hi)
    flo, fhi = ts_lo - target, ts_hi - target
    if flo * fhi > 0:
        return (Calibration(lo, "bound_lo", ts_lo, ts_hi) if abs(flo) < abs(fhi)
                else Calibration(hi, "bound_hi", ts_lo, ts_hi))
    a = brentq(lambda x: ts_of_a(x) - target, lo, hi, xtol=xtol)
    return Calibration(float(a), "ok", ts_lo, ts_hi)
