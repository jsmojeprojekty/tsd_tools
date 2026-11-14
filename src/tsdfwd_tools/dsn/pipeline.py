"""tsd_dsn: dla kazdego przejazdu TSD z katalogu (B_1510off) -> probki pirometru z pliku -> N2 (temperatura warstwy 12 cm) -> N3 -> XML DSN.

To nakladka na N2 i N3 (bez nowych metod obliczen). Nowe sa tylko: dobor probek temperatury z pliku TSD, tabela przejazdow z danymi opisowymi
odcinka (bez wartosci domyslnych) i zapis wynikow per przejazd. Przejazd z bledem (np. eksport nominalny, brak wpisu w tabeli, brak pogody) nie
przerywa pozostalych; powod jest w `batch_summary.csv`.

Zalozenia do potwierdzenia: kolumna 'GPS time' jest w UTC (konfiguracja: temperature.gps_time_basis); temperatura warstwy jest liczona dla probek
co `sample_m` (mediana pirometru w oknie +-`window_m`) i interpolowana liniowo wzdluz pikietazu przez N3."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .. import __version__
from ..common.config import ConfigError, resolve_path
from ..common.config_dsn import DsnConfig
from ..common.config_n2 import build_n2_config
from ..common.config_n3 import build_n3_config
from ..layer_temp.meteo import MeteoError
from ..layer_temp.pipeline import run_n2
from ..tsd.flags import TsdFlag
from ..tsd.fwd_scale import fwd_factor
from ..tsd.io import read_b1510off
from ..tsd.pipeline import run_n3

log = logging.getLogger(__name__)

REQUIRED_TRIP_COLS = ("plik", "kod_oddz", "rok", "droga", "jezdnia", "pas", "km_start")
CAUGHT = (ConfigError, FileNotFoundError, ValueError, KeyError, RuntimeError, MeteoError)


def _key(name: str) -> str:
    return name.split(".")[0].strip().lower()


def find_files(cfg: DsnConfig) -> list[Path]:
    i = cfg.input
    if i.tsd_files:
        files = [resolve_path(f, cfg.base_dir) for f in i.tsd_files]
    else:
        d = resolve_path(i.tsd_dir, cfg.base_dir)
        if not d.is_dir():
            raise FileNotFoundError(f"brak katalogu z przejazdami: {d}")
        files = sorted({p for pat in i.patterns for p in d.glob(pat) if not p.name.startswith("~$")})
    if not files:
        raise ConfigError("nie znaleziono zadnych plikow przejazdow TSD (sprawdz input.tsd_dir i input.patterns)")
    keys = [_key(f.name) for f in files]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise ConfigError(f"ten sam przejazd w kilku plikach (rozne rozszerzenia?): {dup}")
    return files


def read_trips(path) -> dict:
    """Tabela przejazdow: wymagane kolumny plik, kod_oddz, rok, droga, jezdnia, pas, km_start; opcjonalne km_direction, chainage_start_m,
    date_override. Klucz = nazwa pliku do pierwszej kropki (bez rozszerzenia i wielkosci liter)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"brak tabeli przejazdow: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    miss = [c for c in REQUIRED_TRIP_COLS if c not in df.columns]
    if miss:
        raise ConfigError(f"{path.name}: brak kolumn {miss} (wymagane: {list(REQUIRED_TRIP_COLS)})")
    trips: dict = {}
    for _, r in df.iterrows():
        k = _key(r["plik"])
        if not k:
            continue
        if k in trips:
            raise ConfigError(f"{path.name}: przejazd {k!r} wystepuje wiecej niz raz")
        empty = [c for c in REQUIRED_TRIP_COLS if not str(r[c]).strip()]
        if empty:
            raise ConfigError(f"{path.name}: przejazd {k!r}: puste pola {empty} (dane odcinka nie maja wartosci domyslnych)")
        try:
            xml = {"kod_oddz": str(r["kod_oddz"]).strip(), "rok": int(r["rok"]), "droga": str(r["droga"]).strip(),
                   "jezdnia": int(r["jezdnia"]), "pas": int(r["pas"]), "km_start": float(str(r["km_start"]).replace(",", "."))}
            if "km_direction" in df.columns and str(r["km_direction"]).strip():
                xml["km_direction"] = str(r["km_direction"]).strip()
            if "chainage_start_m" in df.columns and str(r["chainage_start_m"]).strip():
                xml["chainage_start_m"] = float(str(r["chainage_start_m"]).replace(",", "."))
            if "date_override" in df.columns and str(r["date_override"]).strip():
                xml["date_override"] = str(r["date_override"]).strip()
        except ValueError as exc:
            raise ConfigError(f"{path.name}: przejazd {k!r}: niepoprawna wartosc ({exc})") from exc
        trips[k] = xml
    return trips


