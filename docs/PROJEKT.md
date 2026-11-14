# PROJEKT pakietu `tsdfwd_tools` (etap E0 — do zatwierdzenia przez Jacka)

Data: 2026-11-13. Stan: propozycja. Kod produkcyjny nie istnieje. Podstawa: `docs\INWENTARZ.md`.
Jezyk: komentarze/docstringi po polsku BEZ diakrytykow, nazwy po angielsku. Python 3.11, srodowisko `C:\ENV\narzedzia_tsd_fwd`.

---------------------------------------------------------------------------------------------------

## 1. Zasady projektowe

1. Pakiet pracuje na plikach (CSV/XLSX/XLS/TXT/opcjonalnie MDB), bez baz SQLite i bez "wydan" projektu badawczego. Zadne narzedzie nie importuje kodu z `sql_tsd_fwd` ani `DOKTORAT` — kod jest przenoszony (kopia + przeredagowanie) z naglowkiem `zrodlo: <sciezka>, stan <hash/data>`.
2. Biblioteka zwraca wyniki i flagi, nigdy nie przerywa procesu (`sys.exit`), nie uzywa stanu globalnego, nie pisze do `output\` zrodel; logowanie przez `logging`.
3. Kazda wartosc spoza zakresu waznosci jest OZNACZANA flaga (rejestr oznaczen zamiast usuwania rekordow, R3.9).
4. Zadnych "cichych" przejsc: formy korekty to enum, nieznana wartosc = wyjatek (S-N1-1).
5. Wszystkie parametry metod (beta, k, progi, okno, seedy) w konfiguracji z domyslnymi = wartosci raportu; zmiana domyslnych wymaga decyzji Jacka. Wersja wspolczynnikow i parametrow jest zapisywana w kazdym wyjsciu (`meta`).
6. Zasady metodyczne (obowiazuja wszedzie): korekta temperaturowa najpierw na kazdym czujniku FWD / kanale TSD; SCI300, BDI, BCI wylacznie z ugiec skorygowanych (nigdy wlasnym wspolczynnikiem wskaznika); parowanie TSD-FWD wylacznie geometryczne.
7. Jednostki: ugiecia [um], nachylenia [um/m], sila [kN], temperatura [C], odleglosci [m], beta [%/C] w wejsciu konfiguracji i plikach danych, w obliczeniach [1/C].
8. Powtarzalnosc: seedy jawne; `hash()` jako seed zabronione (uzywamy `zlib.crc32` jak `seed_for`).

---------------------------------------------------------------------------------------------------

## 2. Struktura pakietu

```
narzedzia_tsd_fwd/
  pyproject.toml            # nazwa tsdfwd-tools, python>=3.11; zaleznosci: numpy>=2, pandas>=2.2, scipy, pyyaml, xlrd, openpyxl
                            #   opcjonalne extras: mdb (pyodbc), net (requests), plots (matplotlib), dev (pytest)
  requirements.txt          # zamrozone wersje (pip freeze z srodowiska)
  README.md
  configs/                  # przyklady: n1_example.yaml ... n4_example.yaml
  docs/                     # DZIENNIK.md, INWENTARZ.md, PROJEKT.md, INSTRUKCJA_N1..N4.md (E5), notatki_E0/
  src/tsdfwd_tools/
    __init__.py  __main__.py  _version.py
    common/
      constants.py          # T_REF=20.0, LOAD_REF_KN=50.0, GEOPHONES_MM, CHANNELS_9 (znak!), GOF_MIN=0.5, INTSTEP_M=0.001
      config.py             # dataclasses + wczytanie YAML + walidacja schematu
      coefficients.py       # wczytanie i walidacja tabel wspolczynnikow (data/*.csv), wybor zestawu
      rules.py              # CorrectionForm(enum LINEAR/EXPONENTIAL), factor(), apply_correction()
      flags.py              # katalog flag (str + bit), zbieranie, serializacja
      io_utils.py           # czytniki CSV (utf-8-sig, ; i ,), nmed, NaN-bezpieczne mediany
      stats_basic.py        # robust_sd (1,4826*MAD), group_median, seed_for(tag)
      geo.py                # to_2180, heading_of, angdiff, project_on, Corridor (E2/E3, jesli tryb B)
      logging_setup.py
    data/
      e2a3_final_k_profile.csv   # kopia z sql_tsd_fwd\tabele (scope lacznie, 12 wskaznikow) + naglowek pochodzenia
      tab71.csv                  # Tab. 7.1 raportu (zaokraglone)
      params_TN.json             # N2: parametry zamrozone + hash zrodla
    fwd/                    # N1
      io.py  normalize.py  quality.py  tempcorr.py  indices.py
    layer_temp/             # N2
      constants.py  params.py  meteo.py  frame.py  solver.py  calibrate.py  predict.py  bells3.py  uncertainty.py  qc.py
    tsd/                    # N3
      io.py  zero_sets.py  integrals.py  tempcorr.py  filters.py  window.py  aggregate.py  qc.py  convert.py  uc_export.py
    compare/                # N4
      sections.py  fwd_position.py  pairing.py  corrections.py  agreement.py  uncertainty.py  lambda_est.py
      conditions.py  calibration.py  report.py
    cli/
      main.py               # `python -m tsdfwd_tools <narzedzie> --config plik.yaml`
  tests/
    unit/                   # testy jednostkowe wzorow (syntetyczne)
    regression/             # testy regresji na wartosciach referencyjnych (znacznik @pytest.mark.reference)
    data/                   # male wycinki testowe (<= kilka MB) z README pochodzenia
    local_paths.example.yaml# sciezki do duzych danych do odczytu (poza repo): bazy, tabele, cache OM
```

Nazwy narzedzi w CLI: `fwd_tempcorr` (N1), `layer_temp` (N2), `tsd_network` (N3), `tsd_fwd_compare` (N4), ze skrotami `n1..n4`.
Wywolanie: `python -m tsdfwd_tools fwd_tempcorr --config configs\n1_example.yaml` (opcje: `--dry-run`, `--log-level`, `--out-dir`). Kod wyjscia: 0 = ok, 1 = blad wejscia/konfiguracji, 2 = wyniki z flagami krytycznymi (tylko gdy `--strict`).

Elementy z audytu, ktorych NIE przenosimy: `datasets.py`, `paths.py` (release_guard), `md5_r2`, kopie `_pre_pNNN.db`, `insert/write_csv` do baz, bootstrap/pasma/werdykty rownowaznosci E2a, `calibrate_conversion.py`, `compare_tsd_fwd.py` (wybor po wartosciach), `inject_dfwd.py`, hybryda/XGBoost, BELLS3_BT/BELLS3_O, eksport nominalny TSD jako zrodlo d0.

---------------------------------------------------------------------------------------------------

## 3. Konfiguracja (schemat YAML)

Wspolne: `tool` (nazwa), `schema_version: 1`, `output: {dir, formats: [csv, xlsx], overwrite: false}`, `log_level`.
Niewskazane klucze maja wartosci domyslne z raportu. Sciezki bezwzgledne lub wzgledem pliku konfiguracji.

### 3.1 N1 fwd_tempcorr
```yaml
tool: fwd_tempcorr
schema_version: 1
input:
  files: ["D:/dane/Drops50_1M_1.xlsx"]        # lub katalog + maska
  stations_files: ["D:/dane/stations50_1M_1.xlsx"]   # dla xlsx_drops_stations (stacje z GPS i temperaturami)
  format: auto                                 # auto | xlsx_drops_stations | mdb | csv_generic
  drop_rule: mean_nonseating                   # mean_nonseating | second_drop | last_nonseating   (Q-N1-3)
  geophone_mapping: by_x                       # by_x (po x1..x9 sesji) | standard_layout
temperature:
  source: column                               # column | constant | csv_join
  column: asphalt_temp                         # nazwa kolumny T_mid w pliku (lub w csv_join)
  csv: null                                    # wynik N2 (klucze: session_id, station_id lub measured_at)
  constant_c: null
  depth_cm: 12                                 # dokumentacyjnie; trafia do meta i flag
  thickness_cm: null                           # opcjonalnie, tylko flaga ostrzegawcza poza 15-30 cm
  max_age_min: 60                              # starsza wartosc operatora -> flaga T_STALE
correction:
  variant: B                                   # A (liniowy) | B (wykladniczy) | legacy (porownawczy: k=0,02 droga publiczna, k=0,01 autostrada wg road_type)
  road_type: public                            # public | highway — tylko dla variant: legacy (k=0,02 / 0,01)
  coefficient_set: e2a3_full                   # e2a3_full | tab71   (Q-N1-1)
  ranges_c: {A: [5, 25], B: [5, 30]}           # zakresy waznosci wariantow (flagi, nie obciecie)
  indices_max_c: 25                            # powyzej: flaga INDEX_ABOVE_RANGE dla SCI300/BDI/BCI
  t_ref_c: 20.0
  load_ref_kn: 50.0
  placeholder_temps_c: [20.4]                  # wartosci zastepcze -> flaga T_PLACEHOLDER (W22)
