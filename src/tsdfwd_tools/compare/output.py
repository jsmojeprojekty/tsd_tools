"""Zapis wynikow N4: CSV (UTF-8 bez BOM), meta JSON i prosty raport HTML."""

from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from ..common.config import ConfigError, resolve_path
from ..common.config_n4 import N4Config

TABLES = (("agreement", "agreement.csv"), ("groups", "agreement_groups.csv"), ("multiplier", "agreement_ci.csv"),
          ("conditions", "conditions.csv"), ("calibration", "calibration.csv"), ("nulls", "null_checks.csv"),
          ("null_delta", "null_delta.csv"), ("conversion", "conversion.csv"), ("pairs", "pairs_corrected.csv"),
          # tryb geometry: tabele posrednie (kandydaci na pary, polozenie plyty FWD, przejscia TSD, os, pary zerowe, sesje, ciagi)
          ("geo_pairs", "geometry_pairs.csv"), ("geo_fwd", "fwd_plate_positions.csv"), ("geo_passes", "tsd_passes.csv"),
          ("geo_corridors", "corridors.csv"), ("geo_nulls", "geometry_null_pairs.csv"),
          ("geo_sessions", "fwd_sessions.csv"), ("geo_runs", "fwd_session_runs.csv"), ("geo_sections", "sections.csv"),
          ("lambda_estimate", "lambda_estimate.csv"))


def _target(path: Path, overwrite: bool) -> Path:
    if path.exists() and not overwrite:
        raise ConfigError(f"plik wynikowy istnieje: {path} (ustaw output.overwrite: true, aby nadpisac)")
    return path


def _fmt(v):
    return f"{v:.4g}" if isinstance(v, float) else html.escape(str(v))


def _html_table(df: pd.DataFrame, cols=None, maxrows: int = 60) -> str:
    if df is None or df.empty:
        return "<p>brak danych</p>"
    d = df[cols] if cols else df
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
    body = "".join("<tr>" + "".join(f"<td>{_fmt(v)}</td>" for v in row) + "</tr>"
                   for row in d.head(maxrows).itertuples(index=False))
    return f"<table border='1' cellpadding='3' style='border-collapse:collapse'><tr>{head}</tr>{body}</table>"


def write_html(result: dict, path: Path) -> None:
    m = result["meta"]
    summary_cols = ["variant", "n_pairs", "n_sessions", "median_ratio", "median_ratio_lo", "median_ratio_hi",
                    "sd_log_ratio", "pearson_r", "spearman_rho", "ccc", "deming_loglog_slope", "r_within_session"]
    parts = [
        "<html><head><meta charset='utf-8'><title>tsd_fwd_compare</title></head><body>",
        f"<h1>Porownanie TSD-FWD (tryb {html.escape(str(m.get('mode', 'pairs')))})</h1>",
        f"<p>Pary: {m['n_pairs']} (wazne: {m['n_valid_pairs']}), sesji FWD: {m['n_sessions']}; "
        f"pary z T12 poza zakresem lub bez T12: {m['n_t12_outside_or_missing']}. beta D0 = {m['beta_pct_used']:.5f} %/C.</p>",
        f"<p>{html.escape(m['note'])}</p>",
        "<h2>Miary zgodnosci</h2>", _html_table(result["agreement"], [c for c in summary_cols if c in result["agreement"]]),
        "<h2>Przedzialy mnoznika (mala liczba klastrow)</h2>", _html_table(result["multiplier"]),
        "<h2>Funkcja przeliczajaca</h2>", _html_table(result["conversion"]),
        "<h2>Warunki zgodnosci</h2>", _html_table(result["conditions"]),
        "<h2>Kalibracja (ocena poza proba)</h2>", _html_table(result["calibration"]),
        "<h2>Kontrola zerowa</h2>", _html_table(result["nulls"], [c for c in ["pair_kind"] + summary_cols[1:]
                                                                  + ["rho_within_session"] if c in result["nulls"]]),
        _html_table(result["null_delta"]),
        "</body></html>",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def write_n4(cfg: N4Config, result: dict) -> list:
    out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, name in TABLES:
        df = result.get(key)
        if df is None or (hasattr(df, "empty") and df.empty):
            continue
        p = _target(out_dir / name, cfg.output.overwrite)
        df.to_csv(p, index=False, encoding="utf-8")
        written.append(p)
    rep = result.get("section_report")
    if rep and cfg.geometry.sections.report_html and len(rep["sections"]):
        from .section_report import write_review
        p = _target(out_dir / "section_review.html", cfg.output.overwrite)
        write_review(p, rep["sections"], rep["matches"], rep["runs"], rep["sessions"], cfg.geometry.sections.report_max_sections)
        written.append(p)
    p = _target(out_dir / "meta.json", cfg.output.overwrite)
    p.write_text(json.dumps(result["meta"], ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    written.append(p)
    p = _target(out_dir / "report.html", cfg.output.overwrite)
    write_html(result, p)
    written.append(p)
    return written
