"""Zapis wynikow N1: CSV (UTF-8 bez BOM), opcjonalnie XLSX, podsumowanie i plik meta JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..common.config import ConfigError, N1Config, resolve_path


def _target(path: Path, overwrite: bool) -> Path:
    if path.exists() and not overwrite:
        raise ConfigError(f"plik wynikowy istnieje: {path} (ustaw output.overwrite: true, aby nadpisac)")
    return path


def write_n1(cfg: N1Config, files: list) -> list:
    out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    summaries = []
    for fr in files:
        stem = Path(fr.source).stem
        summaries.append(fr.summary)
        if cfg.output.per_station_file:
            if "csv" in cfg.output.formats:
                p = _target(out_dir / f"{stem}_tempcorr.csv", cfg.output.overwrite)
                fr.table.to_csv(p, index=False, encoding="utf-8")
                written.append(p)
            if "xlsx" in cfg.output.formats:
                p = _target(out_dir / f"{stem}_tempcorr.xlsx", cfg.output.overwrite)
                with pd.ExcelWriter(p, engine="openpyxl") as xw:
                    fr.table.to_excel(xw, sheet_name="data", index=False)
                    pd.DataFrame([fr.summary]).to_excel(xw, sheet_name="summary", index=False)
                    pd.DataFrame(sorted((k, json.dumps(v, ensure_ascii=False, default=str))
                                        for k, v in fr.meta.items()), columns=["key", "value"]
                                 ).to_excel(xw, sheet_name="meta", index=False)
                written.append(p)
            p = _target(out_dir / f"{stem}_tempcorr_meta.json", cfg.output.overwrite)
            p.write_text(json.dumps(fr.meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            written.append(p)
    if cfg.output.summary:
        p = _target(out_dir / "summary.csv", cfg.output.overwrite)
        pd.DataFrame(summaries).to_csv(p, index=False, encoding="utf-8")
        written.append(p)
    return written
