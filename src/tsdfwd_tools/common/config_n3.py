"""Konfiguracja narzedzia tsd_network (N3): przetwarzanie eksportu TSD B_1510off na sieci i eksport XML DSN (UC)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, _build, _choice, load_yaml
from .constants import T_REF_C


@dataclass
class N3Input:
    tsd_files: list = field(default_factory=list)       # *.raw.sup.txt (eksport B_1510off)
    format: str = "b1510off_txt"
    expected_step_m: float = 1.0                         # krok pikietazu (kontrola skali)


@dataclass
class N3LayerTemp:
    source: str = "csv"                                  # csv (wynik N2 / model) | constant | none
    csv: str | None = None                               # kolumny: chainage_m, t12_c [, file]
    column: str = "t12_c"
    pos_column: str = "chainage_m"
    file_column: str = "file"
    constant_c: float | None = None
    allow_uncorrected: bool = False                      # source: none -> d0 bez korekty (flaga T_MISSING)


@dataclass
class N3Hampel:
    enabled: bool = True
    window_m: float = 10.0                               # +-10 m (21 wierszy przy kroku 1 m)
    k: float = 3.0                                       # prog = k * 1,4826 * MAD okna


@dataclass
class N3Correction:
    beta_pct: float | None = None                        # domyslnie beta D0 z zestawu e2a3_full (1,60415 %/C)
    range_c: list = field(default_factory=lambda: [5.0, 30.0])
    t_ref_c: float = T_REF_C


@dataclass
class N3Processing:
    integral_step_m: float = 0.001
    window_m: float = 5.0                                # +-5 m (dopuszczalnie 10)
    min_rows_in_window: int = 3
    gof_threshold: float = 0.5                           # atrybut okna (udzial czasz GoF >= 0,5)
    aggregate_m: list = field(default_factory=lambda: [50, 100])
    position_offset_m: float = 0.0                       # przesuniecie polozenia ugiec wzgledem pikietazu (konwencja w E2b)
    hampel: N3Hampel = field(default_factory=N3Hampel)
    correction: N3Correction = field(default_factory=N3Correction)
    to_fwd_scale_enabled: bool = False                   # dodatkowe kolumny w skali FWD
    to_fwd_multiplier: float = 1.62


@dataclass
class N3QC:
    gps_gyro: bool = True
    r_min: float = 0.5
    omega_std_min: float = 0.0017
    window_rows: list = field(default_factory=lambda: [-10, -2])


@dataclass
class N3Xml:
    enabled: bool = False
    profile: str = "dsn_h42"                             # dsn_h42 (zal. H p. 4.2, 21 pol)
    kod_oddz: str | None = None                          # wymagane przy enabled
    rok: str | int | None = None
    droga: str | int | None = None
    jezdnia: str | int | None = None
    pas: str | int | None = None
    step_m: int = 10
    km_start: float | None = None                        # KM w punkcie chainage_start_m (wymagane przy enabled)
    km_direction: str = "increasing"                     # increasing | decreasing (KM wraz z pikietazem)
    chainage_start_m: float = 0.0
    schema_location: str = "UC_Schema.xsd"
    scale: str = "tsd"                                   # tsd | fwd (mnoznik tylko opcjonalnie)
    date_override: str | None = None                     # RRRR-MM-DD, gdy brak daty w nazwie pliku


@dataclass
class N3Output:
    dir: str = "wyniki"
    rows_csv: bool = False
    windows_csv: bool = True
    overwrite: bool = False


@dataclass
class N3Config:
    tool: str = "tsd_network"
    schema_version: int = 1
    log_level: str = "INFO"
    input: N3Input = field(default_factory=N3Input)
    layer_temp: N3LayerTemp = field(default_factory=N3LayerTemp)
    processing: N3Processing = field(default_factory=N3Processing)
    qc: N3QC = field(default_factory=N3QC)
    xml_uc: N3Xml = field(default_factory=N3Xml)
    output: N3Output = field(default_factory=N3Output)
    base_dir: str = "."


def build_n3_config(data: dict, base_dir=".") -> N3Config:
    cfg = _build(N3Config, data, "config")
    cfg.base_dir = str(base_dir)
    _choice(cfg.tool, ("tsd_network", "n3"), "tool")
    _choice(cfg.input.format, ("b1510off_txt",), "input.format")
    if not cfg.input.tsd_files:
        raise ConfigError("input.tsd_files: podaj co najmniej jeden plik eksportu B_1510off")
    lt = cfg.layer_temp
    _choice(lt.source, ("csv", "constant", "none"), "layer_temp.source")
    if lt.source == "csv" and not lt.csv:
        raise ConfigError("layer_temp.csv jest wymagane przy layer_temp.source: csv (temperatura warstwy 12 cm z N2/modelu)")
    if lt.source == "constant" and lt.constant_c is None:
        raise ConfigError("layer_temp.constant_c jest wymagane przy layer_temp.source: constant")
    if lt.source == "none" and not lt.allow_uncorrected:
        raise ConfigError("layer_temp.source: none wymaga allow_uncorrected: true (d0 bez korekty temperaturowej, flaga T_MISSING); "
                          "temperatura pirometru (Temp Road) NIE jest temperatura warstwy")
    p = cfg.processing
    if p.window_m <= 0 or p.hampel.window_m <= 0 or p.integral_step_m <= 0:
        raise ConfigError("processing: szerokosci okien i krok calkowania musza byc dodatnie")
    if p.min_rows_in_window < 1:
        raise ConfigError("processing.min_rows_in_window >= 1")
    if len(p.correction.range_c) != 2 or not p.correction.range_c[0] < p.correction.range_c[1]:
        raise ConfigError("processing.correction.range_c: oczekiwano [dolna, gorna]")
    for a in p.aggregate_m:
        if a <= 0:
            raise ConfigError("processing.aggregate_m: dodatnie kroki [m]")
    _choice(cfg.xml_uc.profile, ("dsn_h42",), "xml_uc.profile")
    _choice(cfg.xml_uc.km_direction, ("increasing", "decreasing"), "xml_uc.km_direction")
    _choice(cfg.xml_uc.scale, ("tsd", "fwd"), "xml_uc.scale")
    x = cfg.xml_uc
    if x.enabled:
        missing = [k for k in ("kod_oddz", "rok", "droga", "jezdnia", "pas", "km_start") if getattr(x, k) in (None, "")]
        if missing:
            raise ConfigError(f"xml_uc: wymagane w konfiguracji (bez wartosci domyslnych): {missing}")
        if x.step_m <= 0:
            raise ConfigError("xml_uc.step_m musi byc dodatnie")
    return cfg


def load_n3_config(path) -> N3Config:
    path = Path(path)
    return build_n3_config(load_yaml(path), base_dir=path.resolve().parent)
