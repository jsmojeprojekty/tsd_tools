"""Konfiguracja narzedzia tsd_dsn: katalog przejazdow TSD (B_1510off) -> temperatura warstwy (N2) -> N3 -> XML DSN w skali FWD.

Narzedzie jest nakladka na N2 i N3 (ich ustawienia przechodza bez zmian w sekcjach `processing`, `qc`, `xml`); nowe sa tylko:
tabela przejazdow (dane opisowe odcinka), wybor probek temperatury z pliku TSD i zapis wynikow per przejazd."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, _build, _choice, load_yaml


@dataclass
class DsnInput:
    tsd_dir: str | None = None                            # katalog z eksportami B_1510off (bez podkatalogow)
    tsd_files: list = field(default_factory=list)         # albo lista plikow
    patterns: list = field(default_factory=lambda: ["*.raw.sup.txt", "*.raw.sup.xls", "*.raw.sup.xlsx"])
    trips_csv: str | None = None                          # tabela przejazdow: plik, kod_oddz, rok, droga, jezdnia, pas, km_start [, ...]


@dataclass
class DsnTemperature:
    sample_m: float = 100.0                               # odstep probek pirometru wzdluz przejazdu (N2 liczy dla probek, N3 interpoluje po pikietazu)
    window_m: float = 5.0                                 # mediana pirometru i powietrza w oknie +-window_m wokol probki
    gps_time_basis: str = "utc"                           # utc | local: czas z kolumny 'GPS time' (hhmmss); N2 wymaga czasu lokalnego
    depth_cm: float = 12.0
    calibration: str = "single_shot_ir_mass"              # single_shot_ir_mass | none
    meteo_cache_dir: str | None = None                    # katalog cache Open-Meteo (wymagany)
    meteo_offline: bool = False                           # true = tylko cache, bez polaczen sieciowych


@dataclass
class DsnFwdScale:
    to_fwd_multiplier: float | None = None                # przelicznik TSD->FWD (BEZ wartosci domyslnej; zmienia sie po kalibracji)
    to_fwd_conversion_csv: str | None = None              # albo conversion.csv z N4 dla okresu kalibracji


@dataclass
class DsnOutput:
    dir: str = "wyniki_dsn"
    overwrite: bool = False


@dataclass
class DsnConfig:
    tool: str = "tsd_dsn"
    schema_version: int = 1
    log_level: str = "INFO"
    input: DsnInput = field(default_factory=DsnInput)
    temperature: DsnTemperature = field(default_factory=DsnTemperature)
    fwd_scale: DsnFwdScale = field(default_factory=DsnFwdScale)
    processing: dict = field(default_factory=dict)        # jak N3 `processing` (okna, Hampel, aggregate_m, position_offset_m, ...)
    qc: dict = field(default_factory=dict)                # jak N3 `qc`
    xml: dict = field(default_factory=dict)               # jak N3 `xml_uc` (step_m, schema_location, km_direction, ...); pola odcinka z tabeli przejazdow
    output: DsnOutput = field(default_factory=DsnOutput)
    base_dir: str = "."


def build_dsn_config(data: dict, base_dir=".") -> DsnConfig:
    cfg = _build(DsnConfig, data, "config")
    cfg.base_dir = str(base_dir)
    _choice(cfg.tool, ("tsd_dsn", "dsn"), "tool")
    i = cfg.input
    if bool(i.tsd_dir) == bool(i.tsd_files):
        raise ConfigError("input: podaj dokladnie jedno z: tsd_dir (katalog z przejazdami) albo tsd_files (lista plikow)")
    if not i.trips_csv:
        raise ConfigError("input.trips_csv: podaj tabele przejazdow (plik, kod_oddz, rok, droga, jezdnia, pas, km_start); "
                          "dane odcinka nie maja wartosci domyslnych")
    t = cfg.temperature
    _choice(t.gps_time_basis, ("utc", "local"), "temperature.gps_time_basis")
    _choice(t.calibration, ("single_shot_ir_mass", "none"), "temperature.calibration")
    if t.sample_m <= 0 or t.window_m <= 0:
        raise ConfigError("temperature.sample_m i temperature.window_m musza byc dodatnie")
    if not t.meteo_cache_dir:
        raise ConfigError("temperature.meteo_cache_dir: podaj katalog cache danych Open-Meteo")
    f = cfg.fwd_scale
    if f.to_fwd_multiplier is not None and f.to_fwd_conversion_csv:
        raise ConfigError("fwd_scale: podaj albo to_fwd_multiplier, albo to_fwd_conversion_csv (nie oba)")
    if f.to_fwd_multiplier is None and not f.to_fwd_conversion_csv and cfg.xml.get("scale", "fwd") == "fwd":
        raise ConfigError("fwd_scale: XML w skali FWD wymaga to_fwd_multiplier albo to_fwd_conversion_csv (przelicznik z N4 dla okresu "
                          "kalibracji; nie ma wartosci domyslnej); skala TSD: xml.scale: tsd")
    for sec in ("processing", "qc", "xml"):
        if not isinstance(getattr(cfg, sec), dict):
            raise ConfigError(f"sekcja {sec!r} musi byc mapa klucz: wartosc")
    return cfg


def load_dsn_config(path) -> DsnConfig:
    path = Path(path)
    return build_dsn_config(load_yaml(path), base_dir=path.resolve().parent)
