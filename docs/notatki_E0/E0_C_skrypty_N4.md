# E0-C: skrypty SQL_TSD_FWD istotne dla narzedzia N4 (tsd_fwd_compare, raport PW.S-1063 p. 7.2)

Tryb: TYLKO ODCZYT. Przeczytano kod w C:\projects\sql_tsd_fwd\bak, tabele w ...\tabele, schematy baz przez `file:...?mode=ro`
(tylko `sqlite_master`, `COUNT(*)` i pojedyncze wiersze). Nic nie zapisano poza tym plikiem i skryptami pomocniczymi w scratchpadzie.
Wszystkie sciezki skryptow: `C:\projects\sql_tsd_fwd\bak\<nazwa>`. Kod bez polskich znakow diakrytycznych w komentarzach; w tym pliku tez.

## 0. Skrypty z zadania - status

| Skrypt | Status |
|---|---|
| e1_sref.py (2240 l.) | ZNALEZIONY, opis w p. 2.1 |
| e1_* (inne) | jedyny drugi plik o tym prefiksie to e1b_version.py (914 l.) - p. 2.2; e14_*, e12_*, e13_* to inne etapy (nieopisywane) |
| match_sections.py (533 l.) | ZNALEZIONY, p. 2.3 |
| rebuild_sections.py (429 l.) | ZNALEZIONY, p. 2.4 (logika progow siedzi w `build_road_db.detect_sections`, p. 2.5) |
| section_manual_checks.py (116 l.) | ZNALEZIONY, p. 2.6 |
| e2b1_geometry.py (918 l.), e2b1_pairs.py (561 l.), e2b1_catalog.py (81 l.) | ZNALEZIONE, p. 2.7-2.9 |
| e2b2_agreement.py (797 l.) | ZNALEZIONY, p. 2.11 |
| **e2b1_null_*** | **NIE ISTNIEJE jako skrypt.** Pary zerowe (+-200 m, permutacja) sa w `e2b1_pairs.py` (krok K8, funkcja `build_null_pairs`) -> tabela `e2b1_null_map` / CSV `tabele\e2b1_null_map*.csv`; ich wartosci w `e2b2_values.py` (`build_null_values`, tabela `e2b2_null_values`), test zerowy B4 w `e2b2_agreement.py` (`build_null_test`), bootstrap sparowany w `e2b2b_extra.py` (`paired_bootstrap_null`), wersja "lustro" w `e2bR9_lustro_warianty.py` (krok 4). Pliki `e2b1_null_*.csv` istnieja tylko jako tabele. |
| e2x_uncertainty_methods.py (802 l.) | ZNALEZIONY, p. 2.12 (+ e2x_tab62_male_klastry.py, 252 l., p. 2.13) |
| e2bR9_lustro_* (data, warianty, warunki, kalibracja, plot) | ZNALEZIONE (5 plikow), p. 2.14 |
| baza_odcinki_v4 | to PLIK bazy `bazy\baza_odcinki_v4.db` (nie tabela); p. 4 |

Dodatkowo (poza lista, ale niezbedne do rozumienia N4 - opisane skrotowo w p. 2.15): `paths.py`, `datasets.py`, `e0b_t20_defl.py`
(corrected_xy, heading_of, angdiff, resample, running_median_nan), `e0_fwd_temp.py` (sqlite_uri), `e2b2_values.py` (wartosci FWD/TSD par, lambda),
`e2b2b_extra.py` (bootstrap sparowany), `z15_pairs_export.py` + `z15_temp_correction.py` (korekta do 20 C, main_after), `e2aR2_rules.py` (apply_rule),
`build_road_db.py` (`detect_sections`, DDL), `e2a1b_position.py` (`unit_factor`, `anchor_of`, `robust_sd`).
W repo istnieje tez kopia robocza `.claude\worktrees\adoring-colden-d22ad7\bak\...` - nie czytana (potencjalna rozbieznosc wersji).

## 1. Lancuch przetwarzania i zaleznosci (od surowych danych do wartosci z raportu)

```
build_road_db.py  -> baza_odcinki_v4.db: tsd_files, tsd_measurements, fwd_files/sessions/stations/drops, tsd_fwd_sections (detect_sections)
rebuild_sections.py (-> detect_sections z build_road_db) -> tsd_fwd_sections z progami Etapu 1 (Tab. 3.2)
verify_sections.py (reczny przeglad, poza zakresem) -> tsd_fwd_section_review (167 'confirmed')
section_manual_checks.py -> section_manual_checks (1 wiersz)
match_sections.py --match-set stage1_capture -> tsd_fwd_links (24489 linkow)
stage2_sections_view.py -> v_stage2_sections (167 wierszy, 167 stage2_eligible)
e1_sref.py (importuje e0_fwd_temp, e0_t20_lag.open_v4, e0b_t20_defl) -> baza_produkty_v1.db: ref_corridors, ref_corridor_points, tsd_sref (s_ref), tsd_passes,
     fwd_station_position, fwd_sref, tsd_bin_stats, e1_bin_pairs, ...  [pikietaz wspolny TSD i FWD]
e1b_version.py (importuje e1_sref, e0b) -> diagnostyka wersji rejestratora, FWD jako odniesienie (OLS CR1)  [opisowe]
e2b1_geometry.py (importuje e1_sref, e2a1b_position, datasets, paths) -> baza_analizy_e2b.db: fwd_plate_position_e2b, fwd_session_runs, e2b1_params
e2b1_pairs.py (importuje e2b1_geometry) -> golden_pair_candidates, e2b1_null_map, e2b1_inventory, e2b1_layer_sensitivity
e2b2_values.py (importuje e2b1_pairs, denoise, e2a_autc_1b, e2a2b_beta) -> e2b2_pairs, e2b2_fwd_values, e2b2_tsd_values, e2b2_null_values, e2b2_lambda
e2b2_agreement.py (importuje e2b2_values, e1_sref.make_logger, e0_fwd_temp) -> e2b2_agreement, e2b2_null_test, e2b2_rule_c, e2b2_deming_lambda_sens
e2b2b_extra.py -> e2b2_null_test_paired, e2b2_gof_variants, e2b2_curv_reference
z15_pairs_export.py -> tabele\z15_pary_wejscia.csv (5511 par)  ->  [DOKTORAT: Z15_temperatury_par.csv, T12 obu stron]  ->  z15_temp_correction.py
     (importuje e2b2_agreement.deming/point_stats/bootstrap_ci, e2aR2_rules.apply_rule) -> tabele\z15_korekta_TSD_FWD_*.csv  [main_after]
e2x_uncertainty_methods.py (importuje e2a3e/e2a3i/e2a3d/e2a3f/e2aR_equivalence/e2aR4 + z15_temp_correction + e2aR2_rules) -> e2x_niepewnosc_*.csv
e2x_tab62_male_klastry.py (importuje e2x_uncertainty_methods, e2a4*, e2aR_equivalence)
e2bR9_lustro_data.py (importuje datasets, e0_fwd_temp, e2aR2_rules) <- e2bR9_lustro_warianty.py (importuje e2x_uncertainty_methods, e2b2_agreement, e2a3e_range)
     -> pickle logi\E2b\e2bR9_lustro_reps_cache.pkl <- e2bR9_lustro_kalibracja.py, e2bR9_lustro_warunki.py ; e2bR9_lustro_plot.py (tylko CSV)
```
Wszystkie skrypty zrodlowe maja twarda zasade MD5 baz R2 przed = po, `paths.release_guard` (zapis do baz wydania tylko z `--allow-release-write`),
bazy v4 / produkty otwierane `mode=ro`.

## 2. Opis skryptow

### 2.1 e1_sref.py - referencyjny pikietaz s_ref, korytarze (Etap E1-1, wpis 35)

Plik: C:\projects\sql_tsd_fwd\bak\e1_sref.py. Uruchomienie: `python bak\e1_sref.py --dataset odcinki|odcinki_1km|mikroodcinki [--db --out-db --bin-m 10 --workers 8 ...]`.
Wejscie: `v4.tsd_measurements` (kolumny GEO_COLS: tsd_id, chainage_m, latitude, longitude, speed_ms, profile1, datetime; plus d0..d1500, slope_0210/0310,
deflvel_0310, goodness_of_fit, temp_road, temp_air, strain_*, pavement_class), `v4.tsd_files` (row_count, file_date, filename, meta_json -> ProfileRecorderVer),
`v4.fwd_stations` (+fwd_files.trailer = aparat, time, lat, lon, heading_deg), `v4.fwd_sessions` (facility_name), `v4.tsd_gps_data_qc` (verdict_pair='PRZESUNIETY' -> plik wykluczony),
opcjonalnie `v4.tsd_gps_bad_segments` (strefy zlego GPS -> pikietaz z drogomierza), `v4.tsd_fwd_sections/section_review/links` (walidacja a).
Wyjscie (baza produktow, tabele DROP/CREATE): tsd_position_offset, fwd_station_position, ref_corridors, ref_corridor_merges, ref_corridor_points (corridor_id, s, x_2180, y_2180, heading_deg),
tsd_sref (tsd_id, file_id, corridor_id, pass_id, s_ref_gps, s_ref, lateral_m, align_source, unassigned_reason, lane_fit), tsd_passes, tsd_align_blocks, fwd_sref (station_id, corridor_id, s_ref, lateral_m, lane_match same/adjacent/none),
tsd_bin_stats (korytarz x bin 10 m x przejscie, mediany/MAD wartosci SUROWYCH), e1_valb_blocks, e1_validation, e1_section_check, e1_bin_pairs, e1_repeat_inventory; wykresy plots\e1.

Funkcje publiczne (sygnatury):
- `to_2180(lat, lon)` -> (E, N) [m]; GRS80, szereg Krugera do n^4, lon0=19, k0=0,9993, FE=500000, FN=-5300000. Kolejnosc (E, N) = (x, y) matematyczna (w geodezji PUWG X=N, Y=E).
- `convergence_deg(lat, lon)` - zbieznosc poludnikow (1. rzad): azymut siatki = azymut geograficzny - gamma.
- `shift_along(lat, lon, hd_deg, dist_m)` - przesuniecie punktu geograficznego wzdluz azymutu o dist_m (lokalne promienie krzywizny GRS80).
- `group_median(gid, vals, G)`, `group_mad(gid, vals, med, G)`, `runs_of(mask)`, `split_segments(xc, yc)`.
- `class Corridor(cid, x, y, src)`: `set_geom(x, y, hd=None)` (s = skumulowana dlugosc luku, hd = kurs siatki, cKDTree, bbox, length), `near(bb, margin=LOOSE_M)`, `end_dir(which)`.
- `project_on(c, px, py, phd, max_lat, heading=True)` -> (s, lateral, dh, ok); `best_projection(corrs, px, py, phd, max_lat, heading=True)` -> (cid, s, lateral); `bbox_of(x, y)`; `try_extend(corrs, sx, sy)`.
- `build_corridors(files, log)`, `refine_geometry(c, pts_s, pts_lat)`, `parallel_close(corrs)`, `find_merges(corrs)`, `apply_merges(files, corrs, merges)`, `pass_groups(cid, s)`, `classify_unassigned(corrs, px, py)`, `assign_task(task)`, `run_assign(files, corrs, workers, classify)`, `gather_by_corridor(A, G)`.
- Wyrownanie profilem: `overlap_blocks(both, block)`, `block_lag(y_ref, y_run, y_run_h, b0, b1, min_pairs, lmax=ALIGN_LMAX)`, `align_blocks(y_ref, y_run, y_run_h=None, block=None, min_pairs=None, r_min=None, lmax=None)`, `delta_fn(blocks)`, `loo_residuals(fn)`, `align_corridor(passes, L, log_rows)`, `apply_odometer_anchor(d, segs, corrs)`.
- FWD: `antenna_rule(dev, date)` -> (d [m], confirmed, zrodlo), `fwd_positions(conn)`.
- Walidacje: `synthetic_alignment(seed=SEED, length=8000, shift=2.3, drift_per_km=0.8, noise=0.3)`, `validate_a(conn, files, excluded, F)`, `validate_b(by_corr, corrs, rng)`.
- Pomocnicze: `load_geometry(task)`, `bin_stats_task(task)`, `insert_rows`, `pctl`, `fq`, `to_py`, `iso_t`, `noon_epoch`, `robust_sd`, `recorder_group(v)`, `make_logger(path)` (importowane przez prawie wszystkie skrypty E2), `snapshot_tables`, `run(args, conn, db_abs, log, t0)`, `main()`.

