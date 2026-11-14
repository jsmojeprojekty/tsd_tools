"""Odczyt plikow FWD: eksport XLSX (Drops + Stations), Dynatest MDB (tylko odczyt, ODBC) i generyczny CSV.

Wspolny model wewnetrzny:
  stations: session_id, station_id, station_km, time, latitude, longitude, asphalt_temp, surface_temp, air_temp
  drops:    station_id, drop_id, non_seating (bool), force_kn, stress_kpa, d1..d9 [um]
  sessions: slownik session_id -> {'trailer', 'date', 'x_mm' (9 odleglosci geofonow [mm] lub None)}

Konwencja zrodlowa (bak/e2b2_values.py): zrzut z historii (History = TRUE) to zrzut nieosadczy; osadczy (is_seating)
to zrzut z History = FALSE. Eksport XLSX nie zawiera polozen geofonow — przyjmowany jest uklad standardowy."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..common.constants import SENTINEL_MIN

log = logging.getLogger(__name__)

D_COLS = [f"d{i}" for i in range(1, 10)]


@dataclass
class FwdData:
    source: str
    fmt: str
    stations: pd.DataFrame
    drops: pd.DataFrame
    sessions: dict = field(default_factory=dict)


def detect_format(path, stations_path=None) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in (".mdb", ".accdb"):
        return "mdb"
    if suffix == ".xlsx":
        return "xlsx_drops_stations"
    if suffix == ".csv":
        return "csv_generic"
    raise ValueError(f"nie rozpoznano formatu pliku FWD: {path}")


def read_fwd(path, fmt: str = "auto", stations_path=None) -> FwdData:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku FWD: {path}")
    if fmt == "auto":
        fmt = detect_format(path, stations_path)
    if fmt == "xlsx_drops_stations":
        return _read_xlsx_pair(path, Path(stations_path) if stations_path else None)
    if fmt == "mdb":
        return _read_mdb(path)
    if fmt == "csv_generic":
        return _read_csv_generic(path)
    raise ValueError(f"nieznany format wejscia: {fmt!r}")


def _excel_time(series: pd.Series) -> pd.Series:
    """Czas jako datetime; liczby traktowane jako numery dni Excela (poczatek 1899-12-30)."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def _clean_temp(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Temperatura bez wypelniaczy eksportu (float32 min ~ -3,4e38): zwraca (wartosc lub NaN, maska wypelniacza)."""
    values = pd.to_numeric(series, errors="coerce").astype(float)
    sentinel = values < SENTINEL_MIN
    values = values.where(~sentinel, np.nan)
    return values, sentinel


def _finalize(stations: pd.DataFrame, drops: pd.DataFrame, sessions: dict, source: str, fmt: str) -> FwdData:
    for col in ("asphalt_temp", "surface_temp", "air_temp"):
        if col in stations:
            stations[col], mask = _clean_temp(stations[col])
            stations[f"{col}_sentinel"] = mask
    for col in D_COLS + ["force_kn"]:
        if col in drops:
            drops[col] = pd.to_numeric(drops[col], errors="coerce").astype(float)
    stations = stations.sort_values(["session_id", "time", "station_id"], kind="stable").reset_index(drop=True)
    drops = drops.sort_values(["station_id", "drop_id"], kind="stable").reset_index(drop=True)
    return FwdData(source=source, fmt=fmt, stations=stations, drops=drops, sessions=sessions)


def _read_xlsx_pair(drops_path: Path, stations_path: Path | None) -> FwdData:
    sheets = pd.read_excel(drops_path, sheet_name=None)
    dr = sheets.get("Drops", next(iter(sheets.values())))
    drops = pd.DataFrame({
        "station_id": dr["StationID"].astype(int),
        "drop_id": dr["DropID"].astype(int),
        "non_seating": dr["History"].astype(str).str.upper().isin(["TRUE", "PRAWDA", "1", "TAK"]),
        "force_kn": dr["Force"],
        "stress_kpa": dr["Stress"] if "Stress" in dr else np.nan,
    })
    for i, col in enumerate(D_COLS, 1):
        drops[col] = dr[f"D{i}"]
    if stations_path is not None:
        ss = pd.read_excel(stations_path, sheet_name=None)
        st = ss.get("Stations", next(iter(ss.values())))
        stations = pd.DataFrame({
            "session_id": st["SessionID"] if "SessionID" in st else 1,
            "station_id": st["StationID"].astype(int),
            "station_km": st["Station"] if "Station" in st else np.nan,
            "time": _excel_time(st["Time"]),
            "latitude": st["Latitude"] if "Latitude" in st else np.nan,
            "longitude": st["Longitude"] if "Longitude" in st else np.nan,
            "asphalt_temp": st["AsphaltTemperature"],
            "surface_temp": st["SurfaceTemperature"] if "SurfaceTemperature" in st else np.nan,
            "air_temp": st["AirTemperature"] if "AirTemperature" in st else np.nan,
        })
    else:
        log.warning("brak pliku Stations dla %s: stacje zbudowane z Drops (temperatury z kolumn Asphalt/Surface/Air)",
                    drops_path.name)
        first = dr.sort_values(["StationID", "DropID"]).drop_duplicates("StationID")
        stations = pd.DataFrame({
            "session_id": 1,
            "station_id": first["StationID"].astype(int).values,
            "station_km": np.nan,
            "time": _excel_time(first["DateTime"]).values if "DateTime" in first else pd.NaT,
            "latitude": np.nan,
            "longitude": np.nan,
            "asphalt_temp": first["Asphalt"].values if "Asphalt" in first else np.nan,
            "surface_temp": first["Surface"].values if "Surface" in first else np.nan,
            "air_temp": first["Air"].values if "Air" in first else np.nan,
        })
    sessions = {int(s): {"trailer": None, "date": None, "x_mm": None} for s in stations["session_id"].unique()}
    return _finalize(stations, drops, sessions, str(drops_path), "xlsx_drops_stations")


