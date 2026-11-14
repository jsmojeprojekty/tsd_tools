"""fwd_fit: dopasowanie wspolczynnikow k i beta z wizyt uzytkownika (opcjonalny modul N1)."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .. import __version__
from ..common.config import ConfigError, resolve_path
from ..common.config_fit import FitConfig
from .fit import fit_table

log = logging.getLogger(__name__)


def _truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().isin(["1", "TRUE", "PRAWDA", "TAK", "1.0"])


def read_visits(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku z wizytami: {path}")
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def run_fit(cfg: FitConfig, dry_run: bool = False) -> dict:
    inp = cfg.input
    path = resolve_path(inp.visits, cfg.base_dir)
    visits = read_visits(path)
    n_all = len(visits)
    for col in inp.exclude_if_true:
        if col not in visits:
            raise ConfigError(f"input.exclude_if_true: brak kolumny {col!r}")
        visits = visits[~_truthy(visits[col])]
    for col in inp.require_true:
        if col not in visits:
            raise ConfigError(f"input.require_true: brak kolumny {col!r}")
        visits = visits[_truthy(visits[col])]
    log.info("wizyty: %d (po filtrach %d)", n_all, len(visits))
    f = cfg.fit
    table = fit_table(visits, f.indicators, inp.point_col, inp.date_col, inp.t_col, tuple(f.t_range_c), f.n_boot,
                      f.scope_label, tuple(f.k_bounds), f.min_n)
    meta = {
        "tool": "fwd_fit", "version": __version__, "created_at": datetime.now().isoformat(timespec="seconds"),
        "input": {"file": str(path), "md5": hashlib.md5(path.read_bytes()).hexdigest(),
                  "n_rows": int(n_all), "n_rows_after_filters": int(len(visits))},
        "config": {"input": asdict(inp), "fit": asdict(f)},
        "method": ("log-link (quasi-Poisson), efekt staly punkt x miesiac, wizyty %g <= T < %g C; "
                   "k: D = a_g/(1+k(20-T)); CI: bootstrap blokowy po dniach, %d replik" % (f.t_range_c[0], f.t_range_c[1], f.n_boot)),
        "note": ("Wspolczynniki dopasowane do danych uzytkownika nie zastepuja zestawu z raportu; "
                 "wskazniki SCI300/BDI/BCI w tabeli maja charakter diagnostyczny (nie sa uzywane do korekty)."),
    }
    outputs = []
    if not dry_run:
        out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"{path.stem}_coefficients.csv"
        meta_path = out_dir / f"{path.stem}_coefficients_meta.json"
        for p in (csv_path, meta_path):
            if p.exists() and not cfg.output.overwrite:
                raise ConfigError(f"plik wynikowy istnieje: {p} (ustaw output.overwrite: true)")
        table.to_csv(csv_path, index=False, encoding="utf-8")
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        outputs = [csv_path, meta_path]
    return {"table": table, "meta": meta, "outputs": outputs, "n_visits": int(len(visits))}
