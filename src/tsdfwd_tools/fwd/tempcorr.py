"""N1: korekta temperaturowa ugiec FWD na kazdym czujniku, potem wskazniki krzywizny z ugiec skorygowanych.

Warianty (raport PW.S-1063, 7.1): A - liniowy d20 = d_T * [1 + k_i * (20 - T)] (zakres T_mid 5-25 C);
B - wykladniczy d20 = d_T * exp[beta_i * (20 - T)] (zakres 5-30 C); legacy - dotychczasowy wzor krajowy z jednym k na
kazdym czujniku (porownawczo). Ponizej dolnej granicy zakresu (domyslnie 5 C) korekta nie ma zastosowania (stan podloza):
ugiecia skorygowane puste, flaga T_BELOW_5C. Powyzej gornej granicy zakresu korekta jest wykonywana, a wynik oznaczony
(T_ABOVE_RANGE) — rejestr oznaczen zamiast usuwania."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..common.coefficients import legacy_table, load_coefficients
from ..common.constants import GEOPHONES, INDICES_MAX_C, RANGE_A_C, RANGE_B_C, RANGE_LEGACY_C, T_REF_C
from ..common.flags import Flag
from ..common.rules import CorrectionForm, factor
from .indices import curvature_indices

_DEFAULT_RANGES = {"A": RANGE_A_C, "B": RANGE_B_C, "legacy": RANGE_LEGACY_C}


@dataclass
class CorrectedDeflections:
    d20: pd.DataFrame            # D0_20 .. D1800_20 [um]
    indices: pd.DataFrame        # SCI300_20, BDI_20, BCI_20 [um]
    flag_mask: pd.Series         # maska bitowa Flag
    meta: dict = field(default_factory=dict)


def correct_deflections(d_um: pd.DataFrame, temp_c, variant: str = "B", coefficient_set: str = "e2a3_full",
                        road_type: str = "public", ranges_c: dict | None = None,
                        indices_max_c: float = INDICES_MAX_C, t_ref: float = T_REF_C) -> CorrectedDeflections:
    """d_um: ugiecia [um] znormalizowane do sily odniesienia, kolumny D0..D1800; temp_c: temperatura T_mid [C]
    (Series o tym samym indeksie lub skalar)."""
    if variant not in ("A", "B", "legacy"):
        raise ValueError(f"nieznany wariant korekty: {variant!r} (dozwolone: A, B, legacy)")
    ranges = {**_DEFAULT_RANGES, **(ranges_c or {})}
    lo, hi = (float(x) for x in ranges[variant])
    temp = pd.Series(temp_c, index=d_um.index, dtype=float) if np.isscalar(temp_c) \
        else pd.Series(np.asarray(temp_c, dtype=float), index=d_um.index)
    if variant == "legacy":
        table, form = legacy_table(road_type), CorrectionForm.LINEAR
    elif variant == "A":
        table, form = load_coefficients(coefficient_set), CorrectionForm.LINEAR
    else:
        table, form = load_coefficients(coefficient_set), CorrectionForm.EXPONENTIAL

    t = temp.to_numpy(dtype=float)
    finite = np.isfinite(t)
    below = finite & (t < lo)
    above = finite & (t > hi)
    applicable = finite & ~below
    mask = np.zeros(len(t), dtype=np.int64)
    mask[~finite] |= int(Flag.T_MISSING)
    mask[below] |= int(Flag.T_BELOW_5C)
    mask[above] |= int(Flag.T_ABOVE_RANGE)
    if variant == "legacy":
        mask |= int(Flag.LEGACY_RULE)

    d20 = pd.DataFrame(index=d_um.index, dtype=float)
    for name in GEOPHONES:
        param = table.k(name) if form is CorrectionForm.LINEAR else table.beta(name)
        f = np.where(applicable, factor(np.where(applicable, t, t_ref), form, param, t_ref), np.nan)
        f = np.where(f > 0, f, np.nan)
        d20[f"{name}_20"] = d_um[name].to_numpy(dtype=float) * f

    idx = curvature_indices(d20)
    above_idx = applicable & (t > indices_max_c)
    mask[above_idx] |= int(Flag.INDEX_ABOVE_RANGE)
    nonpos = (idx.to_numpy(dtype=float) <= 0).any(axis=1)
    mask[nonpos] |= int(Flag.INDEX_NONPOSITIVE)

    meta = {
        "variant": variant,
        "form": form.value,
        "coefficients": table.meta,
        "t_ref_c": t_ref,
        "validity_range_c": [lo, hi],
        "indices_max_c": indices_max_c,
        "rule": "korekta na kazdym czujniku; SCI300/BDI/BCI z ugiec skorygowanych (bez wlasnych wspolczynnikow wskaznikow)",
    }
    return CorrectedDeflections(d20=d20, indices=idx, flag_mask=pd.Series(mask, index=d_um.index), meta=meta)
