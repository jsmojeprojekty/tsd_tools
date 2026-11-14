"""Konfiguracja narzedzia fwd_fit (opcjonalny modul N1: dopasowanie wspolczynnikow z wlasnych wizyt)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, OutputConfig, _build, _choice, load_yaml

FIT_INDICATORS = ["D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800", "SCI300", "BDI", "BCI"]


@dataclass
class FitInput:
    visits: str = ""                      # CSV lub XLSX: jedna wizyta = jeden wiersz
    point_col: str = "point_code"         # identyfikator punktu pomiarowego
    date_col: str = "date"                # data wizyty (RRRR-MM-DD)
    t_col: str = "t_mid_met"              # temperatura T_mid [C]
    exclude_if_true: list = field(default_factory=list)   # kolumny logiczne: wiersze z 1/TRUE odrzucone (np. excl_frost)
    require_true: list = field(default_factory=list)      # kolumny logiczne: wiersze z 0/FALSE odrzucone (np. has_met)


@dataclass
class FitSettings:
    indicators: list = field(default_factory=lambda: list(FIT_INDICATORS))
    t_range_c: list = field(default_factory=lambda: [5.0, 30.0])
    k_bounds: list = field(default_factory=lambda: [-0.08, 0.08])
    min_n: int = 30
    n_boot: int = 500
    scope_label: str = "lacznie"


@dataclass
class FitConfig:
    tool: str = "fwd_fit"
    schema_version: int = 1
    log_level: str = "INFO"
    input: FitInput = field(default_factory=FitInput)
    fit: FitSettings = field(default_factory=FitSettings)
    output: OutputConfig = field(default_factory=OutputConfig)
    base_dir: str = "."


def build_fit_config(data: dict, base_dir=".") -> FitConfig:
    cfg = _build(FitConfig, data, "config")
    cfg.base_dir = str(base_dir)
    _choice(cfg.tool, ("fwd_fit", "n1fit"), "tool")
    if not cfg.input.visits:
        raise ConfigError("input.visits: podaj plik z wizytami (CSV/XLSX)")
    if len(cfg.fit.t_range_c) != 2 or not cfg.fit.t_range_c[0] < cfg.fit.t_range_c[1]:
        raise ConfigError("fit.t_range_c: oczekiwano [dolna, gorna], dolna < gorna")
    if len(cfg.fit.k_bounds) != 2 or not cfg.fit.k_bounds[0] < cfg.fit.k_bounds[1]:
        raise ConfigError("fit.k_bounds: oczekiwano [dolna, gorna], dolna < gorna")
    if cfg.fit.n_boot < 0 or cfg.fit.min_n < 5:
        raise ConfigError("fit.n_boot >= 0 oraz fit.min_n >= 5")
    return cfg


def load_fit_config(path) -> FitConfig:
    path = Path(path)
    return build_fit_config(load_yaml(path), base_dir=path.resolve().parent)