def build_survey(run, t, date_override: str | None = None) -> pd.DataFrame:
    """Probki do N2: co `sample_m` wzdluz pikietazu (z koncami przejazdu); w kazdej mediana pirometru, powietrza i polozenia w oknie
    +-window_m oraz czas (UTC z 'GPS time' zamieniany na lokalny Europe/Warsaw z DST)."""
    d = run.data
    date = pd.Timestamp(date_override) if date_override else (pd.Timestamp(run.date) if run.date else None)
    if date is None:
        raise ConfigError("brak daty przejazdu (nazwa pliku T4RRRRMMDDNNNN albo date_override w tabeli przejazdow)")
    chain = d["chainage_m"].to_numpy(float)
    sec = d["gps_time_s"].to_numpy(float)
    ok_t = np.isfinite(sec) & (sec > 0)
    if not ok_t.any():
        raise ConfigError("brak czasu w kolumnie 'GPS time' - nie da sie wyznaczyc godziny pomiaru dla temperatury warstwy")
    sec_tot = sec.copy()
    idx = np.flatnonzero(ok_t)
    jumps = np.concatenate([[0], (np.diff(sec[idx]) < -43200).cumsum()])           # przejscie przez polnoc
    sec_tot[idx] = sec[idx] + 86400.0 * jumps
    lat, lon = d["lat"].to_numpy(float), d["lon"].to_numpy(float)
    ir, air = d["temp_road"].to_numpy(float), d["temp_air"].to_numpy(float)
    c0, c1 = np.nanmin(chain), np.nanmax(chain)
    centers = np.unique(np.concatenate([[c0], np.arange(c0 + t.sample_m, c1, t.sample_m), [c1]]))
    rows = []
    for c in centers:
        m = (np.abs(chain - c) <= t.window_m) & ok_t & np.isfinite(lat) & np.isfinite(lon)
        if not m.any():
            continue
        rows.append({"sec": float(np.median(sec_tot[m])), "latitude": float(np.median(lat[m])), "longitude": float(np.median(lon[m])),
                     "t_surface": float(np.nanmedian(ir[m])) if np.isfinite(ir[m]).any() else np.nan,
                     "t_air": float(np.nanmedian(air[m])) if np.isfinite(air[m]).any() else np.nan, "chainage_m": float(c)})
    if not rows:
        raise ConfigError("brak wierszy z czasem i polozeniem GPS - nie da sie policzyc temperatury warstwy")
    s = pd.DataFrame(rows)
    stamp = date.normalize() + pd.to_timedelta(s.pop("sec"), unit="s")
    if t.gps_time_basis == "utc":
        stamp = stamp.dt.tz_localize("UTC").dt.tz_convert("Europe/Warsaw").dt.tz_localize(None)
    s.insert(0, "measured_at_local", stamp.dt.strftime("%Y-%m-%d %H:%M:%S"))
    return s


def _count_flags(series: pd.Series) -> str:
    cnt: dict = {}
    for v in series.dropna().astype(str):
        for tok in re.split(r"[;, ]+", v):
            if tok:
                cnt[tok] = cnt.get(tok, 0) + 1
    return ";".join(f"{k}={v}" for k, v in sorted(cnt.items()))


def _nominal_check(run, name: str) -> None:
    if run.file_flags & int(TsdFlag.FILE_NOT_RECALIBRATED):
        raise ConfigError(f"{name}: eksport nominalny (pusty 'Re-calibrationfile'); wymagany eksport B_1510off "
                          "(d0 przeliczone z 9 czujnikow nachylen, bez czujnika 1,51 m)")


