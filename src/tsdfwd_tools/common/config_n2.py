"""Konfiguracja narzedzia layer_temp (N2): temperatura warstwy asfaltowej z fizyki 1-D i kalibracji jednorazowej do pirometru."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, _build, _choice, load_yaml


@dataclass
class N2Input:
    survey_csv: str | None = None                         # tabela pomiarow: czas, pozycja, odczyt pirometru
    time_column: str = "measured_at_local"                # czas lokalny naiwny z DST (jak FWD)
    lat_column: str = "latitude"
    lon_column: str = "longitude"
    ir_column: str = "t_surface"                          # pirometr (temperatura powierzchni) [C]
    air_column: str | None = "t_air"                      # opcjonalna; NIE wchodzi do modelu (kopiowana do wyniku)
    id_column: str | None = None
    passthrough: list = field(default_factory=list)       # dodatkowe kolumny kopiowane do wyniku (np. chainage_m, file)
    time_basis: str = "local_Europe_Warsaw_DST"
    encoding: str = "utf-8-sig"
    sep: str = ","


@dataclass
class N2Model:
    depth_cm: float = 12.0                                # glebokosc [cm], siatka 1 cm, 0-50
    thickness_cm: float | None = None                     # gdy podane: glebokosc = grubosc/2 ("polowa pakietu")
    params_file: str = "builtin:params_TN.json"           # parametry zamrozone (alpha, EB, beta50, beta_ir)
    terrain_class: str = "open"                           # open (TN); shaded: TODO (Q-N2-7)
    calibration: str = "single_shot_ir_mass"              # single_shot_ir_mass | none (fizyka bez kalibracji)


@dataclass
class N2Meteo:
    provider: str = "open_meteo_archive"
    cache_dir: str | None = None                          # katalog cache (parquet lub csv z .json); wymagany
    offline: bool = False                                 # true = tylko cache, bez polaczen sieciowych
    grid_deg: float = 0.05
    history_days: int = 35


@dataclass
class N2Qc:
    season_months: list = field(default_factory=lambda: [4, 5, 6, 7, 8, 9, 10])
    snow_depth_max_m: float = 0.005
    night_sw_wm2: float = 5.0


@dataclass
class N2Comparators:
    bells3: bool = False                                  # tylko BELLS3 klasyczny (nigdy BT/O)


@dataclass
class N2Output:
    dir: str = "wyniki"
    overwrite: bool = False
    name: str = "layer_temp"                              # nazwa pliku wynikowego (bez rozszerzenia)


@dataclass
class N2Config:
    tool: str = "layer_temp"
    schema_version: int = 1
    log_level: str = "INFO"
    input: N2Input = field(default_factory=N2Input)
    model: N2Model = field(default_factory=N2Model)
    meteo: N2Meteo = field(default_factory=N2Meteo)
    qc: N2Qc = field(default_factory=N2Qc)
    comparators: N2Comparators = field(default_factory=N2Comparators)
    output: N2Output = field(default_factory=N2Output)
    base_dir: str = "."


def build_n2_config(data: dict, base_dir=".") -> N2Config:
    cfg = _build(N2Config, data, "config")
    cfg.base_dir = str(base_dir)
    _choice(cfg.tool, ("layer_temp", "n2"), "tool")
    if not cfg.input.survey_csv:
        raise ConfigError("input.survey_csv: podaj plik CSV z pomiarami (czas, pozycja, odczyt pirometru)")
    _choice(cfg.input.time_basis, ("local_Europe_Warsaw_DST",), "input.time_basis")
    m = cfg.model
    _choice(m.calibration, ("single_shot_ir_mass", "none"), "model.calibration")
    _choice(m.terrain_class, ("open",), "model.terrain_class")
    depth = m.thickness_cm / 2.0 if m.thickness_cm else m.depth_cm
    if m.thickness_cm is not None and m.thickness_cm <= 0:
        raise ConfigError("model.thickness_cm musi byc dodatnie")
    if not 0.0 <= depth <= 50.0:
        raise ConfigError(f"glebokosc {depth} cm poza zakresem 0-50 cm (siatka symulacji)")
    _choice(cfg.meteo.provider, ("open_meteo_archive",), "meteo.provider")
    if not cfg.meteo.cache_dir:
        raise ConfigError("meteo.cache_dir: podaj katalog cache danych Open-Meteo (wyniki pobierania; przy offline: true tylko odczyt)")
    if cfg.meteo.grid_deg <= 0:
        raise ConfigError("meteo.grid_deg musi byc dodatnie")
    if cfg.meteo.history_days < 31:
        raise ConfigError("meteo.history_days >= 31 (srednia 30-dobowa dolnego warunku brzegowego)")
    if not cfg.qc.season_months or any(not 1 <= int(x) <= 12 for x in cfg.qc.season_months):
        raise ConfigError("qc.season_months: lista miesiecy 1-12")
    return cfg


def effective_depth_cm(cfg: N2Config) -> float:
    m = cfg.model
    return float(m.thickness_cm) / 2.0 if m.thickness_cm else float(m.depth_cm)


def load_n2_config(path) -> N2Config:
    path = Path(path)
    return build_n2_config(load_yaml(path), base_dir=path.resolve().parent)