output:
  dir: "D:/wyniki/n1"
  formats: [csv, xlsx]
  per_station_file: true
  summary: true
```

### 3.2 N2 layer_temp
```yaml
tool: layer_temp
schema_version: 1
input:
  survey_csv: "D:/dane/profil_pirometr.csv"    # kolumny: measured_at_local, latitude, longitude, t_surface, t_air [, id]
  time_basis: local_Europe_Warsaw_DST          # lokalny czas naiwny z DST (jak FWD)
  position_source: column                      # column | interpolate_from_gps_csv
model:
  depth_cm: 12                                 # zadana glebokosc (siatka 1 cm, 0-50 cm); "polowa pakietu" = grubosc/2 gdy thickness_cm podane
  thickness_cm: null
  params_file: builtin:params_TN.json          # parametry zamrozone (alpha, EB, beta50, beta_ir)
  terrain_class: open                          # open (TN); shaded = TODO (Q-N2-7)
  calibration: single_shot_ir_mass             # tryb referencyjny; none = fizyka bez kalibracji
meteo:
  provider: open_meteo_archive
  cache_dir: "D:/cache/open_meteo"             # wyniki pobierania (jedyne polaczenie sieciowe)
  offline: false                               # true = tylko cache (testy), brak pobierania
  grid_deg: 0.05
  history_days: 35
qc:
  season_months: [4, 5, 6, 7, 8, 9, 10]        # poza sezonem: flaga OUT_OF_SEASON
  snow_depth_max_m: 0.005
  night_sw_wm2: 5.0                            # SW_ma6 < 5 W/m2 -> flaga NIGHT (kalibracja nie dziala)
comparators: {bells3: false}                   # tylko BELLS3 klasyczny, nigdy BT/O
output: {dir: "D:/wyniki/n2", formats: [csv]}
```

### 3.3 N3 tsd_network
```yaml
tool: tsd_network
schema_version: 1
input:
  tsd_files: ["D:/dane/B_1510off/T4202405210001.raw.sup.txt"]   # eksport B_1510off
  format: b1510off_txt                         # b1510off_txt | b1510off_csv
  layer_temp_csv: "D:/wyniki/n2/layer_temp.csv"   # T12 na wiersz/blok (z N2) — wymagane
  calib_interval: {K2024-03-01: ["2024-03-01", "2025-05-26"], K2025-05-27: [...], K2026-05-19: [...]}   # dziennik kalibracji
processing:
  channels_m: [-0.45, -0.30, -0.20, 0.11, 0.21, 0.31, 0.46, 0.61, 0.91]   # bez 1,51 m
  integral: {method: pchip_dense, step_m: 0.001, segments: [[0, 0.31], [0.31, 0.61], [0.61, 0.91]]}
  temperature_correction: {form: exponential, beta_pct: 1.60, range_c: [5, 30], t_ref_c: 20.0}
  hampel: {on: d0, window_m: 10.0, k: 4.4478, mad: window, reject_whole_bowl: true}   # Q-N3-1 (domyslnie parametry tsd_pipeline)
  window_m: 5.0                                # +-5 m (dopuszczalnie 10 m)
  min_rows_in_window: 3
  gof_threshold: 0.5                           # tylko atrybut (udzial czasz GoF >= 0,5)
  aggregate_m: [50, 100]
  to_fwd_scale: {enabled: false, multiplier: 1.62}    # D0_FWD,20 = m * d0_TSD,20
qc:
  gps_gyro: true
  channel_shift: true
  position_offset_m: 0.0     # w implementacji: processing.position_offset_m, domyslnie 0; lag -4,8 => pozycja = pikietaz + 4,8 m (Q-N4-3)
output:
  dir: "D:/wyniki/n3"
  csv: true
  xml_uc: {enabled: true, profile: dsn_h42, kod_oddz: "WA", rok: 2026, droga: "50", jezdnia: "1", pas: "1", step_m: 10,   # profile: dsn_h42 (zal. H p. 4.2, 21 pol) | extended43
           direction: auto, km_anchor: first_event_marker, schema_location: "UC_Schema.xsd"}
```

### 3.4 N4 tsd_fwd_compare
```yaml
tool: tsd_fwd_compare
schema_version: 1
mode: pairs                                    # pairs (tryb A: gotowe pary) | geometry (tryb B: z wspolnych odcinkow)
input:
  pairs_csv: "D:/dane/z15_pary_wejscia.csv"    # pair_id, session_id, fwd_d0, tsd_d0, dt_days, gof_share, device, era, calib_interval ...
  t12_csv: "D:/dane/Z15_temperatury_par.csv"   # fwd_t12, tsd_t12 po kluczu pair_id (z N2)
  null_pairs_csv: null                         # lub generowane (tryb geometry)
  tsd_runs: []                                 # tryb geometry
  fwd_sessions: []                             # tryb geometry
sections:                                      # Tab. 3.2 (tryb geometry)
  radius_m: 8.0
  min_coverage_pct: 30
  min_stations: 5
  min_overlap_len_m: 500
  min_abs_spearman: 0.80
  bearing_tol_deg: 30
  lane_same_max_m: 0.75
  lane_adjacent_max_m: 2.0
  same_year: true
fwd_antenna:                                   # parametry polozenia plyty (data, d_m) — Q-N4-2
  "8002-367": [{until: "2025-10-09", d_m: 5.5}, {from: "2025-10-09", d_m: 0.0}]
  "8082-119": [{d_m: 1.0}]
  "8002-369": [{d_m: 1.0}]
tsd_position_offset_m: -4.8
pairing: {representation: W5, also: [W10], min_rows: 3}   # nigdy wybor po wartosciach FWD
correction: {treatment: main_after, beta_pct: 1.60415, t_ref_c: 20.0, flag_outside_c: [5, 30]}
measures: {lambda: {d0: 0.11787}, deming_space: loglog, bootstrap: {replicates: 1000, seed: 20261107}}
uncertainty: {methods: [session_bootstrap, wild_cluster_webb, cr2, iso_week], wild_replicates: 9999}
null_checks: {shifts_m: [-200, 200], permutation_min_m: 300, seed: 20261017}
conditions: {dt_bins_days: [0, 1, 30], gof_bins: [0.5, 0.8], cv_terciles: true, group_by: [device, calib_interval]}
calibration: {multiplier: true, affine: false, leave_out: session}
output: {dir: "D:/wyniki/n4", report_html: true, plots: true}
```

---------------------------------------------------------------------------------------------------

## 4. Interfejsy publiczne (sygnatury; ugiecia/temperatury jako `numpy.ndarray`/`pandas.DataFrame`)

### 4.1 common
```python
class CorrectionForm(enum.Enum): LINEAR = "linear"; EXPONENTIAL = "exponential"
def factor(temp_c, form: CorrectionForm, param: float, t_ref: float = 20.0) -> np.ndarray   # f(T); LINEAR: 1+k(Tref-T); EXP: exp(beta(Tref-T))
def apply_correction(y, temp_c, form: CorrectionForm, param, t_ref=20.0) -> np.ndarray      # y * factor ; nieznany form -> ValueError
def load_coefficients(set_name: str = "e2a3_full", scope: str = "lacznie") -> CoefficientTable
class CoefficientTable:   # indeksowana wskaznikiem D0..D1800, SCI300, BDI, BCI
    def k(self, indicator: str) -> float            # [1/C]
    def beta(self, indicator: str) -> float         # [1/C] (beta_pct/100)
    meta: dict                                      # zrodlo, zakres dopasowania 5<=T<30, T_mid, n, data, hash
def seed_for(tag: str, kind: str) -> int            # crc32 jak w zrodle
```
Konwencja zakresow: flagi zakresu uzywaja przedzialu domknietego `[lo, hi]` dla waznosci wariantu (T=25,0 w zakresie A, T=30,0 w zakresie B); dopasowania wspolczynnikow (opcjonalny modul `fit`) uzywaja `lo <= T < hi` jak w P040. Konwencje opisane w docstringach i testach (S-N1-2).

### 4.2 fwd (N1)
```python
def read_fwd(path: PathLike, fmt: str = "auto", stations_path: PathLike | None = None) -> FwdSession   # sesja, stacje, zrzuty, d1..d9, x1..x9, force, temperatury, czas, gps
def select_drop(drops: pd.DataFrame, rule: str = "mean_nonseating") -> pd.DataFrame
def normalize_load(d_um, force_kn, ref_kn: float = 50.0) -> np.ndarray                             # D * 50 / F
def assess_temperature(station_df, placeholder_temps=(20.4,), max_age_min=60) -> pd.DataFrame      # status wpisu: entry_first/entry_change/entry_possible/carried/missing + flagi
def correct_deflections(d_um: pd.DataFrame, temp_c, variant: str = "B", coefficient_set: str = "e2a3_full",
                        ranges_c=None, t_ref: float = 20.0) -> CorrectedDeflections                # D_i,20 dla kazdego czujnika + flagi
