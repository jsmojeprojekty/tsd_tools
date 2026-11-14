"""Wskazniki krzywizny czaszy FWD liczone WYLACZNIE z ugiec skorygowanych (raport PW.S-1063, 5.3 i 7.1).

SCI300 = D0 - D300, BDI = D300 - D600, BCI = D600 - D900. Zadnych wlasnych wspolczynnikow wskaznikow:
wspolczynnik wskaznika zalezalby od ksztaltu czaszy (D300/D0) i nie przenosi sie miedzy odcinkami."""

from __future__ import annotations

import pandas as pd

from ..common.constants import INDICES


def curvature_indices(d: pd.DataFrame, suffix: str = "_20") -> pd.DataFrame:
    """d: ugiecia (kolumny D0, D300, D600, D900 lub z sufiksem, np. D0_20) -> SCI300/BDI/BCI z tym samym sufiksem."""
    out = pd.DataFrame(index=d.index)
    for name, (near, far) in INDICES.items():
        out[f"{name}{suffix}"] = d[f"{near}{suffix}"] - d[f"{far}{suffix}"]
    return out
