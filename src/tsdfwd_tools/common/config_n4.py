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
class N4TsdColumns:
    run_id: str = "run_id"                   # kolumna przejazdu; gdy jej brak w pliku: nazwa pliku (bez sufiksu _rows)
    chainage: str = "chainage_m"             # pikietaz pliku (SUROWY, rosnacy z jazda); lag -4,8 m N4 stosuje sam
    lat: str = "lat"
    lon: str = "lon"
    d0: str = "d0"                           # d0 TSD [um] z eksportu B_1510off (bez korekty temperaturowej)
    gof: str = "gof"
    t12: str = "t12_c"                       # temperatura warstwy 12 cm (z N2)
    speed: str = "speed_kmh"
    time: str = "time"                       # opcjonalnie: czas wiersza (ISO albo sekundy epoki) - do pary przejazdow w lambdzie
    concrete: str = "concrete"               # opcjonalnie: znacznik betonu (0/1) - do wykluczenia betonu w lambdzie
    profile: str = "profile"                 # opcjonalnie: profil podluzny [mm] (np. profile1) - do wyrownania przejazdow


@dataclass
class N4FwdColumns:
    station_id: str = "station_id"
    session: str = "session_id"
    station_m: str = "station_m"             # dystansomierz FWD (km albo m — jednostka wykrywana z danych)
    lat: str = "latitude"
    lon: str = "longitude"
    time: str = "measured_at"
    device: str = "device"                   # aparat (trailer), np. 8002-367
    date: str = "date"                       # data pomiaru RRRR-MM-DD (do reguly anteny i roku)
    heading: str = "heading_deg"             # opcjonalnie: kurs geograficzny (zwiekszy odrzucanie przeciwnego kierunku)
    d0: str = "D0"                           # D0 FWD [um] znormalizowane do 50 kN, BEZ korekty temperaturowej (z N1)
    t12: str = "t_mid_c"                     # temperatura warstwy po stronie FWD (z N1/N2)
    in_concrete_zone: str = "in_concrete_zone"
    t_surface: str = "t_surface"             # temperatura powierzchni (pirometr aparatu) - tylko do estymatora lambdy


@dataclass
class N4Sections:
    """Odcinki wspolne TSD-FWD (kryteria Tab. 3.2): wykrywanie, raport przegladu i opcjonalny filtr par."""
    enabled: bool = True
    radius_m: float = 8.0
    min_coverage_pct: float = 30.0
    min_abs_spearman: float = 0.80
    bearing_tol_deg: float = 30.0
    max_days: float = 400.0
    lane_same_max_m: float = 0.75
    lane_adjacent_max_m: float = 2.0
    same_year_only: bool = True
    min_overlap_len_m: float = 500.0
    min_matched_stations: int = 5
    review_csv: str | None = None          # decyzje recznego przegladu: session_id, run_id, status (confirmed / rejected)
    require_section: bool = False          # tylko pary z odcinka wspolnego (z pominieciem rejected)
    report_html: bool = True               # raport przegladu "linia do linii" (SVG)
    report_max_sections: int = 300


@dataclass
class N4LambdaEst:
    """Estymator lambdy (Q-N4-5): lambda = sigma_FWD^2 / sigma_TSD^2 z powtorzen pomiarow (wymaga kilku przejazdow TSD tego samego
    dnia i kilku sesji FWD tego samego aparatu na wspolnej drodze)."""
    enabled: bool = False
    apply: bool = False                    # uzyj oszacowania zamiast measures.lambda_d0 w miarach zgodnosci
    bin_m: float = 10.0
    cover_min_n: int = 5
    tsd_max_dt_days: float = 1.0
    fwd_from_date: str | None = "2024-01-01"
    fwd_max_dtemp_c: float = 3.0
    fwd_min_stations: int = 1
    exclude_concrete: bool = True


