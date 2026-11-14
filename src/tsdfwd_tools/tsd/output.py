"""Zapis wynikow N3: CSV (UTF-8 bez BOM), plik meta JSON, XML DSN `UC`."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..common.config import ConfigError, resolve_path
from ..common.config_n3 import N3Config
from .uc_export import write_uc_xml


def _target(path: Path, overwrite: bool) -> Path:
    if path.exists() and not overwrite:
        raise ConfigError(f"plik wynikowy istnieje: {path} (ustaw output.overwrite: true, aby nadpisac)")
    return path


def write_n3(cfg: N3Config, results: list) -> list:
    out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ow = cfg.output.overwrite
    written, summaries = [], []
    for res in results:
        stem = Path(res["run"].source).name.split(".")[0]
        summaries.append(res["summary"])
        if cfg.output.rows_csv:
            cols = ["chainage_m", "pos_m", "lat", "lon", "speed_kmh", "temp_road", "temp_air", "strain_right_kg", "d0", "t12_c",
                    "d0_20", "gof", "hampel_rejected", "a020", "a030", "a031", "a061", "a090", "a091", "a0361", "a6191",
                    "flags", "flags_text"] + (["d0_fwd20"] if "d0_fwd20" in res["rows"] else [])
            p = _target(out_dir / f"{stem}_rows.csv", ow)
            res["rows"][cols].to_csv(p, index=False, encoding="utf-8")
            written.append(p)
        if cfg.output.windows_csv:
            p = _target(out_dir / f"{stem}_windows_{cfg.xml_uc.step_m}m.csv", ow)
            res["windows"].to_csv(p, index=False, encoding="utf-8")
            written.append(p)
        for a, agg in res["aggs"].items():
            p = _target(out_dir / f"{stem}_agg_{a}m.csv", ow)
            agg.to_csv(p, index=False, encoding="utf-8")
            written.append(p)
        if cfg.xml_uc.enabled:
            x = cfg.xml_uc
            p = _target(out_dir / f"UC_{stem}.xml", ow)
            write_uc_xml(p, res["xml_records"], x.kod_oddz, x.rok, x.schema_location)
            written.append(p)
        meta = dict(res["meta"])
        meta["xml_uc"] = ({"enabled": True, "profile": cfg.xml_uc.profile, "scale": cfg.xml_uc.scale,
                           "fwd_scale": res["meta"].get("fwd_scale") if cfg.xml_uc.scale == "fwd" else None,
                           "fwd_scale_unverified_fields": ["SCI_200", "SCI_300", "D_200", "D_300"] if cfg.xml_uc.scale == "fwd" else [],
                           "records": int(len(res["xml_records"]))} if cfg.xml_uc.enabled else {"enabled": False})
        p = _target(out_dir / f"{stem}_n3_meta.json", ow)
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        written.append(p)
    p = _target(out_dir / "summary.csv", ow)
    pd.DataFrame(summaries).to_csv(p, index=False, encoding="utf-8")
    written.append(p)
    return written