def curvature_indices(d20: pd.DataFrame) -> pd.DataFrame                                           # SCI300, BDI, BCI = roznice D_i,20 (wylacznie z ugiec skorygowanych)
def run_n1(cfg: N1Config) -> N1Result                                                              # caly potok; zapis przez writer
```
`CorrectedDeflections`: `.d20` (DataFrame), `.flags` (DataFrame bitowo + `flags_text`), `.meta` (wariant, zestaw wspolczynnikow, hash, T_ref, zakresy).
Nieobslugiwane celowo: wlasne wspolczynniki wskaznikow; korekta T < 5 C; korekta indeksow > `indices_max_c` (flaga zamiast ukrycia).

### 4.3 layer_temp (N2)
```python
# stan wdrozenia (E4) — pakiet tsdfwd_tools.layer_temp
fetch_open_meteo(lat, lon, start, end, *, http_get=None, sleep=time.sleep) -> (DataFrame lokalny, meta)  # meteo.py; urllib (bez `requests`), timezone=UTC, 6 zmiennych, retry 429
class MeteoStore(cache_dir, offline=True, grid_deg=0.05)  # .get(lat, lon, lo, hi) -> (om, info); cache parquet (referencyjny) i csv+json (zapisywany); pobiera brakujace okno (dzien pomiaru + 1)
om_utc_to_local(df_utc) -> DataFrame           # Europe/Warsaw, naiwny; duplikat jesienny: pierwsze wystapienie; luka wiosenna: brak wiersza
build_frame(om, index) -> DataFrame            # frame.py: siatka 10 min, swr przesuniete -30 min, MA7/MA30, sw_ma6 (rolling 36, min_periods 18)
bottom_t50(frame, params), delta_ir(frame, params), longwave_down(...)
simulate_eb(sub, bottom, params, a_sw) -> np.ndarray      # solver.py: PELNA siatka T[nt, 51] (0-50 cm), pierwsze 288 krokow NaN
calibrate_single_shot(ts_of_a, target, a_default, bounds, gate_c, xtol) -> Calibration   # calibrate.py: brentq; ok/bound_lo/bound_hi/gate/nosim
class CellDay(om, day, t_end, params)                      # predict.py: ramka + symulacje wspolne dla (komorka, doba); symulacja przyczynowa
predict_at(ctx, t, ir, depth_m, calibration=..., qc=...) -> LayerTempResult
layer_temperature(ts, lat, lon, ir, air=None, depth_m=0.12, *, meteo, params=None, calibration=..., with_bells3=False) -> LayerTempResult
run_survey(df, meteo, params, depth_cm=12, ...) -> DataFrame          # seria; grupowanie po (komorka, doba)
run_n2(cfg: N2Config, dry_run=False) -> dict(table, meta, outputs)    # pipeline.py
# LayerTempResult: value, value_uncal, u95, a_sw, ts_sim, ir_masa, calib_flag, flags (LayerFlag), grid_lat/lon, sw_ma6, bells3, params_hash
```
Niepewnosc (propozycja do uzgodnienia, Q-N2-5): u95 = +-2*RMSE_pora (6-12 h: 2,8; 12-18 h: 3,8; noc: 4,3), nie mniej niz 2,2 C (dolna granica metody pomiaru).

### 4.4 tsd (N3)
```python
def read_b1510off(path) -> TsdRun                                    # d0, slope[9 kanalow], gof, speed, temperatury, gps, chainage, naglowek (zestaw zer, GoodNess limit)
def dense_integral(slopes_by_channel: dict | np.ndarray, x_m: np.ndarray, x_max: float, step_m: float = 0.001) -> float | np.ndarray
def p0_integrals(slopes: np.ndarray) -> pd.DataFrame                 # A031, A0361, A6191, A061, A091 (PCHIP, od x=0, bez slope(0)=0)
def trapezoid_integral(slopes, stage_channels) -> float              # wariant T (kontrolny), slope(0)=0
def correct_d0(d0_um, t12_c, beta_pct=1.60, range_c=(5, 30), t_ref=20.0) -> tuple[np.ndarray, np.ndarray]   # (d0_20, flagi zakresu)
def hampel_bowl_filter(run: TsdRun, window_m: float = 10.0, k: float = 3*1.4826, step_m: float | None = None) -> pd.Series  # maska odrzutu CALEJ czaszy; MAD prawdziwy okna, thr>0
def window_stats(run, s_points, half_m: float = 5.0, min_rows: int = 3, gof_min: float = 0.5) -> pd.DataFrame   # d0_w5 (mediana), calki (mediana calek), n, gof_share, flagi
def aggregate(run_df, step_m: int, how: str = "median", min_n: int = 3) -> pd.DataFrame      # bin = floor(s / step_m), po wspolrzednej korytarza
def qc_flags(run, gps_gyro: bool = True, channel_shift: bool = True) -> pd.DataFrame
def to_fwd_scale(d0_20, multiplier: float = 1.62) -> np.ndarray
def write_uc_xml(path, records: pd.DataFrame, kod_oddz: str, rok: int, schema_location: str = "UC_Schema.xsd") -> None   # deklaratywna tabela 43 pol; NaN -> puste elementy
def run_n3(cfg: N3Config) -> N3Result
```
Kolejnosc operacji N3 (propozycja do potwierdzenia Q-N3-1): wiersz -> korekta d0 do 20 C (T12 z N2) -> Hampel na d0_20 z odrzutem calej czaszy -> mediana/srednia w oknie +-5 m -> agregacja 50/100 m -> (opcjonalnie) mnoznik 1,62 -> XML. Calki P0 NIE sa korygowane wspolczynnikami FWD (raport 6.1); sa raportowane z flaga.

### 4.5 compare (N4)
```python
def detect_sections(tsd_points: pd.DataFrame, fwd_stations: pd.DataFrame, cfg: SectionCriteria) -> pd.DataFrame      # Tab. 3.2; |Spearman|, kierunek, klasa pasa
def section_review_report(sections, tsd_points, fwd_stations, out_dir) -> list[Path]                                  # wykres "linia do linii" na odcinek
def fwd_plate_position(stations: pd.DataFrame, device_rules: AntennaRules, direction: str = "from_data") -> pd.DataFrame
def build_pairs(sections, tsd_rows, fwd_stations, window_m: float = 5.0, min_rows: int = 3) -> pd.DataFrame            # tylko geometria
def build_null_pairs(pairs, shifts_m=(-200, 200), permutation_min_m: float = 300, seed: int = 20261017) -> dict[str, pd.DataFrame]
def correct_pairs(pairs, t12: pd.DataFrame, treatment: str = "main_after", beta_pct: float = 1.60415) -> pd.DataFrame  # none | main_after | k02
def agreement_measures(fwd, tsd, session_id, *, lam_d0: float = 0.11787) -> AgreementResult   # median_ratio, sd_log_ratio, pearson/spearman (log i w obrebie sesji), CCC, BA (ilorazu), Deming log-log
def session_bootstrap(values, session_id, n_rep: int = 1000, seed: int = ...) -> CI
def paired_bootstrap_null(real_pairs, null_pairs, session_id, ...) -> CI                                              # roznica prawda - zero
def wild_cluster_bootstrap(...); def cr2_interval(...); def iso_week_cluster(...)
def conditions_table(pairs, bins_days, bins_gof, group_by) -> pd.DataFrame                                              # dt (z |dt|), GoF, CV D0 (tercyle po unikalnych stacjach), aparat x calib_interval
def fit_multiplier(...); def fit_affine(...); def leave_one_group_out(fit_fn, groups, ...) -> pd.DataFrame
def estimate_lambda(tsd_repeat_pairs, fwd_repeat_pairs) -> LambdaResult                                                 # sigma_TSD, sigma_FWD, lambda
def run_n4(cfg: N4Config) -> N4Result
```
Tryb `pairs` obowiazkowy w E2; tryb `geometry` (przeniesienie `e1_sref` + `e2b1_geometry` + `e2b1_pairs`) wdrozony w E2b (moduly `compare\geo.py`, `fwd_position.py`, `pairing.py`, `geometry_pipeline.py`; `compare\sections.py` + `section_report.py` (odcinki Tab. 3.2 i raport przegladu) w E2c; `compare\lambda_est.py` (estymator lambdy, E2d), `compare\align.py` (wyrownanie profilem, E2e), scalanie duplikatow pasa w `compare\geo.py` (E2f); poza zakresem: drogomierz zakotwiczony w strefach zlego GPS).

---------------------------------------------------------------------------------------------------

## 5. Formaty wyjsc

Wszystkie CSV: UTF-8 (bez BOM), separator `,`, kropka dziesietna, naglowek angielski, czas ISO-8601; XLSX: arkusze `data`, `summary`, `meta`. Kazde wyjscie ma plik `*_meta.json` (wersja pakietu, hash konfiguracji, wersja/hash wspolczynnikow, data uruchomienia, wejscia + MD5).

### 5.1 N1
`<plik>_tempcorr.csv`, jeden wiersz na stacje: `session_id, station_id, measured_at, latitude, longitude, force_kn, t_mid_c, t_source, t_status, variant, coef_set, d0..d1800 (znormalizowane 50 kN), d0_20..d1800_20, sci300_20, bdi_20, bci_20, flags, flags_text`.
`summary.csv`: per plik/sesja: n stacji, T min/mediana/max, udzial flag (T poza zakresem, brak T, przeniesiona, zastepcza, < 5 C, indeksy powyzej zakresu), mediana korekty D0.
Flagi: `T_MISSING, T_BELOW_5C (brak zastosowania), T_ABOVE_RANGE (powyzej zakresu wariantu), T_CARRIED, T_PLACEHOLDER (np. 20,4), T_STALE, T_MODEL (z N2), INDEX_ABOVE_RANGE (SCI300/BDI/BCI przy T > 25 C), INDEX_NONPOSITIVE, FORCE_OFF_NOMINAL, SEATING_ONLY, THICKNESS_OUT_OF_RANGE`.

### 5.2 N2
`layer_temp.csv`: `id, measured_at_local, latitude, longitude, t_surface, [t_air], depth_cm, t_layer, u95, a_sw, ts_sim, calib_flag, grid_lat, grid_lon, sw_ma6, qc_flags, flags_text, t_layer_uncal, ir_masa, [bells3_c], [t12_c (gdy depth_cm = 12; nazwa domyslna kolumny temperatury w N3)], [passthrough]`; `layer_temp_meta.json` z wersja i hashem parametrow, produktem i trybem Open-Meteo, licznikami flag, konfiguracja i uwaga o dokladnosci (H 1,75 / C 2,73). Flagi (`LayerFlag`): `NIGHT, OUT_OF_SEASON, SNOW, METEO_GAP, TAIL_EXTRAPOLATED, CALIB_GATE, CALIB_BOUND_HI, CALIB_BOUND_LO, CALIB_NOSIM, IR_MISSING, CALIB_OFF, DEPTH_NOT_VALIDATED, DEPTH_OUT_OF_RANGE, SHADED_SITE_SUSPECTED (zarezerwowana, niewykrywana), POSITION_OUT_OF_POLAND`.
Wdrozone w E4 przy domyslnych odpowiedziach na Q-N2-1..9 (patrz DZIENNIK): regresja na H v2, parametry pre-omfix, NIGHT = SW_ma6 < 5 W/m2, tylko archiwum, u95 = 2*RMSE_pora (min. 2,2 C), CALIB_BOUND_HI jako flaga, brak klasy zacienionej, DEPTH_NOT_VALIDATED poza 10/12 cm, cache testowy czytany z `doktorat_root` (bez kopiowania).

### 5.3 N3
`tsd_rows.csv` (opcjonalnie, 1 m): `file_id, chainage_m, s_corridor_m, datetime, latitude, longitude, d0, d0_20, a031, a0361, a6191, a061, a091, gof, speed_kmh, t12, flags`.
`tsd_agg_<step>m.csv`: `bin_id, s_from_m, s_to_m, n_rows, d0_20_median, a031_median, ..., gof_share_ge05, d0_fwd20 (jesli wlaczone), flags`.
`tsd_run_summary.csv` (na przebieg): zestaw zer, calib_interval, udzialy flag QC, wypelnienie d0.
`UC_<droga>_<jezdnia>_<kierunek>.<rok>.xml`: 43 elementow `DANE` w kolejnosci wzorca; precyzje jak w INWENTARZ 3.3; kodowanie UTF-8 bez BOM, LF.

### 5.4 N4
`sections.csv` (Tab. 3.2 + decyzja), `section_review\*.png` ("linia do linii"), `pairs.csv`, `pairs_null_*.csv`, `agreement.csv` (miary x poziom: para/100 m/przebieg x warianty), `agreement_ci.csv` (metody niepewnosci), `conditions.csv`, `calibration.csv`, `report.html`; `meta.json`.

---------------------------------------------------------------------------------------------------

## 6. Plan testow

Legenda: tolerancja 0,01 w jednostce wielkosci, chyba ze podano inaczej. `@reference` = wymaga danych poza repo (sciezki w `tests\local_paths.yaml`, otwierane tylko do odczytu); `@unit` = dane syntetyczne/male wycinki w `tests\data\`.

### 6.1 N1 (E1)
| ID | Test | Wartosc referencyjna | Tolerancja | Zrodlo |
|---|---|---|---|---|
| T-N1-01 | Wspolczynniki z pakietowego CSV zgodne z `e2a3_final_k_profile.csv` (scope lacznie) | D0 k 0,0161092 / beta 1,60415; D300 0,0123428 / 1,21602; D900 0,00328817 / 0,333874; D200 0,0140162 / 1,38103; D450 0,00958895 / 0,954185; D600 0,00702971 / 0,70652; D1200 0,00214063 / 0,216493; D1500 0,00215554 / 0,215758; D1800 0,00271306 / 0,269251 | 1e-9 (identyczne pliki) | @unit |
| T-N1-02 | `apply_correction` linear/exp analitycznie; identycznosc przy T=20; odwracalnosc | D0=200, T=10: A 232,000 / B 234,702; T=5: A 248,000 / B 254,250; T=25: A 184,000 / B 184,623; T=30: A 168,000 / B 170,429; D300=150, T=10: A 168,000 / B 169,463 | 1e-3 (obl. wlasne) | @unit |
| T-N1-03 | Zgodnosc z `e2aR2_rules.apply_rule` dla tych samych wejsc (kod zrodlowy w `tests\data\ref_apply_rule.py` z naglowkiem pochodzenia) | wartosc identyczna | 1e-9 | @unit |
| T-N1-04 | Wskazniki: SCI300_20 = D0_20 - D300_20, BDI, BCI; przyklad D0=200, D300=150, T=10: A 64,000 / B 65,239 | j.w. | 1e-3 | @unit |
| T-N1-05 | Normalizacja 50 kN: D*50/F; zrzuty nieosadcze; wybor zrzutu | analitycznie | 1e-9 | @unit |
| T-N1-06 | Flagi: T<5, T poza zakresem A/B, brak T, 20,4, przeniesiona (klasyfikacja `classify_session` na wycinku sesji) | oczekiwane etykiety | dokladnie | @unit |
| T-N1-07 | Fit: `qp_fit_nd` / `fit_k_profile` na `e2a3_visits` (848 wizyt; 414 z T_mid 5-30 bez stycznia) odtwarzaja wspolczynniki | D0 beta 1,60415 +-5e-5; k 0,0161092 +-3e-6; SCI300 beta 3,24407; BDI 2,8704; BCI 1,92233 | j.w. | @reference (E1 lub pominiete jesli modul fit poza zakresem) |
| T-N1-08 | Pasma R4 (`l20_error` + `band_mean` na `e2a3_visits`): D0 lacznie no_thaw | 15-20: -0,224 %; 20-25: +0,220 %; 25-30: -1,064 %; 30-35: -3,762 % (n_with_ref 108/110/49/25) | 0,01 pp | @reference (E1 jesli odtworzenie procedury testu w zakresie; inaczej E2) |
| T-N1-09 | Regresja na pliku FWD (XLSX Drops/stations 50_1M): pelny potok; porownanie z recznym obliczeniem | do ustalenia w E1 | 1e-6 | @unit (wycinek <= kilka MB) |

### 6.2 N4 (E2)
| ID | Test | Wartosc referencyjna | Tolerancja | Zrodlo |
|---|---|---|---|---|
| T-N4-01 | `z15_pary_wejscia.csv` + `Z15_temperatury_par.csv` -> `main_after`: mediana ilorazu, SD log, r, rho, CCC, Deming | 1,61584 (SD log 0,321151; r 0,659578; rho 0,580602; CCC 0,346871; Deming log-log 0,958655 / 0,642298); 5511 par; 36 sesji | punktowe 1e-5; mediana 0,01 | @reference |
| T-N4-02 | `main_before` | 1,40644; SD 0,342756; r 0,611999; rho 0,503964; CCC 0,424149; Deming 1,05235 / 0,106303; lambda 0,1178696 | 1e-5 | @reference |
| T-N4-03 | r i rho w obrebie sesji W5 (z `lustro`) | r 0,403905 (0,403); rho 0,338739; none 0,407298; k02 0,402391 | 5e-4 | @reference |
| T-N4-04 | Pary zerowe (`e2b2_null_values` + z15): mediana ilorazu, r globalne | 1,5952 / 1,6098 / 1,5932; r 0,5169 / 0,5242 / 0,4076 | 2e-3 | @reference |
| T-N4-05 | r w obrebie sesji dla par zerowych W5 | wartosci lustro 0,155 / 0,135 / 0,096 vs e2b2b 0,118 / 0,141 / 0,023 — **znana rozbieznosc (Q-N4-1)**; test oznaczony `xfail` do decyzji, zapisuje obie wartosci | wg decyzji | @reference |
| T-N4-06 | Niepewnosc W3: sesyjny M0, WCU, CR2 | M0 [1,53804; 1,65362]; WCU [1,53793; 1,6602] (WCR p 0,9393); CR2 [1,53689; 1,66116] dof 20,5; seed `seed_for('e2x_w3_lacznie', 'wcu'/'wcr')` | 0,01 | @reference |
| T-N4-07 | Warunki (dt, GoF, przeciecie) | dt 0-1: r 0,857391 (119); 2-30: 0,322221 (1873); >30: 0,366773 (3268); GoF>=0,8: 0,814548 (1481); przeciecie 0,83682 (99) | 1e-3 | @reference |
| T-N4-08 | Kalibracja mnoznika, LOSO (k02) | a 1,4222; MAE 27,6747; LOSO MAE 27,7366; mediana abs log 0,227208 / 0,227888 | 0,01 | @reference |
| T-N4-09 | Lambda d0 | 0,11787 (sigma_TSD 0,296408; sigma_FWD 0,101763; n 2015/128) | 1e-4 | @reference (E2d: estymator z surowych tabel daje dokladnie 0,11786960020790811 i n 2015/128) |
| T-N4-10 | Syntetyczne: Deming (a=1,3, b=-0,15, sx 0,10, sy 0,18), CCC (bias 2), BA (bias 2, SD 0), pokrycie CI dla 5/15/35/73 klastrow | wg `test_e2b2.py`, `test_e2x_uncertainty.py` | 0,05/0,08; pokrycie 95 % +-3 pp | @unit |
| T-N4-11 | Geometria (tryb B, jesli w zakresie): `detect_sections` z progami Tab. 3.2 na danych v4 | 445 sekcji; 167 `confirmed`; recall/precision wzgledem 167 | wg decyzji | @reference (E2c: 445/445 sekcji identycznych; 167 `confirmed` = sekcje same/same i same/adjacent kierunku same) |
| T-N4-12 | Zgodnosc z `e1`/`e2b1` testami syntetycznymi (to_2180, kierunek odwrocony, podzial ciagow, warstwy A/B/C/X, pary zerowe) | wg `test_e1.py`, `test_e2b1.py` | wg zrodla | @unit (E2b: `test_geo.py`, `test_geometry_pairs.py`) |
| T-N4-13 | Polozenie plyty FWD, 46826 stacji `odcinki` vs `fwd_plate_position_e2b` | `s_fwd`, `sigma_long`, `era`, `pos_source`, `direction`, `run_id` | 1e-6 (sigma_long 1e-4) | @reference (E2b) |
| T-N4-14 | Kandydaci na pary i pary zerowe, korytarze 0..29 (prefiks `pair_id` 1..5632) vs `golden_pair_candidates`, `e2b1_null_map` | 5632 par; 16659 par zerowych; seed 20261017 | 1e-6 | @reference (E2b) |
| T-N4-15 | Przypisanie wierszy TSD do korytarzy (`prepare_run` + `assign_run`) vs `tsd_sref` | korytarz > 99,95 %; `s_ref_gps` 0,02 m; `lateral_m` 0,003 m | jw. | @reference (E2b) |
| T-N4-18 | Os od zera z 239 plikow TSD ze scalaniem duplikatow pasa vs baza produktow | 165 korytarzy, 43 scalenia, 6 956 291 wierszy, 25 219 punktow wide | dlugosci 1e-3; `s_ref_gps` 1e-3 | @reference (E2f: pelna zgodnosc, max 0,0005 m) |
| T-N4-17 | Wyrownanie przejsc profilem (7 korytarzy, 100 przejsc) vs `tsd_passes`, `tsd_sref` | zrodlo wyrownania, liczba blokow, centrowanie, `s_ref` | `s_ref` 5 mm; centrowanie 1e-4 | @reference (E2e: 0 niezgodnych przejsc, max 1,1 mm) |
| T-N4-16 | Mediana d0 w oknie W5 po `s_ref` vs `d0_tsd` Z15 | >= 99 % par zgodnych < 1e-6 (2888/2895 dla korytarzy 0..80) | 1e-6 | @reference (E2b; roznice = definicja okna S-N4-4) |

### 6.3 N3 (E3)
| ID | Test | Wartosc referencyjna | Tolerancja | Zrodlo |
|---|---|---|---|---|
| T-N3-01 | `p0_integrals` na 9 kanalach z `e2a2_slopes.csv`; wiersz 1a, 2025-09-04, pt 0 | p0_a031 21,6023; p0_a061 39,0758; p0_a091 41,5524; p0_a0361 17,4735; p0_a6191 2,47669; t_a031 22,6437; t_a061 39,7148 | 1e-3 um | @reference/@unit |
| T-N3-02 | Tozsamosci: A0361 = A061 - A031; A6191 = A091 - A061 (P0, T); NaN gdy jakikolwiek kanal NaN; stale przesuniecie zer (`apply_variant`) nie zmienia calek | analitycznie / `test_autc.py` T1-T6 | 1e-9 | @unit |
| T-N3-03 | Calka profilu liniowego `a*(x-x0)`: `P0(x1) = a*(x1^2/2 - x0*x1)` | analitycznie | 1 % + 0,05 | @unit |
| T-N3-04 | d0 W5 i calki P0 w oknie dla par sieciowych vs `e2b2_tsd_values.csv`; para 5288: d0_w5 153 (n=8), a031_w5 28,7412, a0361_w5 38,1424, a6191_w5 37,9944, a061_w5 79,3549, a091_w5 112,049 | wartosci z pliku (mediany calek w oknie) | 1e-6 dla tych samych wierszy | @reference (fixture wierszy B_1510off para do `tests\data`) |
| T-N3-05 | Hampel: szereg staly + outlier; zgodnosc z `tsd_pipeline._hampel_col` na wektorze referencyjnym; brak flagowania przy thr == 0; odrzut calej czaszy | wg zrodla | dokladnie | @unit |
| T-N3-06 | Korekta d0: `d0*exp(0,016*(20-T))`; zakres 5-30 flagowany | analitycznie; T12 TSD mediana 21,8 -> 1,152 przy 8,86 C roznicy | 1e-6 | @unit |
| T-N3-07 | Parser `raw.sup.txt` (plik T4202008060001: 86 kolumn, znak D, `strip_unit`, ok. 6104 wiersze; wiersz 1: Chainage 0, D0 -8342, D300 -7695, Slope 0.110 1453,5559, GoF 0,23790418, Lat 50,091676027, Lon 19,813605221) | wg zrodla | dokladnie | @reference/@unit |
| T-N3-08 | Eksport XML: golden-structure test (struktura z `UC_50_1_M_1.2026.xml`: root, 43 pola, kolejnosc, regexy formatow, puste tylko PROFIL_1/OBC_KPA/blok D-SCI-U_STD, DYSTANS krok 10, `|dKM|`=0,010, UTF-8 bez BOM, LF) + regresja 29 pol typu K na 3 odcinkach | wg [F] 8.2 | dokladnie | @unit/@reference |
| T-N3-09 | Agregacja 50/100 m: bin = floor(s/step), mediana, prog n; flagi | syntetyczne | dokladnie | @unit |
| T-N3-10 | Przeliczenie D0_FWD,20 = m*d0_20 (m 1,62; wartosc odniesienia 1,61584 [1,5382; 1,68335]) | analitycznie | 1e-9 | @unit |

### 6.4 N2 (E4)
| ID | Test | Wartosc referencyjna | Tolerancja | Zrodlo |
|---|---|---|---|---|
| T-N2-01 | Glowny: H v2 (549 obs., 226 sesji), fizyka + kalibracja jednorazowa, 12 cm | RMSE 1,7486 (1,75) [1,6193; 1,8689]; MAE 1,4039; bias +0,2653 | 0,001 (zrodlowa replika: 1,7488 / 1,4042 / +0,2649) | @reference (`z14lite_fwd_walidacja_v3.csv` + cache OM 21 MB) |
| T-N2-02 | Liczebnosci i flagi kalibracji | n 549; sesji 226; ok 294, bound_hi 244, gate 11, bound_lo 0 | dokladnie | @reference |
| T-N2-03 | Po obserwacji vs `phys_single_masa` (`Z14c_candidates.parquet`) | 544/549 zgodne do 1e-6 C; 5 obs. po 23:00 (S-N2-4): <= 0,2 C | wg opisu | @reference |
| T-N2-04 | Komparatory | fizyka bez kalibracji 2,0872 / 1,6974 / +0,9455; BELLS3 2,4065 / 1,8160 / -0,3432 | 0,001 | @reference |
| T-N2-05 | RMSE wg pory | 2,167 (n 49) / 1,378 (n 226) / 1,889 (n 237) / 2,167 (n 37) | 0,005 | @reference |
| T-N2-06 | Solver: stan stacjonarny, bilans energii, round-trip kalibracji (Ts(a*)=target -> a~a*) | analitycznie | 1e-3 | @unit |
| T-N2-07 | Czas/DST/UTC: `om_utc_to_local` (godzina podwojna, luka wiosenna), pomiar o 23:30 | wg opisu | dokladnie | @unit |
| T-N2-08 | Tryb sieciowy: atrapa `http_get` (klient na `urllib`, bez `requests`): `timezone=UTC`, `wind_speed_unit=ms`, 6 zmiennych, okno [start-1 d, end+1 d]; retry 429; tryb offline bez zapytan | wg opisu | dokladnie | @unit |
| T-N2-09 | Dryf parametrow: hash `params_TN.json` | wg zrodla | dokladnie | @unit |
| T-N2-10 | Z15 (2. poziom): 200 par `{fwd,tsd}_t12_cal` vs `Z15_temperatury_par.csv` | zgodne < 1e-6 | 1e-6 | @reference |
Uwaga: test T-N2-01 odtwarza zbior H (eksploracyjny) — to test powtarzalnosci, NIE deklaracja dokladnosci produktu (zbior niezalezny C: 2,73 [2,44; 2,98]).

---------------------------------------------------------------------------------------------------

## 7. Plan etapow i punkty kontrolne

| Etap | Zawartosc | Kryterium zamkniecia | Commit |
|---|---|---|---|
| E0 | INWENTARZ, PROJEKT, DZIENNIK; pytania do Jacka | zatwierdzenie projektu | "E0: inwentarz i projekt" |
| E1 | szkielet, pyproject, srodowisko, CLI, config, `common`, `fwd`; testy T-N1-01..09 | wszystkie testy N1 zielone; tabela "referencyjna / uzyskana / roznica / status" w dzienniku | "E1: szkielet pakietu i N1" |
| E2 | N4: `pairs` na danych bazy (tylko odczyt), potem uogolnienie wejsc; opcjonalnie tryb `geometry` | T-N4-01..10 zielone, rozbieznosc zerowa udokumentowana | "E2: N4 porownanie" |
| E3 | N3: calki, korekta, Hampel, okno, agregacja, eksport XML | T-N3-01..10 zielone, golden-structure XML | "E3: N3 siec i XML" |
| E4 | N2: solver, kalibracja, klient OM, interfejs | T-N2-01..10 zielone | "E4: N2 temperatura" |
| E5 | `INSTRUKCJA_N1..N4.md` dla inzyniera; przyklady uruchomienia na danych testowych | przyklady uruchomione, wyniki zgodne | "E5: dokumentacja" |

Po kazdym kroku: wpis w `docs\DZIENNIK.md` + commit lokalny. Rozbieznosc ponad tolerancje = STOP.
Kolejnosc E2 (N4) przed E3 (N3) i E4 (N2) wynika z promptu; zalezy od niej, ze N4 w E2 uzywa gotowego T12 (z `Z15_temperatury_par.csv`), a N3 — T12 z N2 (E3 uzywa tez wynikow Z15 do testow, N2 powstaje dopiero w E4; w E3 wejscie temperatury z pliku).

---------------------------------------------------------------------------------------------------

## 8. Pytania do Jacka (z proponowanymi domyslnymi)

### 8.0 Decyzje Jacka (zapis; od 2026-11-14)
- **N1 (Q-N1-1..8), 2026-11-14:** Q-N1-1 pelna precyzja z `e2a3_final_k_profile.csv` (Tab. 7.1 jako `tab71`); Q-N1-2 kolumna `T_mid` od uzytkownika, bez interpolacji; Q-N1-3 `mean_nonseating`; **Q-N1-4 tryb legacy porownawczy `legacy_k02` ORAZ dla autostrad `legacy_k01` (k=0,01) — oba wybierane przez `road_type: public | highway`; zrodlo k=0,01 = kod TSDLayerIQ (brzmienie przepisu niezweryfikowane — oznaczyc w meta wyjscia)**; Q-N1-5 liczyc i flagowac wskazniki powyzej 25 C (`INDEX_ABOVE_RANGE`); Q-N1-6/7 czytnik MDB (pyodbc, ReadOnly) w E1, testy bez MDB na wycinku XLSX; Q-N1-8 bez eksportu `UP` w E1.
- **N4, 2026-11-14:** Q-N4-1 test r w obrebie sesji par zerowych = `xfail` (zapis obu wartosci; rozstrzygniecie w E2 po sprawdzeniu definicji okna: po `s_ref` vs zakres `tsd_id`) — **ROZSTRZYGNIETE w E2: N4 odtwarza wartosci raportu (0,155 / 0,135 / 0,096) z e2b2_null_values + Z15 z korekta; rozbieznosc dotyczyla wartosci e2b2b (pary BEZ korekty, inna definicja r w obrebie sesji, odtwarzalna tylko dla +200 m) — `xfail` zostaje tylko dla tych wartosci**; Q-N4-2 regula anteny P043b (8002-367: 5,5 m do 2025-10-09, potem 0); Q-N4-3 do sprawdzenia w E2 (czy -4,8 m wliczone w `s_ref`; znak) — wynik do dziennika; Q-N4-4 najpierw tryb `pairs` (E2), tryb `geometry` jako E2b po zatwierdzeniu E2; Q-N4-5 lambda d0 = 0,11787 z konfiguracji (bez estymatora w E2); Q-N4-6 grupowanie `calib_interval` + `device`, ujemne dt raportowane osobno; Q-N4-7 T12: w E2 plik `Z15_temperatury_par.csv` (tylko odczyt), w produkcji z N2 (CSV z kluczem `pair_id`).
- **N3, 2026-11-14:** Q-N3-10 format XML = DSN zal. H p. 4.2 (profil `dsn_h42`, 21 pol), `UC_Schema.xsd` dostarczy Jacek; Q-N3-13 tylko `dsn_h42` (`extended43` odlozony; Q-N3-2/3/4/5 tym samym bez znaczenia dla E3); Q-N3-1 Hampel jak `tsd_pipeline` (okno +-10 m w metrach, k=3*1,4826, MAD okna, thr>0, odrzut calej czaszy) NA d0 PO korekcie do 20 C, potem mediana +-5 m; Q-N3-6 pikietaz KM/DYSTANS jak w produkcji (kotwica 1. markera Event, DYSTANS = metry co 10); Q-N3-7 `KOD_ODDZ`, `ROK`, `DROGA`, `JEZDNIA`, `PAS` WYMAGANE w konfiguracji (bez domyslnych); Q-N3-8 pliki B_1510off z problemami (align_fail, lata 2020-2023, invalid_scale, missing_channel) flagowane, nie odrzucane; Q-N3-9 calki P0 NIE korygowane temperaturowo (flaga `P0_UNCORRECTED`; D_200/D_300 = d0_20 minus P0); Q-N3-11 "D Tkor" pochodzi z BELLS3_BT (wg Jacka; kod TSDLayerIQ nazywa model XGBoost "Bell3_opt" — nazewnictwo w dokumentacji: "model temperatury BELLS3_BT"); Q-N3-12a `SCI_SUB = D_0 - D_900` (definicja do potwierdzenia po zobaczeniu `UC_Schema.xsd`), Q-N3-12b skala TSD (mnoznik 1,62 tylko opcjonalnie).
- **N2, 2026-11-14:** Q-N2-1 test regresji na H v2 + w dokumentacji uczciwa dokladnosc niezalezna (C v2); Q-N2-2 parametry zamrozone sprzed poprawki czasu OM; Q-N2-3 `NIGHT` = SW_ma6 < 5 W/m2 + flaga `CALIB_GATE`; Q-N2-4 tylko archiwum Open-Meteo; Q-N2-5 u95 = +-2*RMSE_pora, min. 2,2 C, jawnie opisane jako heurystyka; Q-N2-6 `CALIB_BOUND_HI` jako flaga (a_sw <= 1,0); Q-N2-7/8 tylko klasa otwarta (TN), glebokosc 0-50 cm, poza 12 cm flaga `DEPTH_NOT_VALIDATED`; Q-N2-9 cache OM jako sciezka w `local_paths.yaml`.
- **Ogolne, 2026-11-14:** Q-G-1 scipy; Q-G-2 duze dane tylko jako sciezki + `skip`; Q-G-4 normatywne liczby: 5511 par / 36 sesji, 167 odcinkow, 445 sekcji v4; Q-G-5 rozbieznosci raport-kod jako notatki w dzienniku, bez zmiany metod (STOP tylko przy rozbieznosci ponad tolerancje testow); Q-G-3 zdalne repozytorium zaklada Jacek.

### 8.1 Blokujace E1 (N1)
- **Q-N1-1 Zestaw wspolczynnikow.** Domyslnie wariant A/B uzywa pelnej precyzji z `e2a3_final_k_profile.csv` (scope lacznie, dopasowanie 5-30 C), co spelnia testy akceptacyjne z promptu; Tab. 7.1 (zaokraglona: D450 +4 %, D900 -9 %) dostepna jako `coefficient_set: tab71`. Wariant A ma zakres waznosci 5-25 C, ale k pochodzi z dopasowania 5-30 C (dopasowanie 5-25: D0 k=0,01753 wg przeliczenia). Czy tak ma byc?
- **Q-N1-2 Co wchodzi jako T.** Proponuje: kolumna `T_mid` dostarczona przez uzytkownika (wpis operatora / sonda / wynik N2), z flaga zrodla; BEZ interpolacji temperatury w czasie w N1 (poza opcjonalnym polaczeniem z wynikiem N2). Glebokosc 12 cm = "polowa pakietu" dla pakietu 24-25 cm; dla innej grubosci flaga ostrzegawcza (beta zalezy od grubosci, zakres wazny 15-30 cm). Zgoda?
- **Q-N1-3 Regula zrzutu.** Siec: srednia zrzutow nieosadczych; stanowiska/analizy 2.: drugi zrzut. Domyslnie `mean_nonseating`, `second_drop` konfigurowalny. Czy zatwierdzic?
- **Q-N1-4 Regula legacy.** Czy `legacy_k02` (k=0,02 na kazdym czujniku, zakres 5-25 C) ma byc tylko trybem porownawczym? R2 (0,01; 0<T<=35 C) pomijam, bo brzmienie nie zweryfikowane w tekstach zrodlowych (wpis 194 p.6); w `inne\TSDLayerIQ` k=0,02 (droga publiczna) i 0,01 (autostrada) wystepuja jako "wymaganie" w kodzie (bez tekstu przepisu).
- **Q-N1-8 Wyjscie UP (DSN).** Zalacznik H 4.1 definiuje plik XML `UP` dla ugiec FWD/KUAB (rekord `ODCINEK`: KM, ZRZUT, OBC_KN, OBC_KPA, G1..G9, T_POW, T_NAW, LAT, LON, SAT, POMIAR, FOTO, DATA, APARAT; atrybuty DROGA, JEZDNIA, PAS, KIERUNEK, ROK, ODL1..ODL8). Czy N1 ma opcjonalnie eksportowac skorygowane ugiecia do `UP`? Domyslnie: nie w E1 (tylko CSV/XLSX wg promptu); `UP` jako opcja pozniej.
- **Q-N1-7 Odczyt MDB.** `inne\TSDLayerIQ\app\core\io_fwd.py` pokazuje strukture MDB (`Stations`, `Drops`, filtr `History`). Czy MDB jest wiec wymagany w E1 (patrz Q-N1-6)? Domyslnie: modul `fwd/io.py` z czytnikiem MDB przez pyodbc (ReadOnly), testy bez MDB (wycinek XLSX).
- **Q-N1-5 Indeksy powyzej 25 C.** Czy SCI300/BDI/BCI w 25-30 C maja byc liczone i flagowane (domyslnie), czy ukrywane (NaN)? SCI300 wariantu B w 25-30 C jest zanizony srednio ok. 7 %.
- **Q-N1-6 Formaty FWD w E1.** Domyslnie XLSX Drops/stations i CSV; MDB (pyodbc/ODBC) jako opcjonalny modul — wymaga sterownika Access. Czy MDB jest potrzebne w E1?

### 8.2 E2 (N4)
- **Q-N4-1 Pary zerowe — kanoniczne wartosci r w obrebie sesji.** lustro P071: 0,155 / 0,135 / 0,096; przeliczenie z `e2b2_null_values` i `e2b2b`: 0,114-0,118 / 0,134-0,141 / 0,023-0,027. Hipoteza: rozna definicja okna (zakres `tsd_id` vs po `s_ref`). Ktore sa kanoniczne dla testu T-N4-05? Do czasu decyzji test = `xfail`.
- **Q-N4-2 Regula anteny FWD i granica daty.** Domyslnie P043b (8002-367: d=5,5 m do 2025-10-09, potem 0), nie `e1_sref` (5,0 m od 2025-01-01). Zgoda?
- **Q-N4-3 Korekta -4,8 m.** Czy `tsd_position_offset` jest juz wliczona w `s_ref` i okna W5; konwencja znaku. Do ustalenia przed trybem `geometry`. **ROZSTRZYGNIETE 2026-11-14 (z kodu zrodlowego, potwierdzone przez Jacka):** korekta jest wliczona w `tsd_sref` (`e1_sref.py`, `corrected_xy` z lagiem -4,8 m przy budowie `s_ref`), wiec okna W5 po `s_ref` ja zawieraja i w trybie `geometry` stosuje sie ja dokladnie raz (nie dokladac do `s_ref`). Konwencja znaku (lag E0-C): wiersz o pikietazu s dostaje polozenie GPS z `s - lag` = `s + 4,8 m`; punkt pomiaru lezy 4,8 m dalej wzdluz toru niz GPS tego samego wiersza. N3 (brak `s_ref`): `processing.position_offset_m` domyslnie 0 (decyzja Jacka), opcja w konfiguracji w tej samej konwencji (`pos = pikietaz - position_offset_m`; wpisac -4,8 dla korekty).
- **Q-N4-4 Zakres trybu `geometry`.** *(ROZSTRZYGNIETE 2026-11-14: `pairs` w E2, `geometry` w E2b — korytarze, polozenie plyty, kandydaci, pary zerowe, wartosci okien; `detect_sections`, wyrownanie profilem i scalanie duplikatow pasa przeniesione do E2c.)* Tryb `pairs` (gotowe pary + T12) w E2 na pewno. Pelny tryb `geometry` (ok. 3500 linii: korytarze, polozenie plyty, kandydaci, `detect_sections`) — w E2 czy odlozyc do E2b (osobny krok po zatwierdzeniu)? Proponuje: najpierw `pairs`, potem `geometry` jako E2b.
- **Q-N4-5 sigma_FWD i lambda.** *(ROZSTRZYGNIETE 2026-11-14 w E2d: estymator zaimplementowany jako opcja `geometry.lambda_est`; domyslnie lambda z konfiguracji 0,11787, oszacowanie tylko raportowane albo — `apply: true` — uzyte w analizie.)* Domyslnie lambda d0 = 0,11787 (sigma_TSD 0,296408 z par przejazdow w binach po `s_ref`; sigma_FWD 0,101763 z `e12_lambda`); `katalog_produktow.md` zabrania 0,09. Estymator lambda w narzedziu dla nowych danych — czy wlaczyc, czy lambda tylko z konfiguracji?
- **Q-N4-6 Warunek "aparat x okres kalibracji TSD".** Zrodlo uzywa `tsd_year`; raport wymaga `calib_interval` (K2024-03-01, K2025-05-27, K2026-05-19). Domyslnie `calib_interval` + `device`; ujemne dt raportowane osobno.
- **Q-N4-7 Zrodlo T12.** W E2 test czyta `Z15_temperatury_par.csv` z DOKTORAT (tylko odczyt). W produkcji T12 po obu stronach z N2. Zgoda na taka kolejnosc?

### 8.3 E3 (N3)
- **Q-N3-1 Hampel.** Domyslnie parametry `tsd_pipeline` (okno 21 wierszy = +-10 m, k=3*1,4826, MAD prawdziwy okna, thr>0, odrzut calej czaszy) po korekcie temperaturowej d0 (zasada: korekta najpierw), na d0; okno w metrach. Raport nie podaje parametrow; w badaniach par Hampela nie stosowano. Potwierdzenie?
- **Q-N3-2 Pola D_* w XML (zaktualizowane 2026-11-14: dla docelowego profilu `dsn_h42` problem znika — potrzebne tylko D_0, D_200, D_300 i SCI, wszystkie wyznaczalne z d0 i calek P0 do 0,2/0,31 m; dotyczy tylko profilu `extended43`).** D_-450, D_-300, D_-200, D_450, D_1200, D_1500 NIE sa wyznaczalne z d0 + calek P0 (D300..D1500 producenta bezuzyteczne, wlasny model czaszy odrzucony). Co ma trafic do tych pol: puste, wartosci z innego zrodla, czy zmiana formatu? To decyzja wymagana przed E3.
- **Q-N3-3 U_STD, SCI_200, SCI_300.** Dokument UC: U_STD = D_0 skorygowane temperaturowo (k=0,02, T_DROGI_OBL), SCI z nieskorygowanych D; obecny `tsd_to_xml.py`: U_STD = D_0 po konwersji. Nowa definicja (d0_20 * m? A031 w skali TSD?).
- **Q-N3-4 Skala D_* w XML.** Skala TSD (d0_20) czy ekwiwalent FWD (m * d0_20, m=1,62)? Domyslnie: skala TSD, mnoznik tylko opcjonalnie.
- **Q-N3-5 T_DROGI_OBL.** Zrodlo: T12 z N2 (nie `T_XGB(120)`, ktorego nie ma w naszych eksportach). Domyslnie T12 z N2.
- **Q-N3-6 Pikietaz KM i DYSTANS.** Domyslnie zachowanie referencyjne (kotwica z 1. markera Event, DYSTANS = metry co 10); opcja interpolacji odcinkowej miedzy markerami (dryf do 24 m na 50_1M). DYSTANS: metry (produkcja) czy numer kroku (przyklad docx)?
- **Q-N3-7 Stale XML i schemat.** `KOD_ODDZ` (WA/OP), `ROK`, `DROGA/JEZDNIA/PAS`, `F_P`; dostep do `UC_Schema.xsd` (walidacja).
- **Q-N3-8 Wejscie B_1510off.** Eksport tworzy Jacek programem producenta; N3 nie przelicza. Czy zestaw zer (A/B/C/B_1510off/NEW) ma byc atrybutem w konfiguracji (z `calib_interval`)? Czy N3 odrzuca pliki `align_fail`, lata 2020-2023, pliki z `invalid_scale`?
- **Q-N3-10 Format XML — ROZSTRZYGNIETE 2026-11-14 (Jacek):** docelowy = format DSN, czyli `UC` z `inne\DSN_Zal.H.pdf` zal. H, p. 4.2 (str. 24). To ten sam "UC", a nie schematy `wdsn` Hellera z `inne\xml\arch\` (starszy, inny format PP-U; nie implementujemy). Zal. H 4.2 definiuje 21 pol: KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1, PREDKOSC, STRAIN_GAUGE, T_DROGI, T_POW, SCI_200, SCI_300, SCI_SUB, D_0, D_200, D_300 (atrybuty korzenia KOD_ODDZ, ROK; `UC_Schema.xsd` — Jacek dostarczy). Rozszerzony 43-polowy `UC_*.xml` z `tsd_2_xml` (m.in. T_DROGI_OBL, F_P, OBC_KN, U_STD, D_-450...D_1500, 10 x SLOPE) jest lokalnym rozszerzeniem poza zalacznikiem. Domyslnie: profil `dsn_h42` (21 pol); profil `extended43` jako opcja. Uwaga: w XSD z zalacznika element glowny nazywa sie `TSD`, a w przykladzie `UC` — rozstrzygnie dostarczony `UC_Schema.xsd`.
- **Q-N3-12 Definicja SCI_SUB i skala pol. — ZAMKNIETE 2026-11-14 (Jacek): SCI_SUB pomijane, w XML pusty element.** Zalacznik H nie definiuje `SCI_SUB` (przyklad: D_0 396,692; SCI_200 62,809; SCI_300 119,458; SCI_SUB 178,889). Czy SCI_SUB = D0 - D600, D0 - D900, czy inaczej? Czy SCI_200 = D_0 - D_200 (przyklad nie spelnia tej rownosci: 396,692 - 328,811 = 67,881 != 62,809, dane z 2012-14 liczone inna procedura)? D_0, D_200, D_300 — w skali TSD (d0_20 i calki P0 do 0,2/0,31 m) czy ekwiwalent FWD (mnoznik 1,62)? Domyslnie: skala TSD, D_x = d0_20 - calka P0 do x, SCI_200 = D_0 - D_200, SCI_300 = D_0 - D_300, SCI_SUB = D_0 - D_900 (tylko jesli potwierdzisz).
- **Q-N3-13 Profil `extended43`.** Czy w E3 zrobic tez rozszerzony format 43-polowy (jak `UC_*.xml`), czy tylko 21 pol z zalacznika H? Domyslnie: tylko `dsn_h42`; `extended43` odlozony.
- **Q-N3-11 Nazwa modelu temperatury.** Raport/prompt: "D Tkor" z BELLS3_BT; kod TSDLayerIQ/`soft_xgb`: `T_XGB(120)` = model XGBoost "Bell3_opt" z reczna `one_day`. Czy to ten sam model, i czy w naglowku nowego XML nalezy go nazywac inaczej? W nowym narzedziu T z N2.
- **Q-N3-14 Zrodlo nachylen do calek P0 (nowe, E3).** N3 liczy P0 z nachylen eksportu B_1510off (jak w specyfikacji). Wartosci referencyjne `a031_w5` itd. w `e2b2_tsd_values.csv` liczono z nachylen eksportu pgc (inny zestaw zer, wspolne przesuniecie ok. +20 um/m): np. para 5288 — mediana calki a031 w oknie 28,74 (e2b2) vs 30,43 (B_1510off z tych samych wierszy); d0 identyczne (153, n 8). Czy kanoniczne dla N3 sa nachylenia B_1510off (domyslnie, zgodnie z promptem), czy pgc?
- **Q-N3-15 Pikietaz KM i data (nowe, E3).** Eksport B_1510off nie ma kolumn `Event` ani `DateTime`/IRI, wiec "kotwica z pierwszego markera Event" (produkcja) nie jest mozliwa: KM = `km_start` + znak * (pikietaz - `chainage_start_m`)/1000 z konfiguracji (kierunek `km_direction`); data z nazwy pliku (`T4RRRRMMDDNNNN`) lub `date_override`; godzina z kolumny `GPS time` (hhmmss). IRI_1 i PROFIL_1 puste. Potwierdzenie?
- **Q-N3-16 Punkty calkowania D_200/D_300/SCI_SUB (nowe, E3).** W XML uzyto dokladnych odleglosci: D_200 = d0_20 - P0(0,20), D_300 = d0_20 - P0(0,30), SCI_SUB = P0(0,90) (= D_0 - D_900); SCI_300_TSD z raportu (0-0,31 m) i `a031` sa liczone osobno w CSV. Czy D_300 ma uzywac 0,31 m (polozenie czujnika) zamiast 0,30 m?
- **Q-N3-9 Korekta calek P0.** Domyslnie NIE korygowane wspolczynnikami FWD (raport 6.1), raportowane z flaga i bez korekty; A031/A0361/A6191 <= 0 w 32-41 % par.

### 8.4 E4 (N2)
- **Q-N2-1 Referencja.** Zbior H v2 (549/226, RMSE 1,749) czy C v2 (2,73/3,08)? W kodzie H v2 = "Tab. 4.2", "Tab. 4.3" = C v2. Test regresji na H v2; w dokumentacji uczciwa dokladnosc na zbiorze niezaleznym.
- **Q-N2-2 Parametry zamrozone.** Pre-omfix (E2-T05, odtwarza 1,749) czy po poprawce czasu OM (`_omfix_check`; roznica <= 0,02 C)? Domyslnie pre-omfix.
- **Q-N2-3 Flaga pory.** NIGHT = SW_ma6 < 5 W/m2 (z OM), lub godziny aparatu 0-6/18-24, lub flaga `gate`? Domyslnie SW_ma6 < 5 W/m2 (+ `gate`).
- **Q-N2-4 Open-Meteo tylko archiwum.** Pomiary sprzed < ok. 5 dni nie maja pelnych danych; brak trybu forecast. Akceptujemy?
- **Q-N2-5 Niepewnosc.** u95 = +-2*RMSE_pora (heurystyka z H v2), dolna granica 2,2 C. Czy takie sformulowanie jest dopuszczalne?
- **Q-N2-6 a_sw > 1.** Kalibracja moze tylko zmniejszac a_sw (a <= 1,0); 44 % H = bound_hi. Zostawic jako flage CALIB_BOUND_HI (domyslnie).
- **Q-N2-7 Klasa zacieniona.** Pomijamy (TODO); model TN ma na terenie zacienionym bias +3..+5 C. Flaga SHADED_SITE_SUSPECTED nie jest wykrywana (brak danych) — tylko uwaga w dokumentacji.
- **Q-N2-8 Glebokosc.** Narzedzie umie liczyc na dowolnej glebokosci 0-50 cm (siatka 1 cm), ale walidacja tylko 12 cm (10 cm w 258 wierszach). Dla innych glebokosci flaga `DEPTH_NOT_VALIDATED`.
- **Q-N2-9 Cache OM w repo.** Czy dopuszczalna kopia cache testowego (21 MB) w `tests\data`? (prompt: duzych danych nie kopiujemy; > kilka MB -> sciezka w konfiguracji.) Proponuje sciezke do odczytu w `local_paths.yaml`.

### 8.5 Ogolne
- **Q-G-1 Scipy.** Zaleznosc od scipy akceptowana (PCHIP, brentq); alternatywa — reimplementacja numpy (bisekcja QP + zlota sekcja dla fit; PCHIP wlasny trudniejszy). Domyslnie scipy.
- **Q-G-2 Dane testowe.** Duze dane tylko jako sciezki do odczytu w `tests\local_paths.yaml`; wycinki do kilku MB w `tests\data`. Testy `@reference` pomijane (skip) gdy brak sciezek.
- **Q-G-3 Repozytorium.** `git init` wykonane; zdalne zaklada Jacek, wtedy push.
- **Q-G-4 Liczby bazowe** (sesje 253/251/250; pary 9201/9132/6087/5511; sekcje 444/445) — normatywne dla testow: 5511 par / 36 sesji, 167 odcinkow, 445 sekcji v4. Potwierdzenie.
- **Q-G-5 Raport jako zrodlo zmian.** Rozbieznosci miedzy raportem a kodem (np. Tab. 7.1 zaokraglona vs CSV) zapisuje w dzienniku jako notatki, bez zmiany metod.
