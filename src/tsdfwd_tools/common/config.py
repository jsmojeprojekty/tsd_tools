"""Konfiguracja YAML narzedzi: dataclasses z wartosciami domyslnymi z raportu i walidacja kluczy."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .constants import (
    INDICES_MAX_C,
    LOAD_REF_KN,
    PLACEHOLDER_TEMPS_C,
    RANGE_A_C,
    RANGE_B_C,
    RANGE_LEGACY_C,
    T_REF_C,
)


class ConfigError(ValueError):
    """Blad konfiguracji (nieznany klucz, zla wartosc, brak wymaganego pola)."""


@dataclass
class N1Input:
    files: list = field(default_factory=list)
    stations_files: list = field(default_factory=list)
    format: str = "auto"                  # auto | xlsx_drops_stations | mdb | csv_generic
    drop_rule: str = "mean_nonseating"    # mean_nonseating | second_drop | last_nonseating
    geophone_mapping: str = "by_x"        # by_x (po x1..x9 sesji, gdy sa w pliku) | standard_layout


@dataclass
class N1Temperature:
    source: str = "column"                # column | constant | csv_join
    column: str = "asphalt_temp"          # kolumna T_mid w danych stacji (lub w csv)
    csv: str | None = None
    constant_c: float | None = None
    depth_cm: float | None = 12.0
    thickness_cm: float | None = None
    max_age_min: float = 60.0


@dataclass
class N1Correction:
    variant: str = "B"                    # A | B | legacy
    coefficient_set: str = "e2a3_full"    # e2a3_full | tab71
    road_type: str = "public"             # public | highway (tylko variant: legacy)
    ranges_c: dict = field(default_factory=lambda: {
        "A": list(RANGE_A_C), "B": list(RANGE_B_C), "legacy": list(RANGE_LEGACY_C)})
    indices_max_c: float = INDICES_MAX_C
    t_ref_c: float = T_REF_C
    load_ref_kn: float = LOAD_REF_KN
    force_tolerance_pct: float = 10.0
    placeholder_temps_c: list = field(default_factory=lambda: list(PLACEHOLDER_TEMPS_C))


@dataclass
class OutputConfig:
    dir: str = "wyniki"
    formats: list = field(default_factory=lambda: ["csv"])
    per_station_file: bool = True
    summary: bool = True
    overwrite: bool = False


@dataclass
class N1Config:
    tool: str = "fwd_tempcorr"
    schema_version: int = 1
    log_level: str = "INFO"
    input: N1Input = field(default_factory=N1Input)
    temperature: N1Temperature = field(default_factory=N1Temperature)
    correction: N1Correction = field(default_factory=N1Correction)
    output: OutputConfig = field(default_factory=OutputConfig)
    base_dir: str = "."                   # katalog pliku konfiguracji (do rozwiazywania sciezek wzglednych)


def load_yaml(path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"brak pliku konfiguracji: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"konfiguracja {path} musi byc mapa klucz: wartosc")
    return data


def _build(cls, data, where: str):
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError(f"sekcja {where!r} musi byc mapa klucz: wartosc")
    known = {f.name: f for f in dataclasses.fields(cls)}
    unknown = sorted(set(data) - set(known))
    if unknown:
        raise ConfigError(f"nieznane klucze w sekcji {where!r}: {unknown} (dozwolone: {sorted(known)})")
    kwargs = {}
    for name, value in data.items():
        ftype = known[name].default_factory() if known[name].default_factory is not dataclasses.MISSING else None
        if dataclasses.is_dataclass(ftype):
            kwargs[name] = _build(type(ftype), value, f"{where}.{name}")
        else:
            kwargs[name] = value
    return cls(**kwargs)


def build_n1_config(data: dict, base_dir=".") -> N1Config:
    cfg = _build(N1Config, data, "config")
    cfg.base_dir = str(base_dir)
    _validate_n1(cfg)
    return cfg


def load_n1_config(path) -> N1Config:
    path = Path(path)
    return build_n1_config(load_yaml(path), base_dir=path.resolve().parent)


def resolve_path(value, base_dir) -> Path:
    p = Path(str(value))
    return p if p.is_absolute() else Path(base_dir) / p


def _choice(value, allowed, where):
    if value not in allowed:
        raise ConfigError(f"{where}: {value!r} niedozwolone (dozwolone: {', '.join(map(str, allowed))})")


def _validate_n1(cfg: N1Config) -> None:
    _choice(cfg.tool, ("fwd_tempcorr", "n1"), "tool")
    _choice(cfg.input.format, ("auto", "xlsx_drops_stations", "mdb", "csv_generic"), "input.format")
    _choice(cfg.input.drop_rule, ("mean_nonseating", "second_drop", "last_nonseating"), "input.drop_rule")
    _choice(cfg.input.geophone_mapping, ("by_x", "standard_layout"), "input.geophone_mapping")
    _choice(cfg.temperature.source, ("column", "constant", "csv_join"), "temperature.source")
    _choice(cfg.correction.variant, ("A", "B", "legacy"), "correction.variant")
    _choice(cfg.correction.coefficient_set, ("e2a3_full", "tab71"), "correction.coefficient_set")
    _choice(cfg.correction.road_type, ("public", "highway"), "correction.road_type")
    for fmt in cfg.output.formats:
        _choice(fmt, ("csv", "xlsx"), "output.formats")
    if cfg.temperature.source == "constant" and cfg.temperature.constant_c is None:
        raise ConfigError("temperature.constant_c jest wymagane przy temperature.source: constant")
    if cfg.temperature.source == "csv_join" and not cfg.temperature.csv:
        raise ConfigError("temperature.csv jest wymagane przy temperature.source: csv_join")
    if not cfg.input.files:
        raise ConfigError("input.files: podaj co najmniej jeden plik wejsciowy")
    if cfg.input.stations_files and len(cfg.input.stations_files) != len(cfg.input.files):
        raise ConfigError("input.stations_files musi miec tyle samo elementow co input.files (pary Drops/Stations)")
    for key in ("A", "B", "legacy"):
        rng = cfg.correction.ranges_c.get(key)
        if rng is None or len(rng) != 2 or not rng[0] < rng[1]:
            raise ConfigError(f"correction.ranges_c.{key}: oczekiwano [dolna, gorna], dolna < gorna")
    if cfg.correction.load_ref_kn <= 0:
        raise ConfigError("correction.load_ref_kn musi byc dodatnie")