Co liczy:
1. Krok 0 - stale: `TSD_OFFSET_M = -4,8` m (niepewnosc 1,5 m) w konwencji lagu E0-C: `e0b_t20_defl.corrected_xy(s, x, y, lag_m)` daje wierszowi o chainage s polozenie GPS z chainage `q = s - lag = s + 4,8` (GPS "z przodu" o 4,8 m; interpolacja liniowa po chainage, poza zakresem NaN). Jedna stala globalna dla wszystkich plikow (lag zyroskopu per plik tylko QC).
   Plyta FWD: `ANTENNA_RULES = {'8002-367': (5,0; 0,0; confirmed 1), '8082-119': (1,0; 1,0; 1), '8002-369': (1,0; 1,0; 0)}`, `ANTENNA_CUTOFF = '2025-01-01'` (porownanie napisow dat `date >= cutoff`). Plyta = punkt GPS stacji przesuniety o d WSTECZ wzdluz `heading_deg + 180` (`shift_along`); brak kursu -> kurs z sasiednich stacji sesji (`111320 m/st` przyblizenie), brak kursu i GPS -> plyta = GPS. Niepewnosc anteny `ANTENNA_UNC_M = 0,5`.
2. Krok 1 - korytarze: przejazd dzielony na ciagi (`SEG_JUMP_M=5` m skoku, `SEG_HEAD_DEG=60` na `SEG_HEAD_ROWS=10` wierszach = zawracanie, `SEG_MIN_M=20`); kurs `heading_of` z roznicy centralnej +-5 wierszy (HEAD_HALF=5) w 2180; ciagi malejaco wg dlugosci; punkt nalezy do korytarza gdy `|lateral| <= LANE_HALF_M = 1,75` m i `|dh| <= HEAD_TOL_DEG = 30` stopni (kurs siatki); nieprzypisane odcinki >= `NEW_MIN_M = 200` wierszy tworza korytarz lub go przedluzaja (`EXT_GAP_M=15`); os = mediana poprzeczna w binach 1 m wygladzona srednia ~`REF_SMOOTH_M=20` m, 1 iteracja; `lateral_m` ze znakiem (+ = w lewo od kierunku jazdy, `lat = cross(v, p)/|v|`). Korytarze krotsze niz 2000 m i bliskie (<= 2,5 m, kurs zgodny, >= 50 % dlugosci) innemu dluzszemu sa scalane ('wide', `MERGE_WIDE_M = 4,25`).
3. Krok 2 - wyrownanie profilem: sygnal `profile1 - mediana biegnaca 101 m (DETREND_W)`; bloki ~1000 m (`ALIGN_BLOCK_M`; dla odcinki_1km/mikro 400 m, min. par 250), lag +-15 m, maks. korelacji (parabola, srednia z wariantem polprobkowym +0,5 m), `r >= 0,8` (ALIGN_R_MIN), odrzucenie blokow > 3 m od mediany; delta(s) odcinkowo-liniowa; `s_ref = s_ref_gps + delta(s)` (po odjeciu mediany delta przejsc wyrownanych = rama GPS stacji FWD). Brak wyrownania -> `align_source='gps'` (note: no_profile / short / no_block_r08); strefy zlego GPS -> `odometer_anchor` (drogomierz zakotwiczony: `s = znak*chainage + c`, MAD <= 5 m).
4. Krok 3 - stacje FWD: rzut POLOZENIA PLYTY (x_2180, y_2180) na korytarze, kurs `hd_grid = (heading_deg - convergence_deg) % 360`; `lane_match`: 'same' gdy `|lat| <= 1,75`, inaczej 'adjacent' gdy `<= FWD_ADJ_M = 5,0`, inaczej 'none'. s_ref FWD wylacznie z GPS (bez wyrownania profilem).
5. Krok 4 - `tsd_bin_stats`: bin = `floor(s_ref / bin_m)`; pokrycie biny `n >= COVER_MIN_N = 5`; wariant GoF `goodness_of_fit >= GOF_MIN = 0,5` (>= `N_GOF_MIN = 3` wierszy d0). Kolumny `*_med`, `*_mad` (MAD bez 1,4826), `*_n`, `*_gof05_med` z wartosci SUROWYCH v4 (bez odszumiania; d0 z v4 jest "nominalny" - patrz p. 2.14 dla B_1510off).
6. Krok 6 - `e1_bin_pairs` (pary przejsc w tym samym binie): `dt_days`, `dT_bin`, `dT_50m` (temp_road), `dV`, `gof_both`, `concrete`, `same_version`. Z tego `e2b2_values` bierze pary z `dt_days <= 1 AND concrete = 0` do lambda (p. 2.15).
Stale na sztywno: patrz lista w kodzie linie 72-114 (LANE_HALF_M, HEAD_TOL_DEG, NEW_MIN_M, SEG_*, ALIGN_*, FWD_ADJ_M, COVER_MIN_N, GOF_MIN, VAL_*, `SEED=20260927`) + GRS80/PUWG; `DEFL_COLS`, `AUX_COLS`.
Pulapki:
- Znak: `corrected_xy` lag = -4,8 => GPS z przodu o +4,8 m wzgledem wiersza TSD (odpowiada "kanaly danych sa 4,8 m za GPS"). Odwrocenie znaku daje blad 9,6 m. Nie mylic z przesunieciem anteny FWD (to wstecz od anteny do plyty).
- Pikietaz s_ref rosnie wzdluz kierunku jazdy KORYTARZA (kierunek pierwszego/najdluzszego ciagu); przeciwny kierunek/pas = OSOBNY korytarz (heading 30 st.). `chainage_m` TSD zakladany rosnacy z jazda. `lateral_m > 0` = lewa strona.
- Kierunek FWD: `heading_deg` w v4 liczony `build_road_db.compute_headings` z KOLEJNOSCI stacji sesji (roznica centralna GPS, min. przerwa 1 m), nie z `station_m`. Docstring detect_sections zaznacza, ze `station_m` bywa rosnace albo malejace wzdluz jazdy (konwencja MDB). `e1_sref` zaklada, ze plyta jest "wstecz" od anteny wzdluz `heading+180`.
- Dwa rozne zestawy regul anteny: e1_sref (8002-367: 5,0 m przed 2025-01-01, 0 od 2025) vs e2b1_geometry (5,5 m do 2025-10-09, potem 0; warianty 5,0/5,5/6,0). Wartosci w `fwd_sref` (R2) wg pierwszej reguly, w `fwd_plate_position_e2b` wg drugiej (p. 2.7). N4 musi miec JEDNA parametryzowana regule.
- Udokumentowany blad etykiety aparatu w R2 dla zbioru mikroodcinki (wszystkie 1347 stacji w `fwd_station_position` jako 8002-367, w tym 90 stacji HWD) - wg docstringu `hwd_diagnostic` w e2b1_geometry; nie dotyczy zbioru odcinki.
- Wiele progow pasa w roznych miejscach: sekcja (0,75 / 2,0 m, kryterium Tab. 3.2), korytarz (1,75 / 5,0 m), warstwy jakosci A/B (|dlat| <= 1,0 / 1,75 m). Nie sa tym samym.
- `tsd_sref.lane_fit = 'lane'` vs 'wide': e2b1 i lustro uzywaja tylko 'lane' (`<= 1,75 m`); `--lane-all` (domyslnie True dla odcinki_1km, mikro) wylacza rozroznienie.
- Bin pokryty gdy n >= 5 wierszy; w mediane NaN pomijane; MAD nieskalowane.
- v4 tylko przez `ATTACH ... ?mode=ro` do bazy w pamieci (`open_v4`), `Pool` (multiprocessing) - Windows: wymaga `if __name__ == '__main__'`.
- Test: `bak\test_e1.py` (T1 ... T21: m.in. poludnik srodkowy, symetria 19 E, skala 2. rzedu, zbieznosc poludnikow, synteza `synthetic_alignment`), `bak\test_e1_regression.py` (przebieg ~3 min vs baza_produkty_v1.db, tol 1e-9).

### 2.2 e1b_version.py - diagnostyka wersji rejestratora, FWD jako wspolne odniesienie (E1-1b, wpis 37)

Plik: C:\projects\sql_tsd_fwd\bak\e1b_version.py (914 l.). Importuje z e1_sref (COVER_MIN_N, D_COLS, GOF_MIN, N_GOF_MIN, group_median, insert_rows, make_logger, recorder_group) i `e0b_t20_defl.ols_cluster_terms`.
Funkcje: `fam_of(ch)`, `off_of(ch)`, `qstats(v)`, `file_task(task)`, `pair_class(gl, ge)`, `dt_class(dt_days)`, `diff_stats(a, b)`, `ratio_stats(a, b, extra=None)`, `plot_*`, `run(args, conn, log, t0)`, `main()`.
Wyjscie (baza produktow): e1b_channel_file, e1b_channel_group, e1b_file_time, e1b_pair_stats, e1b_fwd_stations, e1b_fwd_units, e1b_fwd_model, e1b_merge_effect.
Co liczy: (A) kanaly wg wersji rejestratora ProfileRecorderVer (grupy 1.7/1.0/2.0/brak): per plik i grupa n, mediana, P25/P75, udzial ujemnych; w tych samych binach pary |dT| < 3 C (`DT_MAX_C`): roznice (pozniejsze - wczesniejsze) dla deflvel/slope/doppler, ilorazy exp(mediana log) dla d0...d1500; (B) FWD jako odniesienie: stacje 'same', TSD = mediana d0 binu stacji w przejsciach z tego samego roku (n >= 5), FWD = srednia d1*50/F zrzutow nieosadczych; jednostka = sesja FWD x przejscie TSD (>= `FWD_UNIT_MIN` = 5 stacji), model `mediana log(FWD/TSD) ~ grupa wersji + aparat + strefa betonu + log FWD` OLS z bledem klastrowym CR1 po sesji; (C) skutki scalania korytarzy. `SEED=20260928`. DT_EDGES (30 d, 0,5 / 1 / 1,5 / 2 / 3 lata).
Dla N4: DIAGNOSTYKA OPISOWA, nie funkcja przeliczenia; wazny wniosek (ilorazy poziomow kanalow miedzy wersjami 2.0/1.0 rejestratora) wskazuje, ze zmienna `recorder_group` powinna byc kolumna wejsciowa/warunkiem.

### 2.3 match_sections.py - dopasowanie stacji FWD do punktow TSD w sekcji (krok 2 section-first)

Plik: C:\projects\sql_tsd_fwd\bak\match_sections.py. CLI: `--db --match-set --radius (100) --gather-xtrack (6) --deviation (2) --bearing-tolerance (30) --lane-filter same,adjacent --allow-opposite --max-days --min-section-length-m --min-corr`.
Funkcje: `setup_logging(log_path)`, `haversine_m(lat1, lon1, lat2, lon2)`, `bearing_diff_deg(a, b)`, `cross_track_signed_m(p_lat, p_lon, ref_lat, ref_lon, ref_heading_deg)` (znak: + = punkt na PRAWO od kursu; UWAGA odwrotnie niz `lateral_m` w e1_sref, gdzie + = lewo), `_parse_dt`, `bearing_ok(bdiff, direction, tol)`, `match_sections(conn, allow_opposite, radius_m, gather_xtrack, deviation, bearing_tolerance, lane_filter, match_set='default', max_days=None, min_section_length_m=None, min_corr=None)`, `main()`.
Wejscie: `tsd_fwd_sections` (nie odrzucone: `NOT EXISTS review.status='rejected'`; filtr kierunku i lane_class z COALESCE 'unknown'), `tsd_measurements` (lat, lon, heading_deg, chainage_m, datetime), `fwd_stations` (lat, lon, time, heading_deg, station_m). Wyjscie: `tsd_fwd_links` (tsd_id, station_id, distance_m, cross_track_m, bearing_diff_deg, quality_flag='ok', is_primary, time_diff_days, tsd_date, fwd_date, match_set) - czysci TYLKO swoj match_set.
Algorytm per sekcja (session_pk, tsd_file_id, direction): kandydaci = najblizszy punkt TSD w `radius_m` od stacji (przyblizenie plaskie `lon*111320*cos(lat0)`, `lat*111320`, cKDTree, potem haversine), `|xtrack| <= gather_xtrack` (kurs TSD, zapas FWD), kierunek wg `bearing_ok` (same: bdiff <= tol; opposite: 180 - bdiff <= tol; brak kursu = przepuszcza); mediana signed xtrack; filtr `|xtrack - mediana| <= deviation` (usuwa skoki GPS, zachowuje staly odsuw sasiedniego pasa); link primary = min `|xtrack - mediana|` per stacja; sekcje z < 3 kandydatami pomijane. UWAGA: polozenie STACJI = GPS anteny (bez korekty plyty) i polozenie TSD = GPS (bez -4,8 m).
Wartosci uzyte w v4 (plik_wymiany_informacji.md): `--match-set stage1_capture --radius 30 --gather-xtrack 6 --deviation 5 --bearing-tolerance 30 --lane-filter same,adjacent` (24489 linkow, wszystkie `stage1_capture`). Czyli "luzny" match, NIE r = 8 m z Tab. 3.2.
Pulapki: kryterium parowania w tym skrypcie jest geometryczne (promien, xtrack, kierunek), ale wybor SEKCJI zalezy od przegladu recznego (status confirmed) i od `|Spearman| >= 0,8` (p. 2.5). `match_set` rozny od 'stage1_capture' nie istnieje w v4. Tekst `--max-days` filtruje po sekcji, nie po stacji.

