"""N1 fwd_tempcorr: caly potok od plikow FWD do tabeli wynikow i podsumowania."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .. import __version__
from ..common.config import ConfigError, N1Config, resolve_path
from ..common.constants import GEOPHONES
from ..common.flags import Flag, flags_series_to_text
from .io import read_fwd
from .normalize import select_drops, to_geophones
from .quality import assess_temperature
from .tempcorr import correct_deflections

log = logging.getLogger(__name__)

THICKNESS_RANGE_CM = (15.0, 30.0)


@dataclass
class FileResult:
    source: str
    table: pd.DataFrame
    summary: dict
    meta: dict


@dataclass
class N1Result:
    files: list = field(default_factory=list)
    outputs: list = field(default_factory=list)


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _temperature(cfg: N1Config, stations: pd.DataFrame, base_dir) -> tuple[pd.Series, pd.DataFrame, str]:
    """Zwraca (T_mid [C], ocena jakosci: t_status/t_age_min/flag_mask, etykieta zrodla)."""
    t_cfg = cfg.temperature
    quality = pd.DataFrame({"t_status": "external", "t_age_min": np.nan, "flag_mask": 0}, index=stations.index)
    quality["flag_mask"] = quality["flag_mask"].astype(np.int64)
    if t_cfg.source == "constant":
        temp = pd.Series(float(t_cfg.constant_c), index=stations.index)
        quality["t_status"] = "constant"
        return temp, quality, "constant"
    if t_cfg.source == "csv_join":
        csv_path = resolve_path(t_cfg.csv, base_dir)
        ext = pd.read_csv(csv_path, encoding="utf-8-sig")
        if "station_id" not in ext or t_cfg.column not in ext:
            raise ConfigError(f"{csv_path.name}: wymagane kolumny station_id i {t_cfg.column}")
        keys = ["station_id"] + (["session_id"] if "session_id" in ext and "session_id" in stations else [])
        merged = stations[keys].merge(ext[keys + [t_cfg.column]], on=keys, how="left")
        temp = pd.Series(merged[t_cfg.column].to_numpy(dtype=float), index=stations.index)
        missing = ~np.isfinite(temp.to_numpy())
        quality.loc[missing, "t_status"] = "missing"
        quality.loc[missing, "flag_mask"] = int(Flag.T_MISSING)
        return temp, quality, f"csv:{csv_path.name}:{t_cfg.column}"
    # kolumna z danych stacji (domyslnie wpis operatora)
    if t_cfg.column not in stations:
        raise ConfigError(f"brak kolumny temperatury {t_cfg.column!r} w danych stacji (dostepne: {list(stations.columns)})")
    temp = pd.Series(stations[t_cfg.column].to_numpy(dtype=float), index=stations.index)
    if t_cfg.column == "asphalt_temp":
        quality = assess_temperature(stations, "asphalt_temp", tuple(cfg.correction.placeholder_temps_c),
                                     t_cfg.max_age_min)
    else:
        miss = ~np.isfinite(temp.to_numpy())
        quality.loc[miss, "t_status"] = "missing"
        quality.loc[miss, "flag_mask"] = int(Flag.T_MISSING)
    return temp, quality, f"file:{t_cfg.column}"


def process_file(cfg: N1Config, path: Path, stations_path: Path | None) -> FileResult:
    c = cfg.correction
    data = read_fwd(path, fmt=cfg.input.format, stations_path=stations_path)
    norm = select_drops(data.drops, cfg.input.drop_rule, c.load_ref_kn)
    stations = data.stations.copy()
    stations = stations[stations["station_id"].isin(norm.index)].reset_index(drop=True)
    stations = stations.drop_duplicates("station_id", keep="first").reset_index(drop=True)
    session_of = pd.Series(stations["session_id"].to_numpy(), index=stations["station_id"].to_numpy())
    geo = to_geophones(norm, session_of, data.sessions, cfg.input.geophone_mapping)
    geo_flags = geo.pop("flag_mask")

    temp, quality, t_source = _temperature(cfg, stations, cfg.base_dir)
    d_stat = geo.loc[stations["station_id"]].reset_index(drop=True)
    cor = correct_deflections(d_stat, temp.to_numpy(), variant=c.variant, coefficient_set=c.coefficient_set,
                              road_type=c.road_type, ranges_c=c.ranges_c, indices_max_c=c.indices_max_c,
                              t_ref=c.t_ref_c,
                              coefficients_file=(resolve_path(c.coefficients_file, cfg.base_dir)
                                                 if c.coefficients_file else None),
                              coefficients_scope=c.coefficients_scope)

    force = norm["force_kn"].loc[stations["station_id"]].to_numpy(dtype=float)
    mask = cor.flag_mask.to_numpy(dtype=np.int64).copy()
    mask |= quality["flag_mask"].to_numpy(dtype=np.int64)
    mask |= geo_flags.loc[stations["station_id"]].to_numpy(dtype=np.int64)
    mask |= norm["flag_mask"].loc[stations["station_id"]].to_numpy(dtype=np.int64)
    off = np.isfinite(force) & (np.abs(force - c.load_ref_kn) / c.load_ref_kn * 100.0 > c.force_tolerance_pct)
    mask[off] |= int(Flag.FORCE_OFF_NOMINAL)
    th = cfg.temperature.thickness_cm
    if th is not None and not (THICKNESS_RANGE_CM[0] <= th <= THICKNESS_RANGE_CM[1]):
        mask |= int(Flag.THICKNESS_OUT_OF_RANGE)

    coef_label = cor.meta["coefficients"]["set"]
    table = pd.DataFrame({
        "session_id": stations["session_id"].to_numpy(),
        "station_id": stations["station_id"].to_numpy(),
        "station_km": stations["station_km"].to_numpy(),
        "measured_at": stations["time"].to_numpy(),
        "latitude": stations["latitude"].to_numpy(),
        "longitude": stations["longitude"].to_numpy(),
        "force_kn": force,
        "n_drops": norm["n_drops"].loc[stations["station_id"]].to_numpy(),
        "t_mid_c": temp.to_numpy(),
        "t_source": t_source,
        "t_status": quality["t_status"].to_numpy(),
        "t_age_min": quality["t_age_min"].to_numpy(),
        "variant": c.variant,
        "coef_set": coef_label,
    })
    table = pd.concat([table, d_stat.reset_index(drop=True), cor.d20.reset_index(drop=True),
                       cor.indices.reset_index(drop=True)], axis=1)
    table["flags"] = mask
    table["flags_text"] = flags_series_to_text(mask)

    summary = _summarize(table, path.name)
    meta = {
        "tool": "fwd_tempcorr",
        "version": __version__,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input": {"file": str(path), "md5": _md5(path),
                  "stations_file": str(stations_path) if stations_path else None,
                  "stations_md5": _md5(stations_path) if stations_path else None, "format": data.fmt},
        "config": {"input": asdict(cfg.input), "temperature": asdict(cfg.temperature),
                   "correction": asdict(cfg.correction)},
        "correction": cor.meta,
        "temperature_source": t_source,
        "geophones": list(GEOPHONES),
        "note": ("Ugiecia D* znormalizowane do %g kN; D*_20 sprowadzone do %g C; wskazniki z ugiec skorygowanych."
                 % (c.load_ref_kn, c.t_ref_c)),
    }
    return FileResult(source=str(path), table=table, summary=summary, meta=meta)


def _summarize(table: pd.DataFrame, name: str) -> dict:
    n = len(table)
    flags = table["flags"].to_numpy(dtype=np.int64)
    t = table["t_mid_c"].to_numpy(dtype=float)
    ratio = (table["D0_20"] / table["D0"]).replace([np.inf, -np.inf], np.nan).dropna()
    out = {
        "file": name,
        "n_stations": int(n),
        "t_min_c": float(np.nanmin(t)) if np.isfinite(t).any() else np.nan,
        "t_median_c": float(np.nanmedian(t)) if np.isfinite(t).any() else np.nan,
        "t_max_c": float(np.nanmax(t)) if np.isfinite(t).any() else np.nan,
        "d0_correction_median": float(ratio.median()) if len(ratio) else np.nan,
        "n_corrected": int(table["D0_20"].notna().sum()),
    }
    for f in Flag:
        if f.name == "NONE":
            continue
        out[f"share_{f.name.lower()}"] = float(np.mean((flags & int(f)) != 0)) if n else 0.0
    return out


def run_n1(cfg: N1Config, dry_run: bool = False) -> N1Result:
    base = cfg.base_dir
    files = [resolve_path(f, base) for f in cfg.input.files]
    stations = [resolve_path(s, base) for s in cfg.input.stations_files] or [None] * len(files)
    result = N1Result()
    for path, st_path in zip(files, stations):
        log.info("przetwarzam %s", path.name)
        result.files.append(process_file(cfg, path, st_path))
    if dry_run:
        return result
    from .output import write_n1
    result.outputs = write_n1(cfg, result.files)
    return result