@dataclass
class N4Geometry:
    tsd_rows: list = field(default_factory=list)         # pliki CSV z wierszami TSD (np. *_rows.csv z N3 z rows_csv: true)
    tsd_runs_csv: str | None = None                      # opcjonalnie: run_id, date [, calib_interval, data_tier, recorder_group]
    fwd_stations_csv: str = ""
    corridors_csv: str | None = None                     # gotowa os (corridor_id, s, x_2180, y_2180, heading_deg); domyslnie z przejazdow TSD
    tsd_columns: N4TsdColumns = field(default_factory=N4TsdColumns)
    fwd_columns: N4FwdColumns = field(default_factory=N4FwdColumns)
    lag_m: float = -4.8                                  # lag polozenia ugiec TSD wzgledem GPS (konwencja E0-C), +-1,5 m
    antenna: list = field(default_factory=list)          # reguly anteny: [{device, d_m, era, confirmed, from, until}]; puste = P043b
    sigma_era: dict = field(default_factory=dict)        # nadpisanie sigma_era [m] (era -> wartosc)
    eps_variant: str = "short_zero"                      # short_zero | full
    axis: dict = field(default_factory=dict)             # nadpisanie progow osi (AxisParams)
    calib_intervals: dict = field(default_factory=lambda: {
        "K2024-03-01": ["2024-03-01", "2025-05-26"], "K2025-05-27": ["2025-05-27", "2026-05-18"],
        "K2026-05-19": ["2026-05-19", "2099-12-31"]})
    layers: list = field(default_factory=lambda: ["A", "B"])
    same_year_only: bool = True
    require_valid_d0: bool = True                        # tylko pary z waznym d0 po obu stronach (okno >= min_rows wierszy)
    sections: N4Sections = field(default_factory=N4Sections)
    lambda_est: N4LambdaEst = field(default_factory=N4LambdaEst)
    merge_lanes: bool = True                             # scalanie duplikatow pasa przy budowie osi z przejazdow TSD (gdy brak corridors_csv)
    align: str = "auto"                                  # wyrownanie przejazdow profilem: auto (gdy jest kolumna profilu) | true | false
    window_m: float = 5.0                                # polowka okna wartosci TSD (W5)
    min_rows: int = 3
    date_override: str | None = None                     # data wspolna dla wszystkich przejazdow TSD (gdy brak jej w nazwie/pliku)


@dataclass
class N4Config:
    tool: str = "tsd_fwd_compare"
    schema_version: int = 1
    mode: str = "pairs"
    log_level: str = "INFO"
    geometry: N4Geometry = field(default_factory=N4Geometry)
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
    _choice(cfg.mode, ("pairs", "geometry"), "mode")
    if cfg.mode == "pairs" and not cfg.input.pairs_csv:
        raise ConfigError("input.pairs_csv: podaj plik z parami TSD-FWD")
    if cfg.mode == "geometry":
        g = cfg.geometry
        if not g.tsd_rows:
            raise ConfigError("geometry.tsd_rows: podaj co najmniej jeden plik CSV z wierszami TSD")
        if not g.fwd_stations_csv:
            raise ConfigError("geometry.fwd_stations_csv: podaj plik CSV ze stacjami FWD")
        _choice(g.eps_variant, ("short_zero", "full"), "geometry.eps_variant")
        for ly in g.layers:
            _choice(ly, ("A", "B", "C", "X"), "geometry.layers")
        if g.window_m <= 0 or g.min_rows < 1:
            raise ConfigError("geometry.window_m > 0 oraz geometry.min_rows >= 1")
        for rule in g.antenna:
            if not isinstance(rule, dict) or not {"device", "d_m"} <= set(rule):
                raise ConfigError("geometry.antenna: kazda regula to slownik z kluczami device, d_m [, era, confirmed, from, until]")
        _choice(str(g.align).lower(), ("auto", "true", "false"), "geometry.align")
        if g.lambda_est.apply and not g.lambda_est.enabled:
            raise ConfigError("geometry.lambda_est.apply wymaga geometry.lambda_est.enabled: true")
        if g.sections.radius_m <= 0 or g.sections.min_matched_stations < 1:
            raise ConfigError("geometry.sections: radius_m > 0 oraz min_matched_stations >= 1")
        for name, rng in g.calib_intervals.items():
            if len(rng) != 2:
                raise ConfigError(f"geometry.calib_intervals.{name}: oczekiwano [od, do] (RRRR-MM-DD)")
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