### 2.4 rebuild_sections.py - przebudowa tsd_fwd_sections z progami

Plik: C:\projects\sql_tsd_fwd\bak\rebuild_sections.py. CLI: `--db --out --vacuum --log --dry-run --keep-ids-from REF_DB` + progi detect_sections.
Funkcje: `setup_logging`, `fmt_bytes`, `table_exists`, `count`, `report_state(conn, label)`, `keep_ids_from(conn, ref_db)` (numeracja sekcji jak w bazie ref: klucz (nazwa pliku TSD, sciezka wzgl. FWD, mdb_session_id)), `assert_imported_data`, `main()`.
Zapisuje: kasuje `tsd_fwd_links` poza match_set='legacy', wola `build_road_db.detect_sections(...)` (czysci `tsd_fwd_sections`, kaskadowo `tsd_fwd_section_review`), opcjonalnie VACUUM; wpis do `import_log`. Z `release_guard` (zapis do baz wydania zablokowany).
Progi "Etapu 1" = Tab. 3.2 (jak w import_v3.log; komenda w plik_wymiany_informacji.md l. 2008): `--section-radius 8 --section-min-coverage 30 --section-min-corr 0.8 --section-bearing-tol 30 --lane-same-max 0.75 --lane-adjacent-max 2.0 --max-days 400 --min-overlap-len-m 500 --min-matched-stations 5` (ten sam rok domyslnie; `--cross-year` wylacza). Wartosci DOMYSLNE skryptu to luzne (radius 100, coverage 30, corr 0,5, bearing 45, lane 1,5/6,0, max-days 400, overlap 0, min_stations 3) - nie Tab. 3.2.

### 2.5 build_road_db.detect_sections (logika Tab. 3.2; bak\build_road_db.py l. 2206-2500)

`detect_sections(conn, radius_m=100.0, min_coverage_pct=10.0, min_abs_corr=0.5, bearing_tol_deg=45.0, max_days=5000.0, lane_same_max_m=1.5, lane_adjacent_max_m=6.0, same_year_only=True, min_overlap_len_m=0.0, min_matched_stations=3)`.
Per para (sesja FWD, plik TSD) z nakladajacym sie bbox (margines `max(2*radius, 50)` m): filtr ROKU (same-year, brak daty = odrzut) i `max_days`; dla kazdej stacji FWD najblizszy punkt TSD w `radius_m` (plaskie przyblizenie), `xtrack` wzgledem kursu TSD, wymagane `station_m` i `chainage_m`; `coverage_pct = 100*matched/fwd_in_overlap` (mianownik = stacje FWD w bbox TSD z marginesem radius; `coverage_full_pct` = wzgledem calej sesji, informacyjnie); bramki: `matched >= min_matched_stations` (5), `coverage >= 30 %`, `max(chainage)-min(chainage) >= min_overlap_len_m` (500 m, "dlugosc nakladania po stronie TSD", z chainage dopasowanych punktow, nie z dlugosci pliku); `|Spearman(station_m, chainage_m)| >= min_abs_corr` (0,8). UWAGA: "rho >= 0,80" z Tab. 3.2 to monotonicznosc stacji FWD wzgledem pikietazu TSD (sanity check), NIE korelacja profili/ugiec. Kierunek z `mean_bearing_diff`: <= tol -> 'same', >= 180 - tol -> 'opposite', inaczej odrzut ("30/150 stopni"); `lane_class` z `|median_xtrack_m|`: <= `lane_same_max_m` (0,75) 'same', <= `lane_adjacent_max_m` (2,0) 'adjacent', inaczej 'far'. Zapis do `tsd_fwd_sections` (UNIQUE(session_pk, tsd_file_id)).
Stan v4: 445 sekcji (39 opposite/far, 80 same/adjacent, 239 same/far, 87 same/same), z czego `tsd_fwd_section_review` ma 167 wierszy, wszystkie `confirmed`, widok `v_stage2_sections` = 167 (== 87 same/same + 80 same/adjacent), wszystkie `stage2_eligible=1`.
Uwaga: geometria uzywa przyblizenia plaskiego 111320 m/st zamiast EPSG:2180; promien 8 m jest mierzony do najblizszego PUNKTU TSD w pliku (rozdzielczosc ~1 m), nie do osi.

### 2.6 section_manual_checks.py - reczne kontrole sekcji

Plik: C:\projects\sql_tsd_fwd\bak\section_manual_checks.py. CLI: `--db add|list`. Funkcje: `manual_checks_ddl()` (importuje `build_road_db.MANUAL_CHECKS_DDL`), `section_info(conn, section_id)`, `cmd_add(args)` (zapis; wymaga `--section-id --check-type --result {OK,NOK,NIEROZSTRZYGNIETY} --by --at [--comment --expect-tsd --expect-fwd]`; kontrola zgodnosci numeracji sekcji z nazwami plikow; guard wydania), `cmd_list(args)` (mode=ro), `main()`.
Tabela `section_manual_checks(check_id, section_id, check_type, result, checked_by, checked_at, comment)`; w v4 1 wiersz. Dla N4 tylko pojecie: "kontrola linia-do-linii / slad GPS w Excelu" jako wpis recznej weryfikacji; sluzy do statusu `stage2_note` w widoku. N4 nie powinien pisac do tej tabeli - wystarczy eksport raportu do weryfikacji.

### 2.7 e2b1_geometry.py - polozenie plyty FWD z anteny i dystansomierza (P043/P043b)

Plik: C:\projects\sql_tsd_fwd\bak\e2b1_geometry.py. Zasada nadrzedna: modul NIE czyta wartosci ugiec (test T7 sprawdza statycznie). Wejscie: `datasets.connect(datasets=(dataset,'mikroodcinki'))` (v4 + produkty, mode=ro), `p_*.ref_corridor_points`, `p_*.fwd_station_position`, `p_*.fwd_sref`, `baza_analizy_e2a.db` (`fwd_position_check.shift_m`, `fwd_station_point_mikro`, `mikro_points.s_point`). Zapis: `baza_analizy_e2b.db` (`fwd_plate_position_e2b` 47405 w DB, `fwd_session_runs`, `e2b1_params`, `e2b1_validation_mikro*`, `e2b1_hwd_diagnostic`) i CSV `tabele\e2b1_*.csv`.
Stale: `D_OLD_367 = 5,5`, `D_VARIANTS = (5,0; 5,5; 6,0)`, `CUTOFF_367 = '2025-10-09'`, `D_8082_119 = 1,0`, `D_8002_369 = 1,0`, `RUN_JUMP_FACTOR = 3`, `MIN_RUN_N = 5`, `GROSS_MIN_M = 5`, `GROSS_MAD_MULT = 4`, `STOP_NEW_P90_M = 1,5`, `STOP_OLD_MEDIAN_M = 1,5`, `EPS_MIN_LEN_M = 1000`, `EPS_MIN_N = 10`; `sigma_era` (new 0,380 / old 1,931 / hwd 0,195 / hwd_cautious 1,931 / unconfirmed 1,931 m; `e2b1_params.csv`).
Funkcje: `md5`, `md5_r2`, `write_csv`, `insert`, `safe_table_name`, `pctl`, `load_corridors(conn, pr_alias)` -> dict cid -> `e1_sref.Corridor`, `load_raw_stations(conn, dataset, since=None, until=None)`, `project_antenna_k1(corridors, rows)`, `direction_from_data(rows)`, `plate_offset(device, date, d_old_367=D_OLD_367)` -> (d, era, confirmed), `compute_k2(rows, d_old_367)`, `split_runs(sm, cid, direction)`, `fit_run_robust(sm, y, direction, factor, force_eps_zero=False)`, `compute_k3_k4(rows, sigma_era, eps_variant='full')`, `sigma_era_from_e2a(e2a_db_path, log_)`, `run_k5_validation(conn, sigma_era, log_, d_variant, eps_variant)`, `hwd_diagnostic`, `run_dataset`, `insert_dataset`, `archive_old_tables`, `ensure_tables`, `main()`.
Co liczy:
- K1: rzut ANTENY GPS (nie plyty) na korytarz (reguly pasa jak fwd_sref: 1,75 m / 5,0 m; kurs `heading_deg - convergence`), wynik `s_ant`, `lat_ant`, `lane_match`. Kierunek sesji (+1/-1) Z DANYCH: znak mediany ilorazu `ds_ant/d station_m` (`e2a1b_position.unit_factor`; factor 1000 gdy 300<|iloraz|<3000 = km, 1 gdy 0,3<|iloraz|<3 = m), NIE z `heading_deg` i NIE z `fwd_sessions.station_direction` (test T2).
- K2: `s_plate_gps = s_ant - kierunek * d(aparat, data, era)` - przesuniecie WYLACZNIE wzdluz korytarza; era: 8002-367 'old' (data < 2025-10-09, d = 5,5) / 'new' (d = 0); 8082-119 'hwd' d = 1,0; 8002-369 'unconfirmed' d = 1,0 (antenna_offset_confirmed = 0); inny aparat: d = 0, 'unknown'.
- K3: podzial sesji na ciagi (zmiana korytarza, brak/powtorzenie station_m, skok > 3x mediana kroku, zmiana znaku kroku vs kierunek); w ciagu >= 5 stacji odporna regresja `s_plate_gps = a + slope*station_m` (iteracyjne odrzucanie `|reszta| > 4*sigma_MAD`, `slope = kierunek*factor*(1+eps)`); w wariancie wybranym ('short_zero', `eps_variant_chosen = 1`) eps = 0 dla ciagow < 1000 m lub < 10 stacji (tylko wyraz wolny). Bledy grube GPS oznaczone (`|reszta| > max(5 m, 4*sigma_MAD)`), stacja zostaje.
- K4: `s_fwd` = `s_dmi` (ciag >= 5 stacji, fit poprawny; `pos_source='dmi'`) albo `s_plate_gps` (`'plate_gps'`); `sigma_long = sqrt(sigma_a^2 + sigma_era^2)`, `sigma_a = sigma_MAD/sqrt(n_used)`.
- K5: walidacja na mikroodcinkach vs `mikro_points.s_point` (P50/P90 |blad|; STOP gdy nowe noce P90 > 1,5 m albo wrzesniowe |mediana| > 1,5 m przy d=5,5). Kontrola Cowork: `sigma_era['old']` = 1,93 m, n = 24 (STOP gdy inaczej).
Pulapki:
- `direction` = znak `ds_ant/d station_m` (stacje posortowane po station_m), potem uzywany jako kierunek jazdy w `s_plate = s_ant - direction*d` i w `split_runs` (po czasie). Zalozenie: station_m rosnie w tym samym kierunku co czas pomiaru. Potwierdzic na danych N4 (docstring detect_sections: station_m bywa malejace wzdluz jazdy).
- Zmiana reguly miedzy skryptami (5,0 m / 2025-01-01 vs 5,5 m / 2025-10-09) - p. 2.1.
- Okresy sigma_era sa ZWIAZANE z baza e2a (`fwd_position_check`); w N4 to parametr uzytkownika.
- K2/K4 zalezy od `station_m` (DMI) FWD i jednostek (km vs m): zgadywanie `station_m <= 5 -> km`.
- Przy `device_trailer` w mikro: `se.device_trailer`; w odcinki `ff.trailer`.

### 2.8 e2b1_pairs.py - kandydaci par, warstwy A/B/C/X, pary zerowe, inwentarz (K6-K9)

