"""Konfiguracja narzedzia tsd_fwd_compare (N4), tryb `pairs` (gotowe pary TSD-FWD + temperatury warstwy)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, OutputConfig, _build, _choice, load_yaml
from .constants import T_MIN_APPLICABLE_C

LAMBDA_D0 = 0.11786960020790811      # sigma_FWD^2 / sigma_TSD^2 na skali log (e2b2_lambda.csv, d0)


@dataclass
class N4Columns:
    pair_id: str = "pair_id"
    session: str = "fwd_session_id"          # klaster = sesja FWD
    fwd: str = "fwd_d0"                      # D0 FWD [um], znormalizowane do 50 kN
    tsd: str = "d0_tsd"                      # d0 TSD [um], mediana okna +-5 m
    fwd_t12: str = "fwd_t12_cal"             # temperatura warstwy po stronie FWD [C]
    tsd_t12: str = "tsd_t12_cal"             # temperatura warstwy po stronie TSD [C]
    group: str = "device_group"              # grupa aparat x rok (rozstep median grup)
    dt_days: str = "dt_days"
    gof_share: str = "win5_gof05_share"
    corridor: str = "corridor_id"
    station: str = "fwd_station_id"
    device: str = "device"
    calib_interval: str = "calib_interval"
    tsd_year: str = "tsd_year"
    era: str = "era"
    fwd_date: str = "fwd_measured_at_local"
    sigma_long: str = "sigma_long_fwd"


@dataclass
class N4Input:
    pairs_csv: str = ""
    t12_csv: str | None = None               # gdy temperatury nie sa w pairs_csv (klucz: pair_id)
    meta_csv: str | None = None              # dodatkowe kolumny par (np. e2b2_pairs.csv; klucz: pair_id)
    columns: N4Columns = field(default_factory=N4Columns)
    null_pairs_csv: str | None = None        # wartosci TSD par zerowych (pair_id, null_type, d0_w5, d0_valid_w5)
    null_type_col: str = "null_type"
    null_tsd_col: str = "d0_w5"
    null_valid_col: str | None = "d0_valid_w5"


@dataclass
class N4Correction:
    treatments: list = field(default_factory=lambda: ["none", "main_after"])   # none | main_after | k02
    main_treatment: str = "main_after"       # wariant glowny (przedzialy niepewnosci, warunki, kalibracja)
    beta_pct: float | None = None            # domyslnie beta D0 z zestawu e2a3_full
    t_ref_c: float = 20.0
    flag_outside_c: list = field(default_factory=lambda: [T_MIN_APPLICABLE_C, 30.0])


@dataclass
class N4Measures:
    lambda_d0: float = LAMBDA_D0
    n_boot: int = 1000
    seed_ci: int = 20261019                  # seed bootstrap_ci w zrodle (e2b2_agreement.py)
    seed_paired: int = 20261107              # seed bootstrapu sparowanego (z15_temp_correction.py)


@dataclass
class N4Uncertainty:
    methods: list = field(default_factory=lambda: ["session_bootstrap", "wild_cluster_webb", "cr2"])
    replicates: int = 9999
    seed_tag: str = "e2x_w3_lacznie"
    h0_multiplier: float | None = 1.6        # wartosc testowana (WCR) i sprawdzana w CI95


@dataclass
class N4Conditions:
    enabled: bool = True
    group_by: list = field(default_factory=lambda: ["device", "calib_interval"])
    cv_unit: str = "pairs"                   # pairs (jak w zrodle) | stations
    receiver_cutoff: str | None = None       # np. 2025-10-09: warstwa 'jakosc polozenia FWD'


@dataclass
class N4Calibration:
    enabled: bool = True
    treatment: str = "main_after"            # korekta przed kalibracja
    models: list = field(default_factory=lambda: ["multiplier"])


@dataclass
class N4Nulls:
    n_boot: int = 1000
    seed: int = 20261019


@dataclass
class N4Config:
    tool: str = "tsd_fwd_compare"
    schema_version: int = 1
    mode: str = "pairs"
    log_level: str = "INFO"
    input: N4Input = field(default_factory=N4Input)
    correction: N4Correction = field(default_factory=N4Correction)
    measures: N4Measures = field(default_factory=N4Measures)
    uncertainty: N4Uncertainty = field(default_factory=N4Uncertainty)
    conditions: N4Conditions = field(default_factory=N4Conditions)
    calibration: N4Calibration = field(default_factory=N4Calibration)
    null_checks: N4Nulls = field(default_factory=N4Nulls)
    output: OutputConfig = field(default_factory=OutputConfig)
    base_dir: str = "."


def build_n4_config(data: dict, base_dir=".") -> N4Config:
    cfg = _build(N4Config, data, "config")
    cfg.base_dir = str(base_dir)
    _choice(cfg.tool, ("tsd_fwd_compare", "n4"), "tool")
    if cfg.mode != "pairs":
        raise ConfigError("mode: dostepny jest tylko tryb 'pairs' (tryb 'geometry' w etapie E2b)")
    if not cfg.input.pairs_csv:
        raise ConfigError("input.pairs_csv: podaj plik z parami TSD-FWD")
    for t in cfg.correction.treatments + [cfg.correction.main_treatment, cfg.calibration.treatment]:
        _choice(t, ("none", "main_after", "k02"), "correction")
    if cfg.correction.main_treatment not in cfg.correction.treatments:
        cfg.correction.treatments.append(cfg.correction.main_treatment)
    _choice(cfg.conditions.cv_unit, ("pairs", "stations"), "conditions.cv_unit")
    for m in cfg.calibration.models:
        _choice(m, ("multiplier", "affine"), "calibration.models")
    for m in cfg.uncertainty.methods:
        _choice(m, ("session_bootstrap", "wild_cluster_webb", "cr2"), "uncertainty.methods")
    if cfg.measures.lambda_d0 <= 0:
        raise ConfigError("measures.lambda_d0 musi byc dodatnie")
    if cfg.measures.n_boot < 0 or cfg.uncertainty.replicates < 0:
        raise ConfigError("liczby replik musza byc nieujemne")
    if len(cfg.correction.flag_outside_c) != 2 or not cfg.correction.flag_outside_c[0] < cfg.correction.flag_outside_c[1]:
        raise ConfigError("correction.flag_outside_c: oczekiwano [dolna, gorna]")
    return cfg


def load_n4_config(path) -> N4Config:
    path = Path(path)
    return build_n4_config(load_yaml(path), base_dir=path.resolve().parent)
