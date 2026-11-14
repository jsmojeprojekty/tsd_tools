"""Odczyt eksportu TSD w wariancie B_1510off (`*.raw.sup.txt`).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\b1510off_v4_import.py (parse_raw_sup_txt, classify_file), w2_euler.py (strip_unit),
stan c67f7fe / 2026-10-19. Zmiany: bez zrownania blokami z pgc i bez zapisu do bazy (specyfika projektu bazy).

Format: sekcje `Headers:` / `Parameters:` / `Data:`, separator ', ', jednostki w nazwach kolumn ('Chainage [m]'); ugiecia D*
zapisane z ujemnym znakiem (znak zdejmowany); GPS (Latitude, Longitude, GPS time hhmmss) w pliku. Data przejazdu z nazwy pliku
(`T4RRRRMMDDNNNN`)."""

from __future__ import annotations

import datetime as dt
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .constants import D_COLS, MIN_YEAR_B1510OFF, SLOPE_COL
from .flags import TsdFlag

_UNIT_RE = re.compile(r"\s*\[[^\]]*\]\s*$")
_NAME_DATE_RE = re.compile(r"T4(\d{4})(\d{2})(\d{2})(\d{4})")


@dataclass
class TsdRun:
    source: str
    meta: dict
    data: pd.DataFrame                    # kolumny bez jednostek, d0 i D* z dodatnim znakiem
    date: dt.date | None
    n_bad_rows: int = 0
    file_flags: int = 0
    notes: list = field(default_factory=list)


def strip_unit(name: str) -> str:
    return _UNIT_RE.sub("", name).strip()


def date_from_name(name: str) -> dt.date | None:
    m = _NAME_DATE_RE.search(name)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def gps_time_to_seconds(values) -> np.ndarray:
    """'GPS time' w formacie hhmmss (liczba, np. 163752.0) -> sekundy od polnocy."""
    v = np.asarray(values, dtype=float)
    hh = np.floor(v / 10000.0)
    mm = np.floor((v - hh * 10000.0) / 100.0)
    ss = v - hh * 10000.0 - mm * 100.0
    return hh * 3600.0 + mm * 60.0 + ss


def read_b1510off(path, expected_step_m: float = 1.0) -> TsdRun:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku TSD: {path}")
    with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
        lines = fh.readlines()
    meta = {}
    hdr_i = None
    for i, line in enumerate(lines):
        s = line.rstrip("\r\n")
        if s == "Data:":
            hdr_i = i
            break
        if s in ("Headers:", "Parameters:", ""):
            continue
        if ":" in s:
            k, _, v = s.partition(":")
            meta[k.strip()] = v.strip()
    if hdr_i is None or hdr_i + 1 >= len(lines):
        raise ValueError(f"{path.name}: brak sekcji 'Data:' w naglowku (nie jest to eksport TSD *.raw.sup.txt)")
    names = [strip_unit(c) for c in lines[hdr_i + 1].rstrip("\r\n").split(", ")]
    if "Chainage" not in names or "Goodness of fit" not in names:
        raise ValueError(f"{path.name}: brak kolumny Chainage lub Goodness of fit - format odbiega od opisu")
    ncol = len(names)
    body = [ln.rstrip("\r\n") for ln in lines[hdr_i + 2:] if ln.strip()]
    good = [ln for ln in body if ln.count(", ") == ncol - 1]
    n_bad = len(body) - len(good)
    df = pd.read_csv(io.StringIO("\n".join(g.replace(", ", ",") for g in good)), header=None, names=names,
                     na_values=[""], low_memory=False)
    for c in D_COLS:
        if c in df:
            df[c] = -df[c]                                       # w pliku D* ujemne (konwencja raw.sup)
    flags = 0
    notes = []
    if not meta.get("Re-calibrationfile", "").strip():
        flags |= int(TsdFlag.FILE_NOT_RECALIBRATED)
        notes.append("pusty 'Re-calibrationfile' - to nie jest przeliczenie B_1510off")
    missing = sorted(set(SLOPE_COL) - {k for k, c in SLOPE_COL.items() if c in df})
    if missing:
        flags |= int(TsdFlag.FILE_MISSING_CHANNEL)
        notes.append(f"brak kanalow nachylen: {missing}")
    chain = df["Chainage"].to_numpy(float)
    step = float(np.nanmedian(np.diff(chain))) if len(chain) > 2 else float("nan")
    if not np.isfinite(step) or abs(step - expected_step_m) > 0.05 * expected_step_m:
        flags |= int(TsdFlag.FILE_SCALE_SUSPECT)
        notes.append(f"krok pikietazu {step:.3f} m (oczekiwano {expected_step_m:g} m)")
    date = date_from_name(path.name)
    if date is not None and date.year < MIN_YEAR_B1510OFF:
        flags |= int(TsdFlag.FILE_YEAR_OUT_OF_RANGE)
        notes.append(f"rok {date.year}: B_1510off dotyczy przejazdow od {MIN_YEAR_B1510OFF}")
    if n_bad:
        notes.append(f"pominieto {n_bad} wierszy o blednej liczbie kolumn")
    data = pd.DataFrame({
        "chainage_m": df["Chainage"],
        "speed_ms": df.get("Driving Speed"),
        "temp_road": df.get("Temp Road"),
        "temp_air": df.get("Temp Air"),
        "strain_right_kg": df.get("Strain Gauge Right"),
        "gyro_yaw": df.get("GyroYaw"),
        "d0": df.get("D0"),
        "gof": df["Goodness of fit"],
        "lat": df.get("Latitude"),
        "lon": df.get("Longitude"),
        "gps_time_s": gps_time_to_seconds(df["GPS time"]) if "GPS time" in df else np.nan,
    })
    for key, col in SLOPE_COL.items():
        data[f"slope_{key}"] = df[col] if col in df else np.nan
    return TsdRun(source=str(path), meta=meta, data=data, date=date, n_bad_rows=n_bad, file_flags=flags, notes=notes)