Plik: C:\projects\sql_tsd_fwd\bak\e2b1_pairs.py. Zasada: zero kolumn ugiec (tylko s_ref, lateral_m, czas, GoF, v_med, atrybuty).
Wejscie: `fwd_plate_position_e2b` (z e2b1_geometry; stacje `lane_match IN ('same','adjacent') AND s_fwd NOT NULL`), `p_odc.tsd_passes` + `tsd_pass_calib` (calib_interval, calib_interval_uncertain, data_tier), `p_odc.tsd_sref` + `odc.tsd_measurements.goodness_of_fit` (`lane_fit='lane'`, `s_ref` i `pass_id` niepuste), `p_odc.tsd_position_offset.uncertainty_m` (1,5 m), `tsd_fwd_links.match_set='stage1_capture'` x `tsd_fwd_section_review.confirmed` (`in_stage1`). Wyjscie: `golden_pair_candidates` (65449 w DB; CSV odcinki 64111, same_year=1: 31348 par, 23705 stacji; warstwy same_year: A 8207, B 12211, C 10486, X 444), `e2b1_null_map`, `e2b1_inventory`, `e2b1_layer_sensitivity`.
Stale: `WINDOWS = win1 +-1 m, win2_5 +-2,5 m, win5 +-5 m`, `NEAREST_PREFILTER_M = 100`, `YEAR_DIFF_MAX = 1`, `NULL_SHIFT_M = 200`, `NULL_PERM_MIN_M = 300`, `NULL_SEED = 20261017`, `LAYER_A = (1,0; 1,0)` (|dlat| <= 1,0 m i sigma_long <= 1,0 m), `LAYER_B = (1,75; 2,5)`, `LAYER_C_SIGMA = 5,0`, `TSD_SIGMA_M_DEFAULT = 1,5`, `STAGE1_MATCH_SET = 'stage1_capture'`.
Funkcje: `load_candidate_stations(e2b_path, dataset, log_)`, `load_tsd_sigma`, `load_passes(conn, ds_alias, pr_alias)`, `load_pass_rows_for_corridor(conn, ds_alias, pr_alias, corridor_id)`, `load_in_stage1`, `window_stats(s_sorted, tsd_id, lat, gof, center, radius)` (n, tsd_id_min/max, udzial GoF >= 0,5, mediana lateral), `nearest_row(s_sorted, s0)`, `layer_of(dlat, sigma_long)`, `build_candidates(stations, passes_by_corr, pass_rows_loader, in_stage1, tsd_sigma_m, log_)`, `_dt_days(fwd_date, tsd_date)` (= TSD - FWD, w dniach, ZE ZNAKIEM), `build_null_pairs(candidates, pass_rows_cache, log_)`, `build_inventory(candidates, dataset, log_)`, `make_plots`, `archive_old_pairs_tables`, `main()`.
Co liczy:
- K6: para = stacja FWD (lane_match same/adjacent) x przejazd TSD NA TYM SAMYM korytarzu, rok FWD = rok TSD (`same_year=1`) albo +-1 rok (flaga); najblizszy wiersz TSD (`lane_fit='lane'`) do `s_fwd` (`ds = s_fwd - s_row`, odrzut `|ds| > 100`); okna +-1/+-2,5/+-5 m wg `s_ref`: liczba wierszy, zakres `tsd_id`, udzial GoF >= 0,5, mediana lateral. `dlat = lat_ant(FWD) - mediana lateral TSD(+-5 m)`. UWAGA: rzut FWD to ANTENA (`lat_ant`), polozenie wzdluz = plyta (`s_fwd`).
- K7: warstwa: A `|dlat| <= 1,0 & sigma_long <= 1,0`; B `|dlat| <= 1,75 & sigma_long <= 2,5`; C `sigma_long <= 5,0`; X reszta (NaN -> X). Wrazliwosc na d (5,0/5,5/6,0) przez przesuniecie okna +-5 m bez ponownego K1-K4 (tozsamosc regresji liniowej).
- K8 pary zerowe: (i) srodek okna przesuniety o +-200 m (`shift_minus200`/`shift_plus200`) wzdluz TEGO SAMEGO przejazdu; (ii) `permutation` = losowy srodek ze siatki co 50 m z `[min(s), max(s)]` przejazdu z `|s - s_fwd| >= 300 m` (seed 20261017, rng wspolny dla wszystkich par w kolejnosci `pair_id`; ZALEZNOSC OD KOLEJNOSCI wywolan); strona FWD zostaje ta sama, zmienia sie wylacznie wybor TSD (okno +-5 m, nie zalicza sie warunku >= 3 wiersze - to dopiero w e2b2_values). Zero wartosci ugiec w K8.
- K9 inwentarz: liczby par/stacji wg warstwy x rok x calib_interval x aparat x era x data_tier x same_year; kontrola Cowork (same_year=1: 31348 par, 23705 stacji, 9172 poza Etapem 1) jako OPIS (nie STOP).
Pulapki: (a) `dt_days = TSD - FWD` ze znakiem (ujemne = TSD przed FWD); (b) `in_stage1` laczy po (station_id, file_id) przez `match_set = 'stage1_capture'` (w prompcie P043 bylo 'strict'); (c) przejazdy tylko z korytarzem; para tylko gdy `|ds| <= 100` m; (d) `layer` zalezy od `sigma_long` z K4 (era), nie od zmierzonej jakosci; (e) jeden FWD paruje sie z KAZDYM przejazdem TSD w tym roku (wiele par na stacje - stad klaster = sesja FWD w bootstrapie).

### 2.9 e2b1_catalog.py - dopisanie tabel e2b do katalogu

Plik: C:\projects\sql_tsd_fwd\bak\e2b1_catalog.py. Brak logiki analitycznej: czyta `sqlite_master` bazy `baza_analizy_e2b.db` (mode=ro), generuje wiersze (`database, kind, object_type, name, n_rows, n_columns, primary_key, columns, description`) i przepisuje `tabele\katalog_tabel.csv` (idempotentnie: usuwa stare wiersze tej bazy). `DESC` = opisy tabel e2b1_*; `table_names(conn)`, `main()`. Pomijalny w N4 (sluzy dokumentacji tabel).

### 2.10 Pary zerowe (zamiast "e2b1_null_*")

Skrypt o takiej nazwie nie istnieje; pary zerowe sa rozproszone:
- Odwzorowanie: `e2b1_pairs.build_null_pairs` (p. 2.8) -> `e2b1_null_map` (pair_id, null_type, corridor_id, pass_id, center_s, win5_n, win5_tsd_id_min/max, win5_gof05_share, dataset); CSV `tabele\e2b1_null_map_odcinki.csv` 191612 wierszy (dla wszystkich 64111 par kandydatow x do 3 typow).
- Wartosci TSD: `e2b2_values.build_null_values` (mediana d0 B_1510off w oknie W5, >= 3 wiersze) -> `e2b2_null_values` (27558 wierszy dla par e2b2: pair_id, null_type, d0_w5, n_d0_w5, d0_valid_w5, ...).
- Test zerowy B4: `e2b2_agreement.build_null_test(D_null, D_true, lam_d0, n_boot, log_)` + `_diff_ci_from_rows` (CI roznicy z CI skladowych, UPROSZCZENIE: sqrt(h1^2+h2^2), bez kowariancji), regula C `build_rule_c(b1510_path, pairs_true, pairs_shift, log_)`; poprawny bootstrap sparowany po sesjach: `e2b2b_extra.paired_bootstrap_null(fwd, tsd_true, tsd_null, session_ids, n_boot, seed)` (tabela `e2b2b_null_test_paired`).
- Wersja "lustro": `e2bR9_lustro_warianty.py` krok 4 (pary zerowe dla wszystkich wariantow reprezentacji).

### 2.11 e2b2_agreement.py - miary zgodnosci, test zerowy (P047/P047b)

Plik: C:\projects\sql_tsd_fwd\bak\e2b2_agreement.py. Wejscie: `e2b2_pairs`, `e2b2_tsd_values`, `e2b2_fwd_values`, `e2b2_null_values`, `e2b2_lambda` (z `baza_analizy_e2b.db`), `baza_analizy_e2a.db.e2a3_final_k_profile` (k krzywizn), `baza_odcinki_b1510off_v2.db` (regula C), `e2b1_null_map`. Wyjscie: `e2b2_agreement` (77 wierszy), `e2b2_deming_lambda_sens`, `e2b2_null_test` (4), `e2b2_null_test_diff`, `e2b2_rule_c` + CSV w tabele\ + wykresy.
Funkcje (sygnatury) - rdzen N4:
- `ccc_from_logs(x, y)` - Lin 1989: `2*cov / (var_x + var_y + (mx-my)^2)` z `np.var` (ddof=0) i `cov = mean((x-mx)(y-my))` (ddof=0).
- `bland_altman_log(x_fwd_log, y_tsd_log)` -> (bias, bias-1,96 sd, bias+1,96 sd, sd), sd z ddof=1; wynik raportowany jako ILORAZ `exp(.)`.
- `deming(x, y, lam)` - klasyczny: `slope = ((syy - lam*sxx) + sqrt((syy - lam*sxx)^2 + 4*lam*sxy^2)) / (2*sxy)`, `intercept = my - slope*mx`; x = TSD (zmienna z bledem), y = FWD, `lam = Var(blad y)/Var(blad x) = sigma_FWD^2/sigma_TSD^2`; n < 3, lam <= 0 lub sxy = 0 -> NaN. Wariant liniowy: `lam_lin = lam_log * (med_FWD/med_TSD)^2` (przeliczenie wedlug medianej poziomu).
- `ols(x, y)`.
- `point_stats(fwd, tsd, lam_log)` -> dict: `n, median_ratio = exp(median(ln FWD - ln TSD))`, `sd_log_ratio` (ddof=1), `pearson_r` (na log), `spearman_rho` (na wartosciach; niezmiennicze wzgledem log), `ccc` (na log), `ba_bias_ratio, ba_loa_lo_ratio, ba_loa_hi_ratio`, `deming_loglog_slope/intercept` (na log, lam = lam_log), `deming_linear_a/b`, `ols_linear_a/b`; n < 3 -> NaN.
- `bootstrap_ci(fwd, tsd, session_ids, lam_log, n_boot, seed=BOOT_SEED=20261019)` - bootstrap blokowy po sesjach FWD (losowanie sesji ze zwracaniem w liczbie rownej liczbie unikalnych, wszystkie ich pary razem), CI percentylowy 2,5/97,5, wymaga >= 3 sesji i >= 10 skonczonych replik; wynik dla KAZDEGO klucza z `POINT_KEYS`.
- `agreement_row(fwd_raw, tsd_raw, session_ids, lam_log, n_boot, extra, log_, label)`: filtr `finite & > 0` obu stron; `n_pairs`, `n_sessions`.
- `masked_tsd_col(D, metric_key, repr_key)`: wartosc TSD z NaN tam, gdzie `*_valid_<repr> = 0` (okno W uznane gdy >= 3 wiersze niepuste, P gdy wiersz niepusty).
- `build_agreement_table(D, lam_by_metric, n_boot, log_)`: pary miar `METRIC_PAIRS = (d0/d0, sci300/a031, bdi/a0361, bci/a6191, d0_d600/a061, d0_d900/a091)`; warstwy A+B/A/B/C; reprezentacje `p, w1, w2_5, w5` (+ `w5_dn` falkowy); rozbicia (era, rok, calib_interval) tylko dla d0.
- `build_deming_lambda_sensitivity`, `build_temp_variants` (WYCOFANA: decyzja Jacka wpis 180 - nie wolac z main), `load_null_joined`, `load_true_w5_joined`, `build_null_test`, `_diff_ci_from_rows`, `build_rule_c`, `make_plots`, `update_catalog`, `main()`.
Stale: `N_BOOT_DEFAULT = 1000`, `BOOT_SEED = 20261019`, `LAYER_GROUPS`, `REPR_KEYS`, `DT_MAX_C_SUBSET = 5,0`; `K_D0 = 0,016` i `T_REF = 20` z e2b2_values.
Lambda: `e2b2_lambda.csv`: d0: sigma_tsd 0,296408 (log), sigma_fwd 0,101763, **lambda 0,11787** (= (0,101763/0,296408)^2), n_pairs_tsd 2015, n_fwd_pairs 128, scale_m 10. Powstaje w `e2b2_values.compute_lambda_d0_and_curv`: pary przejazdow TSD tego samego dnia (`e1_bin_pairs`: `dt_days <= 1`, `concrete = 0`, oba pliki B_1510off ok/bez align_fail), bin 10 m po `floor(s_ref/10)` KORYTARZA (poprawka P047b: bin po pikietazu pliku byl bledny), `sigma_TSD = 1,4826*MAD(ln d_i - ln d_j) / sqrt(2)`; `sigma_FWD` z `baza_produkty_v1.e12_lambda` (dataset odcinki, fwd_subset 'ge2024', scale_m 10, `sigma_fwd_within` = 0,10176, n_fwd_pairs 128 - bledy powtorzen FWD, a nie przejazdow).
Pulapki:
- `n_stations` w `agreement_row` liczone jako `len(set(zip(sess, tsd)))` (przyblizenie, nieuzywane w tabeli).
- CI roznic w `build_null_test` bez kowariancji (P047) - poprawna wersja w e2b2b_extra.
- Bootstrap percentylowy przy 36 klastrach (36 sesji FWD, 38 w A+B przed filtrem W5) - patrz p. 2.12.
- `pearson_r` w `point_stats` na log, `spearman_rho` rowny na log i surowych; "r w obrebie sesji" NIE jest w point_stats (jest w e2b2b_extra.within_session_r i e2bR9_lustro_warianty).
- Warianty temperatury (norm20C, dT<=5) wycofane z tabeli glownej; korekta do 20 C robiona w z15_temp_correction.