def process_file(cfg: DsnConfig, path: Path, trip: dict, out_dir: Path, *, http_get=None) -> dict:
    run = read_b1510off(path)
    _nominal_check(run, path.name)
    stem = path.name.split(".")[0]
    t = cfg.temperature
    survey = build_survey(run, t, trip.get("date_override"))
    work = out_dir / stem
    n2dir, n3dir = work / "n2", work / "n3"
    n2dir.mkdir(parents=True, exist_ok=True)
    survey_path = n2dir / f"{stem}_survey.csv"
    if survey_path.exists() and not cfg.output.overwrite:
        raise ConfigError(f"{survey_path} istnieje (output.overwrite: false)")
    survey["file"] = stem
    survey.to_csv(survey_path, index=False, encoding="utf-8")

    n2cfg = build_n2_config({
        "tool": "layer_temp",
        "input": {"survey_csv": str(survey_path), "passthrough": ["chainage_m", "file"], "air_column": "t_air"},
        "model": {"depth_cm": t.depth_cm, "calibration": t.calibration},
        "meteo": {"cache_dir": str(resolve_path(t.meteo_cache_dir, cfg.base_dir)), "offline": t.meteo_offline},
        "output": {"dir": str(n2dir), "overwrite": cfg.output.overwrite}}, base_dir=cfg.base_dir)
    n2 = run_n2(n2cfg, http_get=http_get)
    n2_csv = n2dir / f"{n2cfg.output.name}.csv"

    f = cfg.fwd_scale
    proc = dict(cfg.processing)
    if f.to_fwd_multiplier is not None:
        proc["to_fwd_multiplier"] = f.to_fwd_multiplier
    if f.to_fwd_conversion_csv:
        proc["to_fwd_conversion_csv"] = str(resolve_path(f.to_fwd_conversion_csv, cfg.base_dir))
    xml = {**cfg.xml, **trip, "enabled": True}
    n3cfg = build_n3_config({
        "tool": "tsd_network",
        "input": {"tsd_files": [str(path)]},
        "layer_temp": {"source": "csv", "csv": str(n2_csv), "column": "t12_c", "pos_column": "chainage_m", "file_column": "file"},
        "processing": proc, "qc": dict(cfg.qc), "xml_uc": xml,
        "output": {"dir": str(n3dir), "overwrite": cfg.output.overwrite}}, base_dir=cfg.base_dir)
    n3 = run_n3(n3cfg)
    res = n3["runs"][0]
    s = res["summary"]
    ff = fwd_factor(n3cfg)
    xml_path = next((str(p) for p in n3["outputs"] if Path(p).name.startswith("UC_")), "")
    return {"date": s["date"], "n_rows": s["n_rows"], "n_valid_d0": s["n_valid_d0"], "n2_samples": len(n2["table"]),
            "n2_valid_t12": int(n2["meta"]["n_valid_t_layer"]), "n2_flags": _count_flags(n2["table"]["flags_text"]),
            "n_xml_records": int(len(res["xml_records"])), "fwd_factor": ff["factor"] if ff else None,
            "fwd_source": ff["source"] if ff else "", "xml": xml_path}


def run_dsn(cfg: DsnConfig, dry_run: bool = False, *, http_get=None) -> dict:
    files = find_files(cfg)
    trips = read_trips(resolve_path(cfg.input.trips_csv, cfg.base_dir))
    out_dir = resolve_path(cfg.output.dir, cfg.base_dir)
    summary_path = out_dir / "batch_summary.csv"
    if not dry_run and summary_path.exists() and not cfg.output.overwrite:
        raise ConfigError(f"{summary_path} istnieje (output.overwrite: false)")
    unused = sorted(set(trips) - {_key(f.name) for f in files})
    if unused:
        log.warning("w tabeli przejazdow sa wpisy bez pliku: %s", unused)
    rows = []
    for f in files:
        row = {"file": f.name, "status": "ok", "message": ""}
        try:
            trip = trips.get(_key(f.name))
            if trip is None:
                raise ConfigError(f"{f.name}: brak wpisu w tabeli przejazdow (kolumna 'plik'); dane odcinka nie maja wartosci domyslnych")
            if dry_run:
                run = read_b1510off(f)
                _nominal_check(run, f.name)
                survey = build_survey(run, cfg.temperature, trip.get("date_override"))
                row.update({"status": "dry_run_ok", "date": str(run.date), "n_rows": len(run.data), "n2_samples": len(survey)})
            else:
                log.info("przejazd %s", f.name)
                row.update(process_file(cfg, f, trip, out_dir, http_get=http_get))
        except CAUGHT as exc:
            msg = str(exc) if f.name in str(exc) else f"{f.name}: {exc}"
            row.update({"status": "error", "message": msg})
            log.error("%s", msg)
        rows.append(row)
    table = pd.DataFrame(rows)
    outputs: list = []
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        table.to_csv(summary_path, index=False, encoding="utf-8")
        meta = {"tool": "tsd_dsn", "version": __version__, "created_at": datetime.now().isoformat(timespec="seconds"),
                "n_files": len(files), "n_ok": int((table["status"] == "ok").sum()), "n_error": int((table["status"] == "error").sum()),
                "temperature": {k: getattr(cfg.temperature, k) for k in ("sample_m", "window_m", "gps_time_basis", "depth_cm", "calibration")},
                "fwd_scale": {"to_fwd_multiplier": cfg.fwd_scale.to_fwd_multiplier,
                              "to_fwd_conversion_csv": cfg.fwd_scale.to_fwd_conversion_csv}}
        meta_path = out_dir / "batch_meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        outputs = [summary_path, meta_path]
    return {"table": table, "outputs": outputs, "n_ok": int(table["status"].isin(["ok", "dry_run_ok"]).sum()),
            "n_error": int((table["status"] == "error").sum())}
