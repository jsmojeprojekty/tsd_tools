"""Zapis wynikow N2: CSV (UTF-8 bez BOM, kropka dziesietna) i plik meta JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..common.config import ConfigError, resolve_path
from ..common.config_n2 import N2Config


def _target(path: Path, overwrite: bool) -> Path:
    if path.exists() and not overwrite:
        raise ConfigError(f"plik wynikowy istnieje: {path} (ustaw output.overwrite: true, aby nadpisac)")
    return path


def write_n2(cfg: N2Config, table: pd.DataFrame, meta: dict) -> list:
    out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ow = cfg.output.overwrite
    p_csv = _target(out_dir / f"{cfg.output.name}.csv", ow)
    p_meta = _target(out_dir / f"{cfg.output.name}_meta.json", ow)
    t = table.copy()
    t["measured_at_local"] = pd.to_datetime(t["measured_at_local"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    t.to_csv(p_csv, index=False, encoding="utf-8")
    p_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return [p_csv, p_meta]