### 2.12 e2x_uncertainty_methods.py - bootstrap klastrowy dziki, CR2, klaster tygodniowy (P068, zalacznik D012)

Plik: C:\projects\sql_tsd_fwd\bak\e2x_uncertainty_methods.py. Implementacja wlasna (numpy/scipy), bez statsmodels.
Funkcje rdzenia (niezalezne od bazy):
- `WEBB_WEIGHTS = [-sqrt(1,5), -1, -sqrt(0,5), sqrt(0,5), 1, sqrt(1,5)]` (6 punktow).
- `_ols(X, y)` -> (beta, resid, (X'X)^-1); `_cluster_index(cluster_ids)`; `_build_fe_design(group_key, x_extra)` (dummy na grupe bez wyrazu wolnego + kolumna zmiennej; j = ostatnia).
- `cr1_se(X, resid, XtX_inv, cluster_rows, j)` - Liang-Zeger z `G/(G-1) * (n-1)/(n-p)`.
- `wild_cluster_bootstrap(X, y, cluster_ids, j, n_boot, seed, mode='WCU', ref_value=0.0)` - wagi Webba po klastrze (macierz G x B), `T* = (beta* - srodek)/se*` (CR1 w kazdej replice). `mode='WCU'` (reszty modelu NIEOGRANICZONEGO; zwraca `beta_hat`, `se_hat`, `T`), `mode='WCR'` (reszty z modelu z narzuconym H0 beta_j = ref_value; zwraca `T_obs`, `p_value = mean(|T*| >= |T_obs|)`).
- `wcu_bootstrap_t_ci(X, y, cluster_ids, j, n_boot, seed, alpha)`, `wcr_test(X, y, cluster_ids, j, n_boot, seed, ref_value)`, `wcu_dual_ci(X, y, cluster_ids, j, n_boot, seed)` -> (punkt, lo90, hi90, lo95, hi95) z JEDNEGO ciagu T* (percentile-t: `lo = beta - se*q_hi`, `hi = beta - se*q_lo`).
- `_sym_sqrt_pinv(A, tol)`, `cr2_interval(X, y, cluster_ids, j, alpha)` -> (beta, lo, hi, se, dof): Bell-McCaffrey CR2 + Satterthwaite (Imbens-Kolesar) `dof = (sum phi^2)^2 / sum(phi^4)`, przedzial t; `cr2_dual_ci(X, y, cluster_ids, j)` (CI90 i CI95).
- `cluster_bootstrap_pairs_mean(values, cluster_ids, n_boot, seed, alpha, log_transform=False)` - M0_lin: bootstrap klastrowy par, percentyl, srednia (log -> srednia geometryczna).
- `iso_week_of(date_str)` -> 'RRRR-Www' (klaster tygodniowy, jak P053).
- `write_csv_rows`, `read_csv_dicts`, `find_csv_row(path, **filters)`, `ctrl_stop(label, live, expected, tol, log_)` (STOP gdy |live-expected| > tol; `CTRL_TOL = 0,01`), `log`/`OUT['fh']` (globalny logger).
Czesci aplikacyjne: `run_w1` (beta D0/D300/SCI300, `EXPECTED_W1`), `run_w2` (bledy korekty 25-30 C, `EXPECTED_W2`, `REQ.verdict4`), `run_w3(args, seed_for, log_)` (mnoznik d0 TSD -> D0 FWD po korekcie; ZALEZY OD z15_temp_correction i e2aR2_rules.apply_rule; `EXPECTED_W3_MAIN = {median_ratio 1,61584, lo 1,5382, hi 1,68335, n_sessions 36}`, grupy `{hwd_2024: 4, hwd_2026: 5, old_2024: 9, old_2025: 15, unconfirmed_2026: 3}`), `run_w4` (Delta-beta mikroodcinki, `EXPECTED_W4`), `main()`.
Dla N4 relewantne: (a) W3 - model `X = jedynka` (srednia ln ilorazu) po klastrze `sesja_FWD`, tzn. wild bootstrap/CR2 dla sredniej log-ilorazu; wynik w `tabele\e2x_niepewnosc_metody.csv` dla "mnoznik_lacznie": M0_mediana 1,61584 [1,5382; 1,68335] (36 sesji), M0_lin 1,59782 [1,53804; 1,65362], M1_WCU 1,59782 [1,53793; 1,6602] (WCR p=0,9393 dla H0: 1,6), M2_CR2 1,59782 [1,53689; 1,66116] (dof = 20,5); (b) klaster tygodniowy ISO dla danych dziennych/nocnych (M3).
Pulapki: `seed_for(*parts) = 1000 + crc32('|'.join(parts)) % 80000` (z e2a3e_range.py - potrzebne do identycznego odtworzenia replik); WCU/WCR to statystyki LINIOWE (srednia log-ilorazu), mediana nie ma analogu; domyslnie `n_boot = 9999`; bootstrap `Y_boot` jako macierz n x B (pamiec: n=5511, B=9999 -> ok. 440 MB double); `run_w3` kontroluje `n_sessions == 36`; `EXPECTED_*` wpisane na sztywno.
Test: `bak\test_e2x_uncertainty.py` (symulacja pokrycia 95 % dla 5/15/35/73 klastrow, ICC, M0 pairs vs M1 vs M2, plik `tabele\kontrolne\e2x_synthetic_coverage.csv`).

### 2.13 e2x_tab62_male_klastry.py (P068b)

Plik: C:\projects\sql_tsd_fwd\bak\e2x_tab62_male_klastry.py. Importuje e2x_uncertainty_methods (M1/M2/M3) dla werdyktow rownowaznosci Tab. 6.2 (e30 %, e5 % dla d0, sci300, bdi, bci; klaster = noc / tydzien ISO). Funkcje: `e_of_dbeta_pct(dbeta_pct, T)` = `100*(exp(dbeta/100*(T-20)) - 1)` (T-20, NIE 20-T), `transform_ci`, `pair_arrays(rows_v, pair)` (OLS ln(TSD/FWD) ~ FE(punkt|urzadzenie) + (t10-20)), `werdykty_str`, `min_delta_equivalent`, `main()`. `DELTAS_EXT = [1,37; 2; 3; 5; 7; 10]`, `EXPECTED_DBETA_M0`, `EXPECTED_E_M0`. Dotyczy mikroodcinkow/temperatury (nie par sieciowych) - dla N4 tylko jako przyklad zastosowania metod malych klastrow; nie wchodzi w zakres 7.2.

### 2.14 e2bR9_lustro_* (P071, wpis 253) - warianty reprezentacji TSD, warunki, kalibracja poza proba

Wspolne zasady: zero zapisu do baz; MD5 R2 przed = po; zapis tylko CSV w tabele\ i logi\E2b; cache `logi\E2b\e2bR9_lustro_reps_cache.pkl` (pickle; `real_reps, null_reps, pairs, t12, meta, lam_log, lam_log_sci`) laczy warianty -> kalibracja/warunki (WYMAGANA KOLEJNOSC: warianty najpierw).

**e2bR9_lustro_data.py** (wspolny modul). Zrodla: `tabele\z15_pary_wejscia.csv` (5511 par: strona FWD D0...D1800 w um normalizowanym 50 kN, daty lokalne, `fwd_session_id`, `device_group`, `d0_tsd` = W5 maskowane); `C:\WORK\DOKTORAT\wymiana\wyniki\z15\Z15_temperatury_par.csv` (T12 obu stron, `fwd_t12_cal`, `tsd_t12_cal`, flagi kalibracji; pobierane z DOKTORAT TYLKO do odczytu); `baza_analizy_e2b.db` (`e2b2_pairs`, `e2b1_null_map`, `e2b2_tsd_values`, `e2b2_null_values`, `e2b2_lambda`); `baza_odcinki_v4` + produkty (`tsd_sref` geometria, `tsd_measurements` eksport NOMINALNY d0..d900, czujnik 1,51 m); `baza_odcinki_b1510off_v2.db` (`b1510off_measurements`: B_1510off po kalibracji zer, d_d0/d_d200/d_d300/d_d450/d_d600/d_d900, gof).
Stale: `HAMPEL_WIN_ROWS = 21`, `HAMPEL_K = 3*1,4826`, `NOMINAL_OFFSETS = (d0, d200, d300, d450, d600, d900)`, `COST_OFFSETS = (d0, d200, d300, d450)`, `BETA_D0_PCT = 1,60415`, `BETA_D300_PCT = 1,21602`, `LINEAR_K = 0,02`, `Z15_TEMP_CSV` (sciezka absolutna DOKTORAT).
Funkcje: `fnum(x, default=nan)`, `load_z15_pairs(log_)`, `load_t12(log_)`, `load_pairs_meta(conn_e2b, pair_ids, log_)`, `load_null_map`, `load_precomputed_tsd`, `load_precomputed_null`, `load_corridor_pass_series(conn_ds, conn_b1510, ds_alias, pr_alias, corridor_id)`, `_rolling_median_mad(x, win)` (pandas `rolling(center=True, min_periods=1)`), `_rolling_mean`, `hampel_univariate(vals, win, k)`, `hampel_basin_nominal(series, win, k)` ("pelna czasza" przed filtrem), `nearest_idx(s_sorted, s0)`, `window_idx(s_sorted, center, radius)` (zamkniete `[c-r, c+r]` po s_ref), `window_median(vals, idx, gof=None, min_gof=None)`, `cost_select(s_sorted, offset_arrays, idx, fwd_vals, shape_only=False)` (wybor wiersza o najmniejszej sumie kwadratow roznic do FWD na 0/200/300/450 mm; `shape_only` normalizuje przez wlasne d0 = wariant C'), `correct_pair(fwd_val, tsd_val, fwd_t12, tsd_t12, treatment, beta_pct=BETA_D0_PCT)` (`'none' | 'main_after' | 'k02'`; wola `e2aR2_rules.apply_rule`).
Korekta do 20 C: `apply_rule(y, T, form, param)`: `guideline`: `y*(1 + k*(20 - T))`; inaczej `y*exp(beta*(20 - T))` (beta jako ulamek, 1,60415 %/C -> 0,0160415); T = T12 (temperatura warstwy na 12 cm) KAZDEJ strony osobno; T12 modelowane w DOKTORAT (nie ma ich w repo SQL_TSD_FWD).

**e2bR9_lustro_warianty.py** (`--n-boot 2000`). Warianty reprezentacji TSD d0: `P` (najblizszy wiersz, B_1510off), `W5`/`W10` (mediana d_d0 w oknie +-5/+-10 m, >= `MIN_WINDOW_N = 3` wierszy niepustych), `X_b1510` (Hampel + srednia kroczaca na serii d_d0, potem najblizszy wiersz), `X_nom` (to samo na pelnej czaszy eksportu nominalnego), `C_raw` (wybor wiersza po wartosciach - NARUSZA zasade "parowanie wylacznie geometryczne"; to jest wariant diagnostyczny), `C_X`, `Cprime`. Korekty: `none`, `main_after`, `k02`. Miary: `AGR.point_stats` + `AGR.bootstrap_ci` (seed `EE.seed_for(f'e2bR9_{pairtype}_{variant}_{treatment}', 'boot')`) + `session_demeaned_corr(fwd, tsd, session_ids)` (r i rho W OBREBIE SESJI: log-wartosci minus srednia sesji FWD, potem Pearson/Spearman; sesje z < 2 punktami pozostaja niecentrowane). Pary zerowe: te same pair_id, trzy typy, ta sama wartosc FWD, korekta main_after. Kontrola STOP: W5 main_after median_ratio = 1,61584 +-0,02. SCI300: trzy warianty (e2b2 a031_w5, W5_nom, X_nom). Zapis `tabele\e2bR9_lustro_warianty.csv` (48 wierszy + naglowek).
Pulapki: `r_within_session` liczone BEZ korekty n_session (n_within = n); dla par zerowych `lam_log` bez znaczenia; pickle zawiera sciezki/dane nie nadajace sie do pakietu; wymaga `pandas`.

**e2bR9_lustro_warunki.py** (KROK 6). Cztery proste przekroje jednowymiarowe (NIE pelna tabela krzyzowa), r Pearsona (log) dla W5 i C_X po `main_after`, `r_of` wymaga n >= 10:
- odstep `dt_days` (z `meta`, = TSD - FWD ze znakiem): `0-1` (dt >= 0 i <= 1), `2-30`, `>30` - **pary z ujemnym dt (TSD przed FWD) i z dt = 1,x nie wchodza do zadnego przedzialu: suma n = 119+1873+3268 = 5260 z 5511 (251 par pominieto)**;
- udzial GoF >= 0,5 w oknie +-5 m (`win5_gof05_share` z e2b2_pairs): `>=0,8`, `0,5-0,8`, `<0,5`;
- zmiennosc D0 FWD na odcinku: `CV = std(fwd_d0, ddof=1)/mean` WEWNATRZ `corridor_id` (>= 3 wartosci; wartosci zdublowane przez wiele przejazdow tej samej stacji licza sie wielokrotnie), tercyle liczone na wektorze po PARACH (`np.percentile` na skonczonych `cv_vals`);
- jakosc polozenia FWD: HWD / `stary_przed_2025-10` / `stary_po_2025-10` (granica napisowa `fwd_date >= '2025-10-01'`, NIE 2025-10-09 z e2b1_geometry; kategoria "stary" obejmuje tez 8002-369/unconfirmed - n=370 = `8002-369|2026`);
- aparat x rok TSD (`device_x_tsdyear`; `n >= 10`) - **kolumna "okres kalibracji TSD" z zadania NIE jest tu uzyta (jest `calib_interval` w e2b2_pairs: K2024-03-01 8087 par, K2025-05-27 241, K2026-05-19 873 - do dodania w N4)**.
- przeciecie `dt 0-1 & gof >= 0,8 & CV w T3` jak tsd_2_xml (referencja r ~ 0,90, n = 379, 3 odcinki): W5 r=0,836820 (n=99), C_X r=0,881672.
Wyniki (tabele\e2bR9_lustro_warunki.csv): dt 0-1: W5 r 0,857 (n=119); 2-30: 0,322 (1873); >30: 0,367 (3268); GoF >= 0,8: 0,815 (1481); 0,5-0,8: 0,547; < 0,5: 0,380; CV T1/T2/T3: 0,486 / 0,559 / 0,817.

**e2bR9_lustro_kalibracja.py** (KROK 5). Kalibracja przelicznika FWD <- TSD po korekcie `k02` (liniowa k = 0,02): `fit_multiplier(tsd, fwd)` = `sum(fwd*tsd)/sum(tsd^2)` (bez wyrazu wolnego, skala SUROWA, nie log; wymaga >= 5 par), `fit_affine(tsd, fwd)` (`np.polyfit` stopnia 1, skala surowa), `errors(fwd_pred, fwd_true)` -> (MAE [um], mediana |ln(FWD/FWD_pred)|, n). Ocena poza proba = leave-one-session-out (36 sesji, dopasowanie na 35, prognoza na pominietej, reszty polaczone); warianty: W5 mnoznik D0; C_X afiniczna na 4 offsetach LACZNIE (n_obs 22044) i mnoznik D0. `tabele\e2bR9_lustro_kalibracja.csv`: W5 mnoznik a = 1,4222 (w probie MAE 27,6747 um, mediana |log| 0,227208; LOSO MAE 27,7366, 0,227888); C_X afiniczna a = 0,325056, b = 51,3776 (LOSO 23,7106 / 0,184993); C_X mnoznik D0 a = 0,60008 (LOSO 34,8098 / 0,249911). Pulapka: kalibracja po `k02` (liniowa), a NIE po `main_after` (wykladnicza, mnoznik 1,61584); roznica wspolczynnika (1,4222 vs 1,6158) wynika z OLS-bez-wyrazu-wolnego w skali surowej (waga duzych D0) vs mediana ilorazu.

**e2bR9_lustro_plot.py** - tylko rysunek z CSV (`plots\e2b\e2bR9_lustro.png`), pomijalny w N4 (matplotlib).

### 2.15 Skrypty pomocnicze istotne dla N4 (skrot)

- `paths.py`: `ROOT`, `DB_DIR`, `TABLES_DIR`, `DB_ODCINKI`, `DB_PRODUKTY`, `DB_ANALIZY_E2B`, `release_guard(db_path, allow=None)`; zdejmuje `--allow-release-write` z `sys.argv` przy imporcie.
- `datasets.connect(datasets=..., products=True)`: baza w pamieci + `ATTACH ... mode=ro` aliasy odc/km/mik/sta oraz p_odc/p_km/p_mik/p_sta, widoki TEMP `v_all_*`.
- `e0_fwd_temp.sqlite_uri(path, **params)`, `check_paths`, `file_stamp`, `log_run`, `open_out`.
- `e0b_t20_defl.py`: `heading_of(x, y, half=5)`, `angdiff(a, b)`, `corrected_xy(s, x, y, lag_m)`, `project(...)`, `running_median_nan(y, w=101)`, `resample(s_src, v_src, s_grid, max_gap=3)`, `block_curve`, `curve_peak`, `ols_cluster_terms`.
- `e2b2_values.py` (860 l.): `load_fwd_values` (FWD: srednia zrzutow NIEOSIADCZYCH `d_i * 50 / force_kn` w um dla czujnikow dobranych po offsecie `x1..x9` sesji z tolerancja 1 mm; `F <= 0` lub `d <= 0` pomijane; SCI300 = D0-D300, BDI = D300-D600, BCI = D600-D900; flaga `flag_geophone_layout` dla nietypowego rozstawu), `tsd_values_for_window`, `window_extract`, `compute_lambda_d0_and_curv`, `build_lambda_rows`. `FWD_STANDARD_LAYOUT = (0,200,300,450,600,900,1200,1500,1800)`.
- `z15_pairs_export.py`: zapis `tabele\z15_pary_wejscia.csv` (5511 par = warstwy A+B, W5, tsd_year 2024-2026, 36 sesji FWD, d0_tsd = `d0_w5` z maska `d0_valid_w5`; czasy lokalne `local_Europe_Warsaw_DST_no_shift` (FWD) i `local_export_IBDiM_unverified` (TSD)).
- `z15_temp_correction.py`: protokol korekty (wpis 240): `BETA_D0_PCT = 1,6041459432458258` (CI 1,5132 - 1,7267), `LAM_D0 = 0,11786960020790811`, `BOOT_SEED = 20261107`, `N_BOOT_DEFAULT = 1000`; warianty: main (T12_cal, exp), bells3, operator_fresh (n=33), linear k = 0,02, strict_calib (flagi ok/ok n=1733); mnoznik "proportional" `D0_20 = factor * d0_20` = 1,61584.
- `e2aR2_rules.apply_rule(y, T, form, param)`; `e2aR_equivalence.verdict4(ci90_lo, ci90_hi, ci95_lo, ci95_hi, delta)` (ROWNOWAZNE / ROWNOWAZNE_ROZNE_OD_0 / ROZNE / NIEROZSTRZYGNIETE; `DELTAS = [1,37; 2; 3; 5]`).
- `e2b2b_extra.py`: `paired_bootstrap_null`, `within_session_r(log_fwd, log_tsd, session_ids)`, `build_gof_variants`.

## 3. Weryfikacja liczb z tabele\ (cytaty wierszy)

Katalog `C:\projects\sql_tsd_fwd\tabele`: 268 plikow; poniższe CSV maja BOM UTF-8 (`utf-8-sig`).

### 3.1 z15_korekta_TSD_FWD_main.csv - POTWIERDZONE
Naglowek: `variant,note,n_pairs,n_sessions,median_ratio,sd_log_ratio,pearson_r,spearman_rho,ccc,ba_bias_ratio,...,median_ratio_lo,median_ratio_hi,...` (47 kolumn); 10 wierszy danych:
- `main_before,"T12_cal, exp, beta=1.60%/C",5511,36,1.40644,0.342756,0.611999,0.503964,0.424149,...,median_ratio_lo 1.31686, hi 1.48572`
- **`main_after,"T12_cal, exp, beta=1.60%/C",5511,36,1.61584,0.321151,0.659578,0.580602,0.346871,1.59782,...,median_ratio_lo 1.5382, hi 1.68335`** (Deming log-log nachylenie 0,958655 [0,902308; 1,05999], intercept 0,642298; deming_linear_a 1,41861, b 8,16356)
- `bells3_after ... 1.64221 [1.5792; 1.70646]`, `linear_after (k=0.02) ... 1.65214 [1.58726; 1.72058]`, `strict_calib_after ... 1733 par, 20 sesji, 1.55575 [1.4166; 1.72846]`, `operator_fresh_after ... 33 pary, 21 sesji, 1.64843 [1.21305; 2.07471]`.
Kontrola niezalezna (moj odczyt CSV: `z15_pary_wejscia.csv` + `Z15_temperatury_par.csv`, korekta `y*exp(beta*(20-T12))`, beta = 0,016041459): mediana ilorazu 1,615841, r (log) 0,659578 - zgodne z wierszem `main_after` (do 1e-6). 5511 par = 36 sesji (`fwd_session_id`); grupy: old_2025 1805, hwd_2024 1546, old_2024 1087, hwd_2026 703, unconfirmed_2026 370. `z15_korekta_TSD_FWD_conversion.csv`: `proportional,D0_20 = factor * d0_20,1.61584,1.5382,1.68335,...,5511`.

### 3.2 e2bR9_lustro_warianty.csv - POTWIERDZONE z uwaga
Naglowek: `pairtype,variant,treatment,n,median_ratio,sd_log_ratio,pearson_r,spearman_rho,ccc,deming_loglog_slope,median_ratio_lo,median_ratio_hi,pearson_r_lo,pearson_r_hi,r_within_session,rho_within_session,n_within_session`; 48 wierszy.
- `real,W5,main_after,5511,1.61583,0.321106,0.659716,0.580947,0.346872,0.958455,1.5369,1.68134,0.514602,0.773244,0.403905,0.338739,5511` -> **r w obrebie sesji W5 = 0,403905 (0,403)**; mediana ilorazu 1,61583 (przeliczone od nowa z surowych okien; CSV z15 daje 1,61584; kontrola STOP tolerancja 0,02).
- `real,W5,none,5511,1.40644,...,r_within_session 0.407298`; `real,W10,main_after,...,0.511701`; `real,C_raw,main_after,...,0.615048`.
- Pary zerowe W5 main_after: `null_shift_minus200,W5,main_after,5122,1.59507,0.516812,0.155242,0.117048,5122` -> **r w obrebie sesji 0,155242**; `null_shift_plus200,W5,main_after,5127,1.61026,0.524545,0.13524,0.134948,5127` -> **0,13524**; `null_permutation,W5,main_after,4962,1.59451,0.407856,0.0962062,0.0164007,4962` -> **0,0962062**. (Potwierdza 0,155 / 0,135 / 0,096.) Uwaga: kolumna `pearson_r` (globalna) w tych wierszach to 0,517/0,525/0,408 (nie "w obrebie sesji").
- UWAGA ROZBIEZNOSC: niezalezne przeliczenie z `e2b2_null_values.csv` (d0_w5, n = 5122/5127/4962, zgodne z lustro) + `z15_pary_wejscia.csv` + T12 + `exp(beta(20-T))` daje r globalne 0,5169 / 0,5242 / 0,4076 (zgodne z lustro) ALE r w obrebie sesji 0,1136 / 0,1345 / 0,0266 (kolejno minus/plus/permutation) zamiast 0,155 / 0,135 / 0,096. Pokrywa sie to z `e2b2b_null_test_paired.csv` (`within_session_r_null`: shift_plus200 0,141119, shift_minus200 0,118223, permutation 0,0233381, bez korekty). Wniosek: wartosci `lustro` dla par zerowych shift_minus/permutation NIE odtwarzaja sie z e2b2_null_values; roznia sie srednimi/oknami liczonymi od nowa z B_1510off (okno po `s_ref` w lustro vs zakres `tsd_id` w e2b2_values). Do rozstrzygniecia z Jackiem, ktory zestaw jest kanoniczny; w testach regresji ustawic tolerancje i oznaczyc zrodlo.
- Dodatkowo: lustro `calibration`/`warunki` patrz p. 2.14.

### 3.3 Inne potwierdzone
- `e2b1_params.csv`: `sigma_era_new 0.379914 (n 96)`, `sigma_era_old 1.93146 (n 24)`, `sigma_era_hwd 0.195144 (n 8)`, `D_OLD_367 5.5`, `CUTOFF_367 = 2025-10-09`, `eps_variant_chosen 1`.
- `e2b2_lambda.csv`: `d0,0.296408,-0.0755076,0.101763,0.11787,2015,128,10,` oraz a031 0,0294772, a0361 0,0346035, a6191 0,0270222, a061 0,0354317, a091 0,0377235.
- `e2b2b_null_test_paired.csv`: shift_plus200 `r_true 0.618459, r_null 0.482559, delta_r 0.1359 [0.107799; 0.16538]`; permutation `delta_r 0.255605 [0.218052; 0.299466]`.
- `e2x_niepewnosc_metody.csv`: W3 mnoznik_lacznie (p. 2.12).
- `e2b2_pairs.csv` 9201 par (A 1638, B 4449, C 3045, X 69; rok TSD 2024: 3963, 2025: 4124, 2026: 1114); `e2b1_golden_pair_candidates_odcinki.csv` 64111 (same_year=1: 31348; stacji 23705) - zgodne z kontrola Cowork P043.

## 4. Bazy i tabela decyzji przegladu

- `C:\projects\sql_tsd_fwd\bazy\baza_odcinki_v4.db` (13,65 GB, atrybut tylko do odczytu; R1/R2 `data_release`): "baza_odcinki_v4" to zbior `odcinki` (alias `odc`). Tabele (sqlite_master, mode=ro): fwd_drops, fwd_files (126), fwd_histories, fwd_sessions (253), fwd_stations (46826), import_log, pavement_zones, section_manual_checks (1), sqlite_sequence, tsd_column_map, tsd_file_columns, tsd_files (241), tsd_fwd_links (24489, wszystkie `match_set='stage1_capture'`), **tsd_fwd_section_review (167 wierszy, wszystkie `status='confirmed'`)**, tsd_fwd_sections (445), tsd_gps_data_qc (479), tsd_measurements, tsd_supplement_log, widok `v_stage2_sections` (167).
- **Tabela decyzji przegladu 167 zatwierdzonych odcinkow** = `tsd_fwd_section_review(section_id PK -> tsd_fwd_sections, status, decided_at, decided_by, comment)`; wiersz probka: `(7, 'confirmed', '2026-09-23T18:40:16', 'jacek', 'auto: pojedyncze sparowanie dla tego TSD; przeniesione z v2_clean ... z v3 ...')`. Widok `v_stage2_sections` laczy ja z `tsd_fwd_sections` (direction='same', lane_class IN ('same','adjacent')), `tsd_gps_data_qc` (verdict_pair) i ostatnia `section_manual_checks`.
- Aparaty FWD (fwd_files.trailer): 8002-367: 93 pliki, 8082-119: 30, 8002-369: 3.
- Pozostale pliki w `bazy\`: baza_produkty_v1.db (1,2 GB: `tsd_passes` 901 wierszy, `tsd_pass_calib` 901, `tsd_sref` 7 006 756, `fwd_sref` 46826, `ref_corridor_points` 2 454 803, `e12_lambda` 8, `tsd_position_offset` 1 (-4,8 m, 1,5 m), `fwd_station_temp` 46826), baza_analizy_e2b.db (240 MB; e2b1_*, e2b2_*, e2b3_*, fwd_plate_position_e2b 47405, golden_pair_candidates 65449), baza_odcinki_b1510off_v2.db (B_1510off), baza_analizy_e2a.db, baza_analizy_w2.db, baza_produkty_{mikroodcinki,odcinki_1km,stacje}_v1.db, baza_{stacje,mikroodcinki,odcinki_1km}_v1.db, RELEASE_R1/R2.md.
- `C:\projects\sql_tsd_fwd\baza_TSD_FWD_odcinki` zawiera tylko katalogi zrodlowe `FWD\` (2020-Pomiary, 2021-Pomiary, 2022-Pomiary, A1_Intertol_FWD_2026, BELLS_FWD_HWD, ...) i `TSD\` (pliki `T*.pgc.ibdim.xls`, `*.raw.sup.xls`, B_1510off); to dane wejsciowe importu, nie baza SQLite.
- Kalibracje TSD: `tabele\kontrolne\tsd_kalibracje.csv` (event_id 1-10, np. 2024-03-01 serwis+kalibracja, 2024-05-25 `calibration_not_applied`, 2025-05-27, 2026-05-19); przypisanie przejazdu -> `tsd_pass_calib.calib_interval` ('K2024-03-01', 'K2025-05-27', 'K2026-05-19').

## 5. Dane wejsciowe dla N4 poza baza - minimalny schemat

N4 liczy na parach i sesjach, wiec uzytkownik musi dostarczyc (w CSV/Parquet) cztery obiekty plus parametry. Kolumny w nawiasach = nazwy z projektu.

A. Tryb "pary gotowe" (wystarcza do p. 7.2: miary, bootstrap, warunki, kalibracja; odpowiada `z15_pary_wejscia.csv` + T12):
1. `pairs`: `pair_id`; `session_id` (klaster = sesja/dzien/noc FWD; `fwd_session_id`); `station_id`; `pass_id`/`file_id`; `fwd_d0` [um, znormalizowane do 50 kN, srednia zrzutow nieosiadczych]; `tsd_d0` [um, mediana z okna +-5 m wg s_ref, >= 3 wiersze; znak dodatni, po kalibracji zer]; opcjonalnie `fwd_d200..d900` i `tsd_*` (krzywizny); `fwd_date`/`fwd_time`, `tsd_date`/`tsd_time` (lokalny czas, podac strefe!); `fwd_t12`, `tsd_t12` [C] albo (`t_layer`, `t_road`, T powietrza) + model; `device` (trailer), `era`, `tsd_year`, `calib_interval`, `data_tier`/`recorder_group`; `win5_gof05_share`, `win5_n`; `dlat`, `sigma_long_fwd`, `layer` (A/B/C/X) albo kolumny do jej wyliczenia; `dt_days` (ze znakiem lub |dt|).
2. Parametry: `lambda_log = sigma_FWD^2 / sigma_TSD^2` (albo oba sigma i metoda), `beta_D0` (%/C) lub k liniowe, `T_ref = 20`.
B. Tryb "z geometrii" (pelna procedura od wspolnych odcinkow do par):
1. TSD wiersze: `file_id`, `chainage_m` (rosnacy z jazda), `latitude`, `longitude` [stopnie, WGS84/GRS80], `datetime`, `heading_deg` (opcj.), `d0` (lub `d_d0`), `goodness_of_fit`, `temp_road`, `speed_ms`; plik: `file_date`, rejestrator (`ProfileRecorderVer`), `pavement_class`.
2. FWD stacje: `station_id`, `session_id`, `station_m` (z jednostka: km/m), `latitude`, `longitude`, `time`, `heading_deg`/kolejnosc, `device` (trailer), `gps_source`; zrzuty: `force_kn`, `d1..d9` (mm?/um - sprawdzic jednostke: w v4 `d*50/F` daje um), `is_seating`; rozstaw czujnikow `x1..x9` [mm]; temperatura (`asphalt_temp`, `surface_temp`, `air_temp`, `t_layer`).
3. Progi (domyslne = Tab. 3.2): `radius_m = 8`, `min_coverage_pct = 30`, `min_matched = 5`, `min_overlap_len_m = 500`, `min_abs_spearman = 0,80`, `bearing_tol = 30 deg` (kierunek same >=150 = opposite), `lane_same_max = 0,75`, `lane_adjacent_max = 2,0`, `same_year = True`.
4. Antena FWD (parametry): tabela `device -> [(data_od, d_m)]` (domyslne: 8002-367 5,0/5,5 m do 2025-01-01 / 2025-10-09, potem 0; 8082-119 1,0; 8002-369 1,0), `tsd_gps_lag_m = -4,8` (+-1,5).
5. Lista decyzji recznej weryfikacji (`section_id`, `status`) - odpowiednik `tsd_fwd_section_review` (167 'confirmed').
6. Do lambdy: pary przejazdow TSD tego samego dnia w tym samym binie 10 m (`s_ref`) i powtorzenia FWD (`sigma_fwd_within`, n=128).
7. Zewnetrzny model temperatury warstwy T12 (DOKTORAT) jako funkcja/kolumna - repo SQL_TSD_FWD go NIE zawiera.

Uwagi: "pikietaz" TSD to `chainage_m` pliku; wspolna os `s_ref` wymaga korytarzy (e1_sref) - bez nich uzytkownik musi dac `s_ref`/`s_fwd` wzdluz wspolnej osi (EPSG:2180, m) albo N4 musi miec uproszczony budowniczy osi (p. 7). Tryb A jest realny do wdrozenia od razu; tryb B wymaga przeniesienia ok. 3500 linii (e1_sref, e2b1_geometry, e2b1_pairs, detect_sections).

## 6. Mapowanie kryteriow Tab. 3.2 na kod

| Kryterium | Gdzie w kodzie | Wartosc | Uwagi |
|---|---|---|---|
| r (promien) 8 m | `detect_sections(radius_m)` przez `rebuild_sections --section-radius 8` | 8 m do najblizszego PUNKTU TSD | `match_sections` (stage1_capture) uzywa 30 m (luzny match) - roznica |
| pokrycie 30 % | `min_coverage_pct` | `matched / fwd_in_overlap` (stacje FWD w bbox TSD) | `coverage_full_pct` informacyjnie |
| >= 5 stacji | `min_matched_stations` | 5 | domyslne w skrypcie 3 |
| >= 500 m | `min_overlap_len_m` | `max - min` chainage dopasowanych punktow | nie dlugosc pliku |
| rho >= 0,80 | `min_abs_corr` | `|Spearman(station_m, chainage_m)|` (monotonicznosc), NIE korelacja ugiec | znak bez znaczenia |
| kierunek 30/150 | `bearing_tol_deg` | `mean_bearing_diff <= 30` -> same, `>= 150` -> opposite, reszta odrzut | w korytarzach `HEAD_TOL_DEG = 30` na kursie siatki 2180 |
| klasy pasa 0,75/2,0 m | `lane_same_max_m`, `lane_adjacent_max_m` | `|median_xtrack_m|` | korytarze: 1,75/5,0; warstwy A/B: 1,0/1,75 |
| ten sam rok | `same_year_only=True` (+ `max_days = 400`) | rok kalendarzowy daty TSD i FWD | e2b1: `YEAR_DIFF_MAX = 1` flagowane, glowny zbior same_year = 1 |
| przeglad linia-do-linii | `tsd_fwd_section_review`, `section_manual_checks`, `verify_sections.py`, `plot_tsd_fwd_sections.py` | 167 confirmed | reczny; N4 ma to zastapic raportem |
| pary geometryczne W5 / W10 | `e2b1_pairs.window_stats`, `e2b2_values.tsd_values_for_window`, `lustro_warianty.build_b1510_reps` | +-5 / +-10 m po s_ref, >= 3 wiersze | wybor po wartosciach (C) tylko diagnostycznie |
| korekta do 20 C obu stron | `z15_temp_correction`, `e2aR2_rules.apply_rule`, `lustro_data.correct_pair` | `y*exp(beta*(20 - T12))`, beta 1,6041 %/C (exp.) / `y*(1 + 0,02*(20 - T))` (linear) | T12 z DOKTORAT |
| lambda z powtorzen przejazdow | `e2b2_values.compute_lambda_d0_and_curv` | 0,11787 | sigma_FWD z e12_lambda |
| bootstrap po sesjach | `e2b2_agreement.bootstrap_ci` | 1000/2000 replik | percentylowy |
| male klastry | `e2x_uncertainty_methods` | WCU/WCR Webb 9999, CR2 + Satterthwaite, klaster tydzien ISO | |
| pary zerowe +-200 m / permutacja >= 300 m | `e2b1_pairs.build_null_pairs` | seed 20261017 | |
| tabela warunkow | `e2bR9_lustro_warunki.py` | dt, GoF, CV D0, aparat x rok (nie x kalibracja) | do uzupelnienia o calib_interval |
| kalibracja poza proba | `e2bR9_lustro_kalibracja.py` | LOSO po sesji | k02, skala surowa |

## 7. Wnioski dla projektu

### 7.1 Proponowany podzial na moduly pakietu `tsdfwd_tools` (wspolne czesci: `core/`, N4 w `tsd_fwd_compare/`)

```
tsdfwd_tools/
  core/
    geo.py            to_2180, convergence_deg, shift_along, heading_of, angdiff, corrected_xy, project_on, Corridor, best_projection  (z e1_sref + e0b)
    config.py         dataclasses z progami Tab. 3.2, reguly anteny, lag TSD, T_ref, beta, wlaczone seedy (zamiast stalych modulowych)
    stats_basic.py    group_median, robust_sd (1,4826 MAD), pctl, window median z min_n
    io_schema.py      walidatory schematow pairs/tsd_rows/fwd_stations/sections/sessions (p. 5), czytniki CSV/Parquet, SQLite mode=ro (opcjonalnie)
  tsd_fwd_compare/
    sections.py       detect_sections (Tab. 3.2) na DataFrame, `|Spearman|`, kierunek, klasa pasa, raport "linia do linii"
    fwd_position.py   regula anteny (parametryzowana tabela), direction_from_data, split_runs, fit_run_robust, sigma_long (z e2b1_geometry)
    pairing.py        build_candidates (okna W5/W10/+-1/+-2,5, nearest, layer_of), build_null_pairs (+-200 m, permutacja), tylko geometria
    corrections.py    apply_rule (exp/guideline), correct_pair, T12 provider (interfejs; model DOKTORAT poza pakietem)
    agreement.py      ccc, bland_altman_log, deming, ols, point_stats, within_session_corr, median ratio/SD log (z e2b2_agreement + lustro)
    uncertainty.py    bootstrap_ci po sesjach (+ sparowany dla par zerowych), wild_cluster_bootstrap (WCU/WCR), cr2_interval, iso_week_of, cluster_bootstrap_pairs_mean
    lambda_est.py     sigma_TSD z par przejazdow (MAD/sqrt2), sigma_FWD z powtorzen, lambda
    conditions.py     tabela warunkow (dt, GoF, CV D0 odcinka, aparat x okres kalibracji) - przeniesienie z lustro_warunki + poprawka p. 7.2
    calibration.py    fit_multiplier, fit_affine, leave_one_group_out (z lustro_kalibracja)
    report.py         tabele CSV/HTML, kontrola "linia do linii" (wykresy opcjonalnie)
  cli/  tsd_fwd_compare.py (subpolecenia: sections, pairs, agree, uncertainty, conditions, calibrate)
```
Moduly E1 (budowa korytarzy i s_ref, wyrownanie profilem, 2200 l.) wydzielic jako `tsd_fwd_compare/axis_ref.py` (opcjonalny, tryb B); w trybie A (os wspolna dostarczona) niepotrzebny.

### 7.2 Co wymaga przeredagowania (nie przenosic 1:1)
1. Globalny logger `UM.OUT['fh']` / `log()` w e2x*, e2b2_agreement, lustro - zamienic na `logging` i parametr; usunac `sys.path.insert`, `import paths`, `release_guard`, MD5 baz R2.
2. Stale na sztywno i kontrolne `EXPECTED_*`/`ctrl_stop`/`sys.exit` w srodku obliczen (e2x, lustro, e2b1_pairs `kontrola`, e2b1_geometry `sig_old_expected`) -> przeniesc do testow regresji; w bibliotece zwracac wyniki, nie przerywac procesu.
3. Pary/okna oparte o `tsd_id` zamiast odleglosci (e2b2_values uzywa zakresu `tsd_id_min..max`; lustro uzywa okna po `s_ref`) - w N4 jedna definicja: okno po `s_ref` (`searchsorted`, przedzial domkniety), >= 3 wiersze niepuste. To MOZE tlumaczyc rozbieznosc w parach zerowych (p. 3.2) - hipoteza, nie sprawdzona (brak dostepu do wierszy B_1510off w tym przebiegu).
4. Dwie reguly anteny (5,0 m/2025-01-01 vs 5,5 m/2025-10-09) i dwa progi "stary po 2025-10" (01 vs 09 pazdziernika): jedna tabela parametrow z data i zrodlem, ustawiona jawnie przez uzytkownika; domyslnie wartosc z P043b (5,5 m, 2025-10-09, era new/old).
5. `direction` FWD z `ds/dstation_m` + zalozenie jazdy zgodnej ze wzrostem `station_m` - udokumentowac i dodac test odwroconej sesji (jak `test_e2b1.py` T2); alternatywa: kierunek z czasu.
6. `dt_days` ze znakiem i przedzialy bez ujemnych (251 par pominietych w `warunki`): w N4 uzyc `|dt|` albo jawnie raportowac ujemne; dodac przedzial `<0`.
7. Warunek "aparat x okres kalibracji TSD" - dodac `calib_interval` (K2024-03-01, K2025-05-27, K2026-05-19) i `device`; usunac podmiane przez `tsd_year`.
8. CV(D0) odcinka: uzywa wartosci powtarzanych przy wielokrotnych parowaniach tej samej stacji; w N4 liczyc na unikalnych stacjach (lub jawnie wazyc); tercyle po stacjach, nie parach.
9. Bootstrap: `percentile` przy 36 klastrach niedoszacowuje; dla N4 domyslnie raportowac obok: sparowany bootstrap sesji (p. 2.10), WCU/WCR (Webb) i CR2 z dof; `seed_for` zachowac (crc32), by powtarzalnosc zgadzala sie z raportem.
10. `e2b2_agreement.deming` - jawna konwencja: x = TSD, y = FWD, lambda = Var(err_FWD)/Var(err_TSD) (ta sama w testach T1); wariant liniowy z `lam_lin` skalowanym mediana poziomow - zachowac; dodac walidacje wejsc (n >= 3, lambda > 0).
11. `build_temp_variants` wycofane (decyzja wpis 180) - nie przenosic; korekta do 20 C tylko jako osobny, jawny krok z `treatment in {none, main_after (exp), k02 (linear)}`; T12 jako wejscie.
12. Wariant C/C'/X w lustro (wybor po wartosciach, Hampel + srednia) - tylko jako tryb diagnostyczny "lustro", poza domyslnym potokiem (zasada: parowanie wylacznie geometryczne).
13. pickle cache -> Parquet/CSV; pandas tylko do `rolling` (mozna numpy).
14. Konwencje znaku i ukladow: wszystkie polozenia w EPSG:2180 (x = E, y = N), `lateral_m` + = lewo (e1_sref) vs `cross_track_signed_m` + = prawo (match_sections) - ujednolicic; Spearman bez znaku; kierunek 30/150.
15. Detect_sections uzywa plaskiego przyblizenia 111320 m/st; przy N4 uzyc `to_2180` (e1_sref) lub haversine - wynik w progu 8 m moze sie nieznacznie zmienic (do testu na 167 sekcjach).

### 7.3 Testy regresji z wartosciami referencyjnymi - wykonalne
Poziom 1 - bez baz (tylko CSV w repo + Z15 DOKTORAT do odczytu):
1. `tabele\z15_pary_wejscia.csv` + `C:\WORK\DOKTORAT\wymiana\wyniki\z15\Z15_temperatury_par.csv` -> `z15_korekta_TSD_FWD_main.csv`: `main_before` mediana 1,40644 [1,31686; 1,48572], SD log 0,342756, r 0,611999, rho 0,503964, CCC 0,424149, BA bias 1,38622, Deming log-log 1,05235 / 0,106303 (lambda 0,11786960020790811); `main_after` mediana 1,61584 [1,5382; 1,68335], SD log 0,321151, r 0,659578, rho 0,580602, CCC 0,346871, Deming log-log 0,958655 / 0,642298, Deming liniowy 1,41861 / 8,16356, 5511 par, 36 sesji. Tolerancja 1e-5 dla punktow (sprawdzone: mediana i r odtwarzaja sie do 1e-6), CI bootstrap statystycznie (seed 20261107, 1000 replik; ew. 1e-2 jesli RNG inny).
2. W3 niepewnosc: `e2x_niepewnosc_metody.csv` (M0_lin 1,59782 [1,53804; 1,65362]; M1_WCU [1,53793; 1,6602], WCR p = 0,9393; M2_CR2 [1,53689; 1,66116], dof 20,5) - wejscie: `log(fwd_after/tsd_after)` + `fwd_session_id` (z p. 1); seed `seed_for('e2x_w3_lacznie','wcu')`/`'wcr'`; tolerancja CTRL 0,01.
3. Kalibracja: `e2bR9_lustro_kalibracja.csv` wiersze W5 (mnoznik w probie a = 1,4222, MAE 27,6747, mediana |log| 0,227208; LOSO MAE 27,7366, 0,227888) - wejscie: z15 pary + T12 + korekta `k02` (`y*(1 + 0,02*(20 - T12))`) i `fit_multiplier`.
4. Warunki: `e2bR9_lustro_warunki.csv` (dt 0-1: W5 r = 0,857391, n = 119; 2-30: 0,322221 / 1873; >30: 0,366773 / 3268; GoF >= 0,8: 0,814548 / 1481; przeciecie 0,83682 / 99) - wejscie: z15 pary + T12 + `e2b2_pairs.csv` (join po `pair_id`: `dt_days`, `win5_gof05_share`, `corridor_id`, `device`, `era`, `sigma_long_fwd`).
5. Miary zgodnosci i r w obrebie sesji: `e2bR9_lustro_warianty.csv` wiersze `real,W5,none|main_after|k02` (r w obrebie sesji 0,407298 / 0,403905 / 0,402391; z CSV z15 odtworzone 0,40362 dla main_after - tolerancja 5e-4) i `e2b2_agreement.csv` (main, AB, w5, d0_vs_d0, none: mediana 1,40644, r 0,611999, deming_linear_a 1,41031 / b -5,71915). Dla par zerowych: `e2b2_null_values.csv` + z15 -> r globalne 0,5169 / 0,5242 / 0,4076 i mediana ilorazu 1,5952 / 1,6098 / 1,5932 (zgodne z lustro: 1,59507 / 1,61026 / 1,59451, tolerancja 2e-3); r w obrebie sesji dla par zerowych odtwarza sie tylko do e2b2b (0,118 / 0,141 / 0,023 bez korekty), NIE do lustro (0,155 / 0,135 / 0,096) - oznaczyc jako test "znana rozbieznosc".
6. Synteza: `test_e2b2.py` T1/T2 (Deming: prawda a = 1,3, b = -0,15, sigma_x 0,10, sigma_y 0,18, tolerancje 0,05/0,08; CCC = 2 sx^2/(2 sx^2 + 4) dla bias 2; BA bias 2, SD 0), `test_e2x_uncertainty.py` (pokrycie 95 % dla 5/15/35/73 klastrow), `test_e1.py` T1 (to_2180: poludnik srodkowy, symetria 19 E, skala 2. rzedu, zbieznosc), `test_e2b1.py` T1-T5, T11 (regresja dystansomierza, kierunek odwrocony, podzial ciagow, warstwy/okna, pary zerowe) - przeniesc prawie 1:1 (wymagaja tylko importow).
Poziom 2 - z bazami `mode=ro` (opcjonalne, "ciezkie"):
7. `baza_odcinki_v4.db`: `detect_sections` z progami Tab. 3.2 -> oczekiwane 445 sekcji (v4 po `rebuild_sections`), 167 `confirmed` w `tsd_fwd_section_review` (87 same/same + 80 same/adjacent w `v_stage2_sections`) i `tsd_fwd_links` 24489 (`stage1_capture`, radius 30). Test odtworzenia sekcji N4 = zbior 167 (kontrola recall/precision), uwaga na decyzje reczne.
8. `baza_produkty_v1.db` (`ref_corridor_points`, `tsd_sref`, `fwd_sref`) + `baza_analizy_e2b.db` (`fwd_plate_position_e2b`, `golden_pair_candidates`, `e2b1_null_map`): `build_candidates` -> `golden_pair_candidates` odcinki (64111 par w CSV; same_year = 1: 31348 par, 23705 stacji, warstwy A 8207, B 12211, C 10486, X 444); `build_null_pairs` seed 20261017 -> `e2b1_null_map_odcinki.csv` 191612; `compute_k3_k4` -> `fwd_session_runs`, `sigma_era` (new 0,379914, old 1,93146, hwd 0,195144).
9. `e2b2_lambda.csv`: lambda d0 = 0,11787 (sigma_tsd 0,296408, sigma_fwd 0,101763, n_pairs 2015) - z `e1_bin_pairs` + `b1510off_measurements`.
Do ustalenia z Jackiem: kanoniczne zrodlo wartosci "par zerowych w obrebie sesji" (p. 3.2).