def _mdb_connect(path: Path):
    try:
        import pyodbc
    except ImportError as exc:  # pragma: no cover - zalezy od srodowiska
        raise RuntimeError("odczyt MDB wymaga pakietu pyodbc (pip install tsdfwd-tools[mdb])") from exc
    driver = "Microsoft Access Driver (*.mdb, *.accdb)"
    if driver not in pyodbc.drivers():
        raise RuntimeError(f"brak sterownika ODBC '{driver}' (wymagany do odczytu plikow MDB)")
    conn_str = f"DRIVER={{{driver}}};DBQ={path};ReadOnly=1;"
    return pyodbc.connect(conn_str, autocommit=True, readonly=True)


def _query(conn, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    return pd.DataFrame.from_records([tuple(r) for r in cur.fetchall()], columns=cols)


def _read_mdb(path: Path) -> FwdData:
    conn = _mdb_connect(path)
    try:
        st = _query(conn, "SELECT SessionID, StationID, Station, AsphaltTemperature, SurfaceTemperature, "
                         "AirTemperature, [Time], Latitude, Longitude FROM Stations")
        dr = _query(conn, "SELECT StationID, DropID, History, Stress, Force, D1, D2, D3, D4, D5, D6, D7, D8, D9 "
                         "FROM Drops")
        se = _query(conn, "SELECT SessionID, Trailer, [Date], X1, X2, X3, X4, X5, X6, X7, X8, X9 FROM Sessions")
    finally:
        conn.close()
    drops = pd.DataFrame({
        "station_id": dr["StationID"].astype(int),
        "drop_id": dr["DropID"].astype(int),
        "non_seating": dr["History"].astype(str).str.upper().isin(["TRUE", "PRAWDA", "1", "TAK"]),
        "force_kn": dr["Force"],
        "stress_kpa": dr["Stress"],
    })
    for i, col in enumerate(D_COLS, 1):
        drops[col] = dr[f"D{i}"]
    stations = pd.DataFrame({
        "session_id": st["SessionID"].astype(int),
        "station_id": st["StationID"].astype(int),
        "station_km": st["Station"],
        "time": _excel_time(st["Time"]),
        "latitude": st["Latitude"],
        "longitude": st["Longitude"],
        "asphalt_temp": st["AsphaltTemperature"],
        "surface_temp": st["SurfaceTemperature"],
        "air_temp": st["AirTemperature"],
    })
    sessions = {}
    for _, row in se.iterrows():
        x = tuple(float(row[f"X{i}"]) for i in range(1, 10))
        sessions[int(row["SessionID"])] = {"trailer": str(row["Trailer"]).strip() or None,
                                           "date": row["Date"], "x_mm": x}
    return _finalize(stations, drops, sessions, str(path), "mdb")


def _read_csv_generic(path: Path) -> FwdData:
    """CSV: jeden wiersz = jeden zrzut. Wymagane: station_id, force_kn, d1..d9. Opcjonalne: session_id, drop_id,
    non_seating, time, latitude, longitude, asphalt_temp, surface_temp, air_temp, station_km."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = [c for c in ["station_id", "force_kn"] + D_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV {path.name}: brak wymaganych kolumn {missing}")
    df = df.copy()
    if "drop_id" not in df:
        df["drop_id"] = df.groupby("station_id").cumcount() + 1
    if "non_seating" not in df:
        df["non_seating"] = True
    df["non_seating"] = df["non_seating"].astype(str).str.upper().isin(["TRUE", "1", "PRAWDA", "TAK"])
    if "session_id" not in df:
        df["session_id"] = 1
    drops = df[["station_id", "drop_id", "non_seating", "force_kn"] + D_COLS].copy()
    drops["stress_kpa"] = df["stress_kpa"] if "stress_kpa" in df else np.nan
    drops["station_id"] = drops["station_id"].astype(int)
    drops["drop_id"] = drops["drop_id"].astype(int)
    first = df.sort_values(["station_id", "drop_id"]).drop_duplicates("station_id")
    stations = pd.DataFrame({
        "session_id": first["session_id"].astype(int).values,
        "station_id": first["station_id"].astype(int).values,
        "station_km": first["station_km"].values if "station_km" in first else np.nan,
        "time": _excel_time(first["time"]).values if "time" in first else pd.NaT,
        "latitude": first["latitude"].values if "latitude" in first else np.nan,
        "longitude": first["longitude"].values if "longitude" in first else np.nan,
        "asphalt_temp": first["asphalt_temp"].values if "asphalt_temp" in first else np.nan,
        "surface_temp": first["surface_temp"].values if "surface_temp" in first else np.nan,
        "air_temp": first["air_temp"].values if "air_temp" in first else np.nan,
    })
    sessions = {int(s): {"trailer": None, "date": None, "x_mm": None} for s in stations["session_id"].unique()}
    return _finalize(stations, drops, sessions, str(path), "csv_generic")
