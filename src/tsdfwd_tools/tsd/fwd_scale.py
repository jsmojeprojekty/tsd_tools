"""Przelicznik TSD -> FWD stosowany w N3 (skala wartosci DSN `UC` i opcjonalnych kolumn CSV).

Przelicznik zmienia sie po kazdej kalibracji (co najmniej raz w roku), wiec nie ma wartosci domyslnej: podaje sie go wprost
(`processing.to_fwd_multiplier`) albo bierze z wyniku porownania N4 (`processing.to_fwd_conversion_csv` = `conversion.csv` z N4
dla okresu kalibracji, gdy funkcja przeliczajaca jest proporcjonalna)."""

from __future__ import annotations

import math

import pandas as pd

from ..common.config import ConfigError, resolve_path


def fwd_factor(cfg) -> dict | None:
    """Slownik {factor, lo, hi, source} albo None, gdy nie podano zrodla przelicznika."""
    p = cfg.processing
    if p.to_fwd_multiplier is not None:
        return {"factor": float(p.to_fwd_multiplier), "lo": None, "hi": None, "source": "config:to_fwd_multiplier"}
    if not p.to_fwd_conversion_csv:
        return None
    path = resolve_path(p.to_fwd_conversion_csv, cfg.base_dir)
    if not path.is_file():
        raise ConfigError(f"processing.to_fwd_conversion_csv: brak pliku {path}")
    df = pd.read_csv(path)
    if df.empty or "form" not in df:
        raise ConfigError(f"{path.name}: to nie jest conversion.csv z N4 (brak kolumny 'form')")
    row = df.iloc[0]
    if str(row["form"]) != "proportional":
        raise ConfigError(f"{path.name}: N4 podal funkcje '{row['form']}' (nie proporcjonalna); N3 stosuje tylko mnoznik - "
                          "podaj processing.to_fwd_multiplier recznie po decyzji, jak przeliczac")
    factor = float(row["factor"])
    if not math.isfinite(factor) or factor <= 0:
        raise ConfigError(f"{path.name}: niepoprawny mnoznik {factor}")
    lo = float(row["factor_lo"]) if "factor_lo" in df and pd.notna(row["factor_lo"]) else None
    hi = float(row["factor_hi"]) if "factor_hi" in df and pd.notna(row["factor_hi"]) else None
    return {"factor": factor, "lo": lo, "hi": hi, "source": f"n4:{path.name}"}
