# E0-B: przeglad skryptow C:\projects\sql_tsd_fwd\bak pod narzedzia N1 (fwd_tempcorr) i N3 (tsd_network)

Tryb: wylacznie odczyt. Bazy SQLite otwierane tylko jako `file:...?mode=ro` (kilka kontrolnych SELECT-ow: `baza_analizy_e2a.db`, `baza_analizy_w2.db`, `baza_analizy_e2b.db`, `baza_odcinki_b1510off_v2.db`). Nic nie zapisano w C:\projects\sql_tsd_fwd ani C:\WORK\DOKTORAT. Jedyne pliki zapisane: ten raport oraz pomocnicze `verify_k.py`, `r4_table.md` w scratchpadzie.
Data przegladu: 2026-11-13. Wszystkie sciezki skryptow: `C:\projects\sql_tsd_fwd\bak\<nazwa>.py`.

## 0. Podsumowanie, znalezione / nieznalezione

| Skrypt z zadania | Status | Linie |
|---|---|---|
| e2aR2_rules.py | jest | 646 |
| e2a3f_range.py | jest | 455 |
| e2aR4_indices.py | jest | 722 |
| b1510off_v4_import.py | jest | 906 |
| e2a_autc_1b.py | jest | 545 |
| e2a2b_beta.py | jest | 767 |
| e2b2_values.py | jest | 860 |
| backcal.py | jest | 574 |
| datasets.py | jest | 386 |
| paths.py | jest | 119 |
| import_station_fwd.py | jest | 876 |
| e0_fwd_temp.py | jest | 751 |
| kontrola2_*.py | **tylko `kontrola2_nachylenia.py`** (736 l.). Innych `kontrola2_*` (np. kontrola2_k1...) w `bak\` NIE MA; w `plots\kontrola\` sa tylko PNG `kontrola2_k1..k5_*.png`, generowane przez ten jeden skrypt (K1-K6). Kopia w `.claude\worktrees\adoring-colden-d22ad7\bak\` pominieta (duplikat). | 736 |

Nie znaleziono tez **jednego** skryptu realizujacego caly lancuch N3 (Hampel na d0 + korekta wykladnicza beta=1,60 + okno +-5..10 m + GoF jako atrybut + agregacja 50/100 m + flagi QC). Elementy sa rozproszone (patrz sekcja 13).

Skrypty dodatkowe, ktore musialem przeczytac, bo sa zaleznosciami zadanych (opisane skrotowo w sekcji 12): `e2a3_beta.py` (E3), `e2a3i_final.py` (E3F), `e2a3d_nonlin.py` (ED), `e2a3e_range.py` (EE), `e2aR_equivalence.py` (R49, tylko verdict4), `e2aR2_rules_R4.py`, `w2_euler.py` (stale kanalow), `e2bR9_lustro_data.py` (Hampel), `z15_temp_correction.py` / `z15_curvature_correction.py` (korekta beta=1,60 na d0 TSD), `e1_sref.py` (s_ref, offset -4,8 m, biny), `qc_gyro_gps.py`, `qc_profile_consistency.py`, `scan_tsd_gps_segments.py`, `tsd_pipeline.py` (projekt tsd_2_xml, zrodlo Hampela).

### 0.1 Srodowisko (wazne dla pakietu)

- Interpretery w systemie: miniconda 3.13 (numpy 2.4.2, pandas 3.0.1, xlrd 2.0.2, **brak scipy**), Python 3.14 x2 (brak numpy). Skrypty projektu wymagaja **scipy** (`brentq`, `minimize_scalar`, `root`, `PchipInterpolator`, `pearsonr/spearmanr/theilslopes`) oraz **numpy >= 2.0** (`np.trapezoid`). Dokumentacja skryptow (e2a2b) mowi "pandas niedostepny w srodowisku projektu" - to jest nieaktualne (pandas jest), a scipy w srodowisku diagnostycznym nie. Pakiet tsdfwd_tools musi zadeklarowac zaleznosci jawnie (numpy>=2, scipy; pandas opcjonalnie).
- Weryfikacje liczbowe w sekcji 14.1 wykonalem czystym numpy (bisekcja QP + zlota sekcja dla k) - dziala bez scipy.

---

## 1. paths.py (119 l.)

- Sciezka: `bak\paths.py`. Brak funkcji obliczeniowych; zaleznosci: tylko stdlib (`os`, `sqlite3`, `sys`).
- Stale: `ROOT = dirname(dirname(abspath(__file__)))`; katalogi `bazy`, `tabele`, `tabele\kontrolne`, `logi`, `plots`, `narzedzia`, `archiwum`, `do_usuniecia`; bazy: `DB_ODCINKI=bazy\baza_odcinki_v4.db`, `DB_MIKRO`, `DB_ODCINKI_1KM`, `DB_STACJE`, `DB_PRODUKTY*`, `DB_ANALIZY_E2A/E2B/W2`, `DB_ODCINKI_B1510OFF=bazy\baza_odcinki_b1510off_v2.db` (v1 wycofana), `TSD_COLUMN_MAP_CSV`, `CONTROL_DIR`, `PLOTS_E2A`, `LOGS_E2A`...
- Funkcje publiczne: `log_path(stage_dir, name)`; `release_guard(db_path, allow=None) -> bool` (SystemExit gdy baza ma `data_release` lub jest aktywna baza zbioru przy istniejacym `RELEASE_R*.md`); `_norm`.
- Pulapki: (1) **efekt uboczny importu** - `ALLOW_RELEASE_WRITE` i usuniecie `--allow-release-write` z `sys.argv` przy imporcie; (2) wszystkie sciezki wyliczane z polozenia pliku (zmiana struktury = zmiana tu); (3) straznik wydania to logika specyficzna dla projektu badawczego - do pakietu nie przenosic.

## 2. datasets.py (386 l.)

- Rola: warstwa dostepu do 4 zbiorow (odcinki, odcinki_1km, mikroodcinki, stacje) + produkty; polaczenie w pamieci z `ATTACH ... mode=ro` i widokami TEMP `v_all_*` (UNION ALL, kolumny `dataset`, `dataset_role`).
- Funkcje publiczne (sygnatury): `role_of(dataset)`, `tier_of(dataset, date_str)`, `class DatasetConnection(sqlite3.Connection)` (atrybuty `info`, `views`), `build_view(conn, view, attached)`, `temp_view_sql(ds, info, conn)`, `build_temp_view(conn, attached)`, **`connect(datasets=ALL_DATASETS, products=True, specs=None)`**, `exclusions(conn, dataset, level, purpose, include_sensitivity=False) -> set[str]`, `describe(table)`. Slowniki: `SPECS`, `VIEW_TABLES`, `DERIVED`, `DATASET_ROLE`, `TABLE_DESCRIPTIONS`, `SNAPSHOT_SUFFIX_DESC`.
- Co liczy: nic numerycznego. Jedyny wzor: `v_all_fwd_temp` - jednolita temperatura FWD: dla `odcinki` `t_surface=COALESCE(surface_temp_med3, surface_temp)`, `t_layer=asphalt_temp`, `t_layer_source` = operator_carried / operator_entry; dla mikro/1km temperatura warstwy z `fwd_layer_temp_measured` ('measured_series'); dla stacji sondy 4/8/12 cm lub `met_t12`.
- Stale: `TIER_CURRENT_FROM='2024-03-01'` (serwis TSD, rejestrator 2.0), `FLAG_PURPOSES=('noise','level','conversion','temperature')`.
- Zaleznosci: `paths`, `e0_fwd_temp.sqlite_uri` (import ciezkiego modulu tylko dla jednej funkcji), `sys.path.insert(0, HERE)`.
- Pulapki: silne sprzezenie ze schematem baz projektu (nazwy tabel, `fwd_files.trailer`); brak sensu w pakiecie narzedzi - N1/N3 maja dostawac dane z plikow, nie z baz.

## 3. e0_fwd_temp.py (751 l.) - temperatury FWD (zrodlo temperatury dla N1)

- Cel: z `v4.fwd_stations` (asphalt_temp wpisywana RECZNIE przez operatora, surface/air - czujnik) buduje tabele `fwd_station_temp`, `fwd_session_temp_summary`, `fwd_temp_checks`.
- Funkcje: `sqlite_uri(path, **params)`, `check_paths(db,out_db)`, `open_out`, `file_stamp`, `log_run`, `haversine_m(lat1,lon1,lat2,lon2)`, `parse_t(s)` (format `%Y-%m-%d %H:%M:%S`), `differs(a,b)`, `change_share(vals)`, **`classify_session(st, gap_factor=3.0, gap_min_s=150.0, gap_q=0.90, min_regular=5)`**, `surface_spikes_med3(st, jump_c=5.0)`, `placeholder_runs(st,key,values=(20.4,),tol=1e-3,near=3)`, `trust_rules(st, sp, const_min=20, min_h=1.0, manual=MANUAL_UNTRUSTED)`, `pct`, `replace_tables`, `plot_sessions`, `main`.
- Logika `asphalt_status`: `entry_first` (pierwsza niepusta wartosc sesji), `entry_change` (|v - poprzednia niepusta| > 1e-6), `entry_possible` (bez zmiany, ale odstep od poprzedniej stacji > max(150 s, 3*P90 odstepow "zwyklych" sesji)), `carried` (przeniesiona), `missing`. Pomiarem sa TYLKO `entry_first/entry_change` (flaga `temp_entry` w e2b2_values).
- Stale na sztywno: zakres fizyczny `TEMP_RANGE=(-10,60)`, `JUMP_C=5`, `PLACEHOLDER_VALUES=(20.4,)` (wartosc zastepcza aparatu), `PLACEHOLDER_MIN_H=1`, `CONST_MIN_STATIONS=20`, `MANUAL_UNTRUSTED` (sesje s258 asphalt, s225-227 air - dane projektowe).
- Pulapki: wartosc 20,4 C = placeholder aparatu (wylaczana jako niezaufana); `surface_temp_med3` = mediana 3 stacji; brak konwersji temperatury powierzchni na temperature warstwy 12 cm (to robi model Z15 w DOKTORAT - patrz sekcja 13.2).
- Dla N1: przeniesc idee klasyfikacji (entry/carried) jako flage jakosci temperatury; reszta (baza) - nie.

## 4. e2aR2_rules.py (646 l.) - postacie regul korekty (R1, R2, R3a/b)

- Krok P050: porownanie regul R1 (krajowa, `f=1+0,02*(20-T)`, zakres wg dokumentu 5-25 C), R2 (rozporzadzenie 2002, `f=1+0,01*(20-T)`, 0<T<=35 C - **niezweryfikowane w dokumentach zrodlowych**, jak przyznaje docstring), R3a (wykladnicza, STALE beta z `e2a3_final_k_profile`, scope=lacznie), R3b (beta dopasowane od nowa w kazdej replice, kontrola zgodnosci z P049).
- **Funkcje publiczne:**
  - `apply_rule(y, T, form, param)`: `form=='guideline'` -> `y*(1.0 + param*(20.0 - T))`, **kazde inne `form`** -> `y*np.exp(param*(20.0 - T))`. Wynik: D znormalizowane do 20 C (mnoznik `D20 = D_T * f(T)`). Dziala na skalarach i ndarray.
  - `load_rule3a_betas(conn, log_) -> {indicator: beta_ulamek}` (SELECT z `e2a3_final_k_profile` WHERE scope='lacznie' AND indicator IN ('D0','D300','D900','SCI300'); `beta = beta_pct/100`).
  - `filter_thaw(T, y, pid, day, month, variant)`; `build_krok1(visits, rules, log_)`; `control_krok1(krok1_rows, log_)`; `build_krok1b(visits, rules, n_boot, log_)`; `run_band_fixed(T, y, group_key, day, form, param, n_boot, seed_tag, min_n_band=RNG.MIN_N_BAND)`; `verdict_or_brak_danych(estimate, ci90_lo, ci90_hi, ci95_lo, ci95_hi, delta)`; `krok2_band_rows_from_fixed(band_results, scope, group_variant, indicator, rule, thaw_variant)`; `krok2_band_rows_from_r49(...)`; `build_krok2_stations(visits, rules_fixed, beta3a, n_boot, log_)`; `build_krok2_micro(points, rules_fixed_no_r3a, n_boot, log_)`; `control_krok2`; `make_fig_rules(lang, out_dir, bands_rows_d0, withinday_rows_d0, conn=None)`; `main()`; pomocnicze `log`, `md5_r2`, `write_csv`, `insert`.
- Wzory/algorytmy: patrz sekcja 5 (l20_error), bo `run_band_fixed` wola `RNG.l20_error(T, y, group_key, param, form)`. Dodatkowo: werdykt rownowaznosci (Lakens, 4 kategorie + BRAK_DANYCH), `delta in {1.37, 2, 3, 5}` [%].
- Wejscia: `visits` = wiersze `e2a3_visits` z `baza_analizy_e2a.db` (848 wizyt TN+Podkowa, 2025-03-20..2026-08-12; 515 z `has_met & !excl_frost`), `points` = mikroodcinki (`ED.load_micro_points`). Jednostki: D w um znormalizowane do 50 kN, T w C (T_mid z czujnikow stacji, patrz sekcja 12.1).
- Wyjscia: `tabele\e2aR2_rules_{cv,withinday,bands}.csv`, `e2aR2_rules_summary.md`, rysunki PNG/PDF, **zapis do `baza_analizy_e2a.db`** (po kopii `_pre_p050.db`; `DROP TABLE IF EXISTS e2aR2_*`), logi.
- Stale na sztywno: `RULE_INDICATORS=['D0','D300','D900','SCI300']`, `T_RANGES=[(5,25),(5,30),(0,35)]`, `THAW_MONTHS=('02','03')`, `BANDS8` (0-5,5-10,10-15,15-20,20-25,25-30,30-35,gt35), `REF_BANDS={'15_20','20_25'}`, `N_BOOT_DEFAULT=1000`, `CTRL_TOL_KROK1=1e-4`, `CTRL_TOL_KROK2=0.01`, k=0,02 (R1), 0,01 (R2). Referencja 20 C zakodowana w literalach `20.0` (nie ma parametru T_REF).
- Zaleznosci projektowe (import): `paths`, `e2a2b_beta`(QP), `e2a3_beta`(E3), `e2a3d_nonlin`(ED), `e2a3e_range`(EE), `e2a3f_range`(RNG), `e2a3i_final`(E3F), `e2aR_equivalence`(R49), `cowork_e2a\pub_e_figures`(PEF), `e0_fwd_temp.sqlite_uri`; biblioteki numpy, matplotlib.
- Pulapki:
  1. **`apply_rule` ma ciche fallback na postac wykladnicza** dla dowolnej wartosci `form` != 'guideline' (literowka = inna regula). W pakiecie: enum + wyjatek.
  2. Brak kontroli zakresu T (5-25 C "zakres stosowania wytycznych" nie jest egzekwowany; dla `guideline` przy duzym T czynnik moze byc <=0 - tylko `l20_error` to filtruje `f_t > 0`).
  3. Konwencja: mnoznik do 20 C `D20 = D_T * f(T)`, czyli D_T rosnie z T, wiec dla T<20 f>1 (D20 > D_T). `beta>0` = wzrost ugiecia z temperatura.
  4. R3b w kroku 2 liczone na zbiorze NIEFILTROWANYM (etykieta `thaw_variant='all_p049'`), a R1/R2/R3a osobno na `no_thaw` / `thaw_only` - inne uniwersum dni do resamplingu (swiadoma decyzja z uzasadnieniem w docstringu `build_krok2_stations`).
  5. Wizyty tylko z T_mid>=5 C z referencja 15-25 C w TEJ SAMEJ grupie punkt x miesiac: pasma <10 C daja `BRAK_DANYCH` (patrz tabela R4, sekcja 14.2) - nie da sie zweryfikowac korekty ponizej ~10 C na stacjach.
  6. `krok1b`: grupy punkt x dzien (>=2 wizyty, rozpietosc T>=3 C), klasy sredniej dziennej T: <10 / 10-20 / >=20.

## 5. e2a3f_range.py (455 l.) - rdzen oceny bledu normalizacji (l20_error, fit_params)

- P035: poprawka bledu referencji z P034 (D20,ref liczone ze znormalizowanych, nie surowych ugiec). **Funkcje publiczne:**
  - **`fit_params(T, y, group_key, k_bounds, min_n_fit=30) -> dict|None`**: maska `5.0 <= T <= 25.0` (DOMKNIETA); jesli n<30 -> None. `k_hat,_,_,ok_k = E3.fit_k_profile(T[m], y[m], group_key[m], k_bounds)` (postac liniowa); `b_beta,_,ok_beta = QP.qp_fit_nd((T[m]-20).reshape(-1,1), y[m], group_key[m])` (log-link quasi-Poisson, efekt staly grupy). Zwraca `dict(k_hat, ok_k, beta_hat, ok_beta, n_fit)`.
  - **`l20_error(T, y, group_key, param, form, min_group_ref=2) -> (e[%], keep)`**: `f_t = 1 + param*(20-T)` (guideline) lub `exp(param*(20-T))`; `valid = isfinite(f_t) & f_t>0 & isfinite(y) & y>0`; `lnD20 = ln y + ln f_t`; referencja grupy = SREDNIA `lnD20` z wizyt `15 <= T <= 25` (domkniete) o ile >= `min_group_ref`=2 takich wizyt w grupie; `e = 100*(lnD20 - ref_grupy)`; `keep = valid & (grupa ma referencje)`.
  - `band_mean(T, e, keep, lo, hi, min_n=20) -> (srednia, n)` (pasmo `[lo,hi)`, `hi=inf` dla gt35; NaN gdy n<min_n).
  - `run_range30_core_v2(T, y, group_key, day, indicator, bands, wide_bands, n_boot, seed_tag, log_, min_n_fit=30, min_n_band=20, k_bounds=ED.K_BOUNDS)`: punktowo + bootstrap blokowy po dniach/nocach (1000 replik, refit k i beta w kazdej replice, CI percentylowe 2,5/97,5).
  - `run_range30_stations(visits, n_boot, log_)`, `micro_xy_variant_v2(points, indicator, sections, group_variant)`, `run_range30_micro(points, n_boot, log_)`, `repeatability_rows_v2(visits, scope, indicator, n_boot, log_, max_dts=(1.0,2.0))` (sigma wizyty = RMS(100*ln(v2/v1))/sqrt(2) dla par tego samego dnia/punktu z |dT|<max_dt), `run_repeatability`, `plot_error_range`, `md5`, `md5_r2`, `write_csv`, `insert`, `main`.
- Wejscia/wyjscia/zaleznosci jak w sekcji 4; zapis do `baza_analizy_e2a.db` (tabele `e2a3_range30_v2`, `e2a3_range30_micro_v2`, `e2a3_repeatability`; kopia `_pre_p035.db`, **STOP gdy kopia juz istnieje**).
- Stale: `BANDS30_V2` (15-20, 20-25, 25-27.5, 27.5-30, 30-32.5, 32.5-35, gt35), `WIDE_BANDS_V2` (20-25, 25-30, 30-35), `GROUP_VARIANTS_V2=['point_month','point_season']`, `SEASON_BY_MONTH`, `MIN_N_FIT=30`, `MIN_N_BAND=20`, `MIN_GROUP_REF=2`; `K_BOUNDS=(-0.08, 0.08)` z ED.
- Pulapki:
  1. **Niespojnosc granic zakresu dopasowania:** `RNG.fit_params` uzywa `T <= 25.0` (domkniete), a `e2aR4.fit_params_range` uzywa `T >= t_lo & T < t_hi` (otwarte); `E3F.get_data` (P040) uzywa `5 <= T < 30`. Roznica miala znaczenie tylko dla wartosci rowno na granicy, ale w pakiecie ustalic JEDNA konwencje.
  2. Prog `y>0` w `l20_error` wyrzuca wizyty z niedodatnim wskaznikiem (SCI/BDI/BCI po korekcie moga byc <=0) - n_nonpos raportowane w e2aR4.
  3. Referencja grupy jest liczona na PROBCE (powtarza sie w bootstrapie) - nie jest to znany, stalym wspolczynnik; do N1 bardziej przydatne jest `apply_rule` ze stalym parametrem.
  4. Wizyty tego samego punktu o temperaturach w jednym pasmie moga miec ref z innymi wizytami z tego samego miesiaca (efekt miesiaca w grupie).
  5. Moduly cale sa 'badawcze' (bootstrap, pasma, CI) - do pakietu przeniesc tylko `fit_params` (opcjonalnie) i `l20_error` jako diagnostyke.

## 6. e2aR4_indices.py (722 l.) - SCI300/BDI/BCI z czaszy skorygowanej

- P052: warianty CB (kazdy geofon D0,D300,D600,D900 korygowany WLASNYM wspolczynnikiem, potem roznice), OWN (kontrola - wskaznik z wlasnym wspolczynnikiem), R1 (k=0,02 na kazdym geofonie), R2 (k=0,01).
- **Funkcje (sygnatury):** `get_sigma_tn(conn)`, `load_station_rows(visits, scope, t_lo=None, t_hi=None) -> (T, geo{D0,D300,D600,D900}, pid, day, month)` (wymaga `has_met`, `!excl_frost`, `t_mid_met` skonczone, **wszystkie 4 geofony > 0**, `T < t_hi` otwarte), `load_micro_own(points, indicator, group_variant='point_month')`, `load_micro_rows(points, group_variant='point_month')`, **`apply_f(Dg, T, p, form)`** (`Dg*(1+p*(20-T))` lub `Dg*exp(p*(20-T))`), **`build_index20(T, geo, param, form) -> {'SCI300': D0_20-D300_20, 'BDI': D300_20-D600_20, 'BCI': D600_20-D900_20}`**, `fit_params_range(T, y, group_key, k_bounds, min_n_fit, t_lo, t_hi)`, `fit_geo_point(T, geo, group_key, k_bounds, min_n_fit, t_lo=5.0, t_hi=25.0)`, `geo_params_ok(fp, form)`, `geo_params_get(fp, form)`, `ci_from_boots(boots, n_boot)`, `run_bands_core(T, geo, group_key, day_or_night, form, fit_mode, fixed_param, bands, wide_bands, n_boot, seed_tag, k_bounds=ED.K_BOUNDS, min_n_fit=RNG.MIN_N_FIT, min_n_band=RNG.MIN_N_BAND)`, `ratio_error_rows(T, I20_all, group_key, bands, wide_bands, min_n_band)` (wariant ilorazowy `e=100*(I20/ref_arytm-1)`), `ratio_rows_to_verdicts`, `verdict_or_brak_danych`, `band_rows_to_verdicts(rows, scope, group_variant, variant, form, sigma_tn, error_def='log', n_nights_of=None)`, `count_nights_per_band`, `run_a1_stations`, `run_a1_micro`, `norm_row`, `control_a1_own`, `build_a3`, `make_fig11`, `other_files_md5`, `main`.
- Wzory: `SCI300_20 = D0*f0(T) - D300*f300(T)`, `BDI_20 = D300*f300 - D600*f600`, `BCI_20 = D600*f600 - D900*f900`, gdzie `f_g(T)` = `1+k_g(20-T)` albo `exp[beta_g(20-T)]`, wspolczynniki per geofon dopasowane 5-25 C (A1/A2) albo 5-30 C przez `qp_fit_nd` (A3, tylko wykladnicza). Blad: `e = 100*(ln I20 - srednia ln I20 wizyt 15-25 C w grupie)` przez `RNG.l20_error(..., param=0.0, 'guideline')` (f_t=1 tozsamosciowo).
- Wejscia: `visits` jak wyzej; `e2a3_repeatability_v3` (sigma TN jako delta), `e2a3_final_norm_test` (kontrola), `e2aR_equivalence` (kontrola). Wyjscia: `tabele\e2aR4_{indices_bands,indices_norm,coefs}.csv`, zapis do `baza_analizy_e2a.db` (kopia `_pre_p052.db`), rysunek fig11.
- Pulapki:
  1. **`e2aR4_coefs.csv`: kolumna `n` to liczba zbieznych replik bootstrapu (np. 984), NIE liczba danych** (`n=len(bvals)`), mimo nazwy.
  2. Populacja CB jest mniejsza niz "wlasna" (wymaga 4 geofonow >0 w wierszu) - w `e2aR2_rules_R4.py` to samo (n_all identyczne w tabeli, ale `n_with_ref` SCI300 30_35: 24 vs 25).
  3. Wskaznik korygowany z roznicy ugiec moze byc <=0 -> `n_nonpos`; wariant 'log' go pomija, 'ratio' liczy wszystkie.
  4. Kontrole `STOP` (sys.exit(2)) gdy OWN/A3 nie odtworza starszych tabel do 0,01 pp / 1e-4 - badawcze zabezpieczenie.
  5. Dla N1 ta logika (korekta geofon po geofonie, potem roznice) jest dokladnie tym, co powinien robic `fwd_tempcorr` dla SCI300/BDI/BCI z "ugiec skorygowanych"; reszta pliku (pasma, werdykty, rysunki) jest do pominiecia.

## 7. e2a_autc_1b.py (545 l.) - AUTC (calka nachylen), zestawy zer

- A1 (wpis 95, P024): test calki nachylen TSD na mikroodcinku 1b. Zrodla: baza mikroodcinkow (`mik.tsd_measurements`), `p_mik.tsd_sref`, `baza_analizy_e2a.db` (`mikro_points_tsd`, `temp_sens_fwd_mikro`).
- **Stale polozen kanalow** [m] wzgledem kola: `FRONT_X = {'0110':0.110,'0210':0.210,'0310':0.310,'0460':0.460,'0610':0.610,'0910':0.910,'1510':1.510}` (przod, **dodatnie**), **`REAR_X = {'m200':0.200,'m300':0.300,'m450':0.450}` (tyl, wartosci DODATNIE = modul)**; `ALL_CHANNELS = list(FRONT_X)+list(REAR_X)` (10 kanalow); `AUTC_FRONT_STAGES`: `autc_031=[0110,0210,0310]`, `autc_061=+[0460,0610]`, `autc_091=+[0910]`, `autc_151=+[1510]` (kontrolnie); `AUTC_061_CHAIN`; `COEF_COLS` (kolumny CSV `s1510..sm0450` -> klucze kanalow); `VARIANTS=('nominal','A_all','B_all','C_all')`; `GOF_MIN=0.5` (tylko informacyjnie - `n_gof05_window`, bez filtrowania); `FWD_D_OF_MM={0:'d1',200:'d2',300:'d3',450:'d4',600:'d5',900:'d6',1200:'d7',1500:'d8',1800:'d9'}`; `AUTC_TO_FWD`.
- **Funkcje:**
  - `load_coefficients(csv_path) -> {set_id: {kanal: float [urad = um/m]}}` (CSV `tabele\kontrolne\tsd_wspolczynniki.csv`, **separator `;`**, kodowanie utf-8-sig).
  - `zestaw_pliku(series_date) -> 'A'|'B'|None`: `<= '2026-03-19'` -> A; `>= '2026-05-14'` -> B; luka -> None (STOP). Logika WYLACZNIE dla mikroodcinkow (nocne serie 2025-09..2026-08).
  - `apply_variant(raw, file_set, variant, coef) -> dict`: `'nominal'` lub `file_set is None` -> kopia; inaczej `slope_X = raw_X + (coef[target][X] - coef[file_set][X])`, `target = variant.split('_')[0]` (np. `'B_all'`->`'B'`, takze `'B'`). Przesuniecie stala per kanal; **KeyError gdy `file_set` spoza A/B/C** (np. NEW1..NEW4 z P044; w b1510off_v4_import uzywany `load_full_coef`).
  - **`autc_front(slopes, stage_channels) -> float`**: `xs=[0]+[FRONT_X[c]]`, `ys=[0]+[slopes[c]]` (**wymuszone slope(0)=0**), `np.trapezoid(ys, xs)`; NaN gdy jakikolwiek y nieskonczony. Trapez z "trojkatem" 0..0,11 m.
  - `autc_rear(slopes)`: `trapezoid([0,|s_m200|,|s_m300|,|s_m450|], [0,0.2,0.3,0.45])`.
  - `zero_crossing_x0(slope_m200, slope_0110)`: miejsce zerowe prostej przez (-0,20; s_m200) i (0,11; s_0110): `x0 = -0.2 - y1*(0.31)/(y2-y1)`; NaN gdy y1==y2. `autc_061_x0(x0, slopes)`: calka od x0 (slope=0) do 0,61; NaN gdy `x0 >= 0.11`.
  - `load_tsd_rows(conn)`: SELECT slope_* + goodness_of_fit z `mik.tsd_measurements` + `p_mik.tsd_sref WHERE lane_fit='lane'` -> `pass_id`, `s_ref` (wiersze bez s_ref: `pass_id=-1`).
  - **`window_medians(D, pass_id, s_point, half=5.0) -> (dict kanal->mediana, n, n_gof05)`**: wiersze z `|s_ref - s_point| <= half` (DOMKNIETE) w obrebie `pass_id`; mediana (NaN-odporna `nmed`) kazdego z 10 kanalow; bez filtra GoF.
  - `load_points`, `load_fwd` (normalizacja FWD `d*50/F`; `fwd_d0_300 = d1-d3` itd.), `ols_slope`, `demean_by_group`, `trend_row`, `build_point_rows`, `aggregate_nights`, `build_trends`, wykresy, `main`.
- Wzory: `AUTC_T(x_max) = int_0^{x_max} slope(x)dx` trapezami z punktami (0,0), (x_i, s_i); jednostki: slope [um/m = urad], calka [um]. Interpretacja: AUTC_031 ~ D0 - D300 (SCI300), AUTC_061 ~ D0 - D600, AUTC_091 ~ D0 - D900.
- Zestawy zer (`tsd_wspolczynniki.csv`; wartosci [um/m] w kolejnosci s1510;s0910;s0610;s0460;s0310;s0210;s0110;sm0200;sm0300;sm0450):
  - A (do 2026-03-20): -223,6; 42,0; -276,2; -11,0; -443,4; 401,9; 290,8; -162,1; -394,8; 69,0
  - B (do 08.2026): -244,3; -5,6; -278,2; -17,7; -453,1; 346,7; 245,7; -220,1; -383,1; 60,1
  - C (kalibracja 2024-05-21): -188,0; 71,5; -184,5; 86,0; -337,5; 471,5; 449,5; -80,0; -242,0; 167,0
  - Dodatkowo w bazach (nie w CSV): `B_1510off` (`tsd_zero_sets` w e2a.db), `NEW1..NEW6` (w2_v4_zero_sets).
- Pulapki: (1) `REAR_X` dodatni vs `X_POS` ujemny w e2a2b/backcal (patrz nizej) - latwa pomylka znaku; (2) `autc_front` NIE interpoluje PCHIP (inaczej niz `dense_integral`), wiec `t_a031 != p0_a031` (mediany 35,69 vs 39,51 um w `e2a2_autc_var.csv`); (3) okno `s_ref` domkniete obustronnie; (4) mediany kanalow, a nie calki w oknie (w e2b2_values odwrotnie - mediana calek); (5) `zestaw_pliku` oparty na DACIE nocy - nie nadaje sie do odcinkow (tam zestaw per plik z naglowkow raw.pg2: `w2_v4_file_zero_set`: A 6, B 7, C 69, NEW1-4 156 plikow).
- Testy istniejace: `test_autc.py` (T1-T6: stale nachylenie, liniowe, niezmienniczosc na przesuniecie zer, norma FWD, x0, warianty).

## 8. e2a2b_beta.py (767 l.) - kanaly 9, dense_integral (calka P0), M8 (QP)

- P029. **Stale:** `T_REF=20.0`; **`CHANNELS_9 = ['m450','m300','m200','0110','0210','0310','0460','0610','0910']` (BEZ 1,51 m)**; `X_POS = {'m450':-0.450,'m300':-0.300,'m200':-0.200,'0110':0.110,...,'0910':0.910}` (**ze znakiem**); `XS_SORTED` (rosnaco, ndarray); `STAGES = {'a031':[0110,0210,0310], 'a061':+[0460,0610], 'a091':+[0910]}`; **`INTSTEP = 0.001`** (1 mm); `EXPOSURE` (nasloneczenie odcinkow 1a..5).
- **Funkcje publiczne:**
  - **`dense_integral(pchip, x0, x1, step=INTSTEP) -> float`**: `grid = arange(lo, hi + step/2, step)`, dolozony `hi` gdy `grid[-1]<hi`, `np.trapezoid(pchip(grid), grid)`, znak ujemny gdy `x0>x1`; 0.0 gdy `x0==x1`. **To jest calka P0.**
  - `find_x_max(pchip, lo=-0.200, hi=0.110) -> float`: `brentq` miejsca zerowego nachylenia (maksimum czaszy), NaN gdy brak zmiany znaku na [-0,20; 0,11]. (dodatnie = przed kolem).
  - `build_autc_var(slope_rows, log_)`: dla wiersza z 9 skonczonymi nachyleniami: `pchip = PchipInterpolator(XS_SORTED, ys)`; **P0: `p0_a031 = dense_integral(pchip, 0, 0.31)`, `p0_a061 = ...0.61`, `p0_a091 = ...0.91`, `p0_a0361 = p0_a061 - p0_a031`, `p0_a6191 = p0_a091 - p0_a061`**; wariant T (`AC.autc_front`, trapezy z slope(0)=0) -> `t_a*`; wariant PX (od `x_max`) -> `px_a*`; `ar045` = calka |slope| od -0,45 do x_max. Jesli jakikolwiek z 9 kanalow nieskonczony -> wszystkie NaN. Okno calkowania [0, 0.91] lezy wewnatrz zakresu wezlow [-0.45, 0.91] - brak ekstrapolacji PCHIP.
  - `build_slopes(conn, pts, coef, log_)`: dla punktow `valid`, `fset = AC.zestaw_pliku(date)`, mediana w oknie +-5 m (`AC.window_medians`), `AC.apply_variant(raw, fset, 'B_all', coef)`.
  - **Estymatory:** `qp_fit_1d(x, y, groups, bracket=(-0.5, 0.5)) -> (beta, n, ok)`; `qp_fit_nd(X, y, groups, x0=None) -> (beta ndarray, n, ok)`; `ols_fe_1d(x, y, groups) -> (nachylenie, n)`; `bootstrap_draws(universe, n_boot, seed)`; `bootstrap_qp(x, y, groups, resample_key, draws)`; `_prep_groups(y, groups)`.
  - `run_m8/run_m9/run_m10`, `section4_diagnostics`, `plot_*`, `main`, `validate_t_vs_points`, `build_m8_dataset`, `indicator_xy`, `build_section_attributes`, `nmed`, `md5`, `md5_r2`, `write_csv`, `insert`.
- Wzor QP (conditional Poisson, efekt staly grupy g): `mu_i = S_g * exp(x_i*beta) / sum_{j in g} exp(x_j*beta)`, `S_g = sum y w grupie`; rownanie wynikowe `sum x_i (y_i - mu_i) = 0` (brentq na [-0,5; 0,5] dla 1 kowariaty; `scipy.optimize.root(hybr)` dla wielu); grupy z `S_g <= 0` odrzucone; **min. 20 obserwacji i 2 grupy** inaczej `ok=False`; wiersze <=0 zostaja (metoda momentow). Kowariata `x = T - 20`. `beta` = wzgledna zmiana na 1 C (ln); `pct = 100*beta`.
- Wejscia: `e2a2_points`, `mikro_points_tsd`, `tsd_measurements` (mikro), `tsd_wspolczynniki.csv`; wyjscia: tabele CSV `e2a2_slopes`, **`e2a2_autc_var`**, `e2a2_beta_m8`, `..._pairs_m8`, `..._exposure`, `..._m10`, `section_attributes` + tabele w `baza_analizy_e2a.db` (kopia `_pre_p029.db`, nadpisanie bez sprawdzenia istnienia kopii: `shutil.copy2` zawsze).
- Pulapki: (1) `np.trapezoid` (numpy>=2); (2) `X_POS` ze znakiem vs `AC.REAR_X` modul; (3) kanal 1,51 m wykluczony wszedzie (B_1510off ma celowo przesuniety zero tego kanalu - "off"); (4) `P0` nie wymusza slope(0)=0 (PCHIP przechodzi przez (-0,2; s_m200) i (0,11; s_0110)); (5) `find_x_max` i `PX` - nie potrzebne dla N3; (6) `M8_INDICATORS` ma stale 'sci300_prod_tsd' = `d0 - d300` z eksportu (nie z calek).
- Testy istniejace: `test_e2a2b.py` T1-T5 (x_max, calki dla profilu liniowego `a*(x-x0)`: P0(x1) = a*(x1^2/2 - x0*x1), QP odtwarza beta, zgodnosc z implementacja Cowork 1e-6).

## 9. e2b2_values.py (860 l.) - reprezentacje P / W1 / W2,5 / W5, mediana calek, lambda

- P047/P047b. Wejscia: `baza_analizy_e2b.db` (`golden_pair_candidates`, `e2b1_null_map`), `baza_odcinki_b1510off_v2.db`, `baza_odcinki_v4.db` (+ produkty: `tsd_sref`, `tsd_passes`, `e1_bin_pairs`, `e12_lambda`, `fwd_station_temp`), `baza_analizy_w2.db` (`w2_v4_file_zero_set`, `w2_frozen_params`), `tsd_wspolczynniki.csv`. Wyjscie: tabele `e2b2_pairs/fwd_values/tsd_values/null_values/lambda` w `baza_analizy_e2b.db` (+CSV w `tabele\`), archiwizacja `_p047` przez `ALTER TABLE RENAME`.
- **Funkcje (sygnatury):** `load_pairs(e2b_path, b1510_path, log_) -> (rows, n_ab)`, `load_file_zero_set(w2_path, log_)`, `load_null_pairs_w5(e2b_path, pair_ids, log_)`, **`match_geophone_indices(x_vals) -> {'d0':'d1',...}`** (dopasowanie offsetu [mm] z `x1..x9` sesji, tolerancja `FWD_OFFSET_TOL_MM=1.0`), `is_standard_layout(x_vals)` (0,200,300,450,600,900,1200,1500,1800), **`load_fwd_values(odc_conn, prod_conn, station_ids, log_)`**, `load_b1510_by_file(b1510_path, file_ids, log_)`, `load_pgc_by_file(odc_conn, file_ids, coef, file_set_map, log_)`, **`row_curv_integrals(slopes_col) -> {a031,a0361,a6191,a061,a091}`**, `precompute_row_integrals(pgc_file)`, `load_wavelet_params(w2_path, log_)`, `denoise_pass_slopes(pgc_file)`, `window_extract(sorted_ids, lo_id, hi_id)`, `nearest_index(sorted_ids, target)`, **`tsd_values_for_window(b1510_file, pgc_file, row_integrals, lo_id, hi_id, nearest_id, is_point, denoised_integrals=None)`**, `build_tsd_values`, `build_null_values`, `load_bin_pairs_same_day`, `load_sref_bins_by_file`, `_bin_values_by_key`, **`compute_lambda_d0_and_curv(...)`**, `load_fwd_sigma`, `build_lambda_rows`, `nmed`, **`mad_robust_sd(x) = 1.4826*median(|x-med|)`**, `infer_ddl_types`, `archive_table_once`, `create_and_insert`, `md5`, `md5_r2`, `write_csv`, `main`.
- Co liczy:
  - FWD (krok 2): dla stacji - SREDNIA z zrzutow nieosiadczych (`is_seating=0`, `force>0`, `d>0`) `d_i*50/F` [um] dla geofonow 0/200/300/600/900 mm; `SCI300=D0-D300`, `BDI=D300-D600`, `BCI=D600-D900`, `D0-D600`, `D0-D900`; flaga `flag_geophone_layout` (nietypowy uklad), `temp_entry` (asphalt_status in entry_first/entry_change). **Bez korekty temperaturowej.**
  - TSD (krok 3): (a) `d0` z `b1510off_measurements.d_d0` (znak zdjety przy imporcie); (b) krzywizny z nachylen pgc (tsd_measurements v4) sprowadzonych do zestawu B (`apply_variant(raw, file_set, 'B', coef)`, zestaw pliku z `w2_v4_file_zero_set`): w KAZDYM WIERSZU calki P0 `a031=P0(0,31)`, `a061=P0(0,61)`, `a091=P0(0,91)`, `a0361=a061-a031`, `a6191=a091-a061`; reprezentacje: **P** = najblizszy wiersz (`nearest_index` po `tsd_id`, remis -> lewy), **W1/W2,5/W5** = **mediana wartosci wierszowych** w oknie `tsd_id` min..max (okna +-1/2,5/5 m w s_ref policzone wczesniej w `golden_pair_candidates`: `win1_/win2_5_/win5_tsd_id_min/max`); okno uznane gdy `n_niepustych >= MIN_WINDOW_N=3` (P: >=1); `gof`, `speed` = mediana okna; `temp_road` = mediana (pgc).
  - (c) wariant falkowy W5 `a*_w5_dn`: nachylenia odszumione WZDLUZ CALEGO PRZEJAZDU (siatka 1 m z `chainage_m`, dziury NaN, `DN.run_method('wavelet_ti', {'rule':'fdr_0.05','wavelet':'haar'}, ...)`) PRZED calkami.
  - Lambda (krok 5): `bin = floor(s_ref/10)`, klucz `(corridor_id, bin_id)` (poprawka P047b), pary `e1_bin_pairs` (dt<=1 dzien, `concrete=0`, oba pliki `ok` i bez `align_fail`); roznica `ln(mediana_i) - ln(mediana_j)` binow; `sigma_TSD = mad_robust_sd(roznice)/sqrt(2)`; `lambda = sigma_FWD^2 / sigma_TSD^2` (`sigma_FWD` z `e12_lambda`, ge2024, 10 m); dla krzywizn jesli par <20 -> lambda d0 z notatka. **Kontrola STOP: lambda_d0 wzgledem 0,118 (+-20%)** - twardo wpisana w `main` (`LAMBDA_D0_CONTROL = 0.118`).
- Stale: `TARGET_YEARS=(2024,2025,2026)`, `MIN_WINDOW_N=3`, `STOP_MIN_PAIRS_AB=1000`, `MIN_PAIRS_LAMBDA_CURV=20`, `FWD_TARGET_MM`, `FWD_STANDARD_LAYOUT`, `FWD_OFFSET_TOL_MM=1.0`, **`K_D0=0.016` (martwa stala - nie uzywana w tym skrypcie; korekta temperaturowa jest w z15_* / e2b2_agreement)**, `T_REF=20`, `CURV_NAMES`, `WINDOWS4=(('p',None),('w1',1.0),('w2_5',2.5),('w5',5.0))`.
- Pulapki:
  1. **Mediana calek, nie calka z mediany** - `a0361_w5 != a061_w5 - a031_w5` (zbadalem `e2b2_tsd_values.csv`: rownosc zachodzi tylko w 49 z 9059 wierszy; na wierszach/`P` zachodzi dokladnie). e2a2b/e2a_autc_1b robia odwrotnie (calka z mediany nachylen).
  2. **Okna po zakresie `tsd_id`, nie po s_ref**: `window_extract` zaklada, ze zakres [min,max] `tsd_id` okna odpowiada ciagowi wierszy (monotonicznosc tsd_id vs s_ref); przy jezdzie "pod prad" w korytarzu mogloby objac za duzo.
  3. FWD: srednia ze WSZYSTKICH zrzutow nieosiadczych stacji; w stacjach (e2a3_beta/`v_station_point_drop2`) uzywany jest DRUGI zrzut (`drop_seq=2`). Rozne definicje "wartosci FWD stacji".
  4. `P` (najblizszy wiersz): remisy -> lewy; `d0_valid_p` = tylko "niepusty". 4725 z 9201 par ma `d0_p` (reszta NaN - brak wiersza B_1510off w mapowaniu tsd_id).
  5. Pierwotne P047 binowalo po pikietazie WLASNYM pliku (blad); naprawiono w P047b - dla N3 zasada: zawsze po wspolrzednej korytarza (s_ref), nigdy po chainage pliku.
  6. Odszumianie falkowe wzdluz przejazdu (zmienia dane) - tylko wariant W5_dn, "badawcze".
- Testy istniejace: `test_e2b2.py` (T1 Deming, T2 CCC/BA, T3 okna, T4 calki krzywizn / zestaw zer, T7 lambda binowanie, T9 wspolny offset PCHIP, T10 filtr GoF).

## 10. b1510off_v4_import.py (906 l.) - format eksportu B_1510off, zrownanie pikietazu blokami

- P046b. Zrodlo: `baza_TSD_FWD_odcinki\TSD\B_1510off\*.raw.sup.txt` (476 plikow = 238 par .txt/.xls). Zapis: `bazy\baza_odcinki_b1510off_v2.db` (tabele `b1510off_files`, `_zero_check`, `_alignment`, `_align_blocks`, **`_measurements` (1 423 864 wierszy)**, `_qc`) + CSV (bez measurements). Zakres: TYLKO lata 2024-2026 (82 pliki `ok`; 156 `out_of_scope_original_calib`).
- **Format pliku (sprawdzony na T4202008060001.raw.sup.txt):** sekcje `Headers:` (m.in. `Re-calibrationfile: ...\baza_b_1510off\t4202405210001.raw.pg2`), `Parameters:` (`Result interval: 1.0000 m`, `Model type: Asymmetrical model`, `GoodNess limit: 0.1500`, `Gyro: yes`, `GPS: yes`, ...), pusta linia, `Data:`, linia naglowkow kolumn rozdzielona `", "` (przecinek + spacja), potem wiersze 1 m rozdzielone `", "`. 86 kolumn: `Chainage [m]`, `Driving Speed [m/s]`, `GyroYaw/Roll/Pitch [rad/s]`, `Accl*`, `Strain Gauge Left/Right [kg]`, `Laser 0.0[mm]`, `Temp Road [C]`, `Temp Air`, `Temp Inside 8.4/3.4/0.5`, `Temp Beam*`, `Doppler <x> [m/s]` (11), `DeflVel <x> [mm/s]` (10), **`Slope <x> [um/m]` (10: 1.510, 0.910, 0.610, 0.460, 0.310, 0.210, 0.110, -0.200, -0.300, -0.450)**, `DoppDR`, **`D-450 ... D1800 [um]` (12 kolumn: -450,-300,-200,0,200,300,450,600,900,1200,1500,1800; `WE.D_COLS` ma tylko 11 - bez D1800)**, `Maximum Deflection [um]`, `Position of Max D [m]`, `Goodness of fit`, `Latitude`, `Longitude`, `Height`, `DOP`, `Satellites`, `GPS time`.
  - Jednostki w nazwach kolumn w nawiasach `[..]` (usuwane regexem `WE.strip_unit`); w pliku znak `um` bywa zapisany jako zastepczy znak '�' (kodowanie) - parser uzywa `encoding='utf-8-sig'`.
  - **D* sa UJEMNE w pliku** (np. D0 = -8342, wartosci calkowite w um); importer odwraca znak (`data[c] = -data[c]` dla `WE.D_COLS`). Nachylenia: dodatnie dla czujnikow przednich (np. +1453 um/m dla 0,110).
  - Chainage pliku B_1510off ma wlasna skale/offset wzgledem pgc; plik ma GPS (Lat/Lon), ale importer czyta TYLKO `NEEDED_COLS = {Chainage, Goodness of fit, Driving Speed, Temp Road, Temp Air, Maximum Deflection, Position of Max D} + D_COLS + SLOPE_COL.values()` - **lat/lon NIE sa importowane**; polozenie bierze sie z wiersza pgc po dopasowaniu.
- **Funkcje (sygnatury):** `parse_raw_sup_txt(path, log_, needed=NEEDED_COLS) -> (meta, data, slope_channels, n_rows, n_bad, error)`; `classify_file(meta, data, slope_channels, n_rows, pgc_row_count) -> (status, note)` (priorytet: `invalid_scale` [wiersze txt / wiersze pgc < 0,5] > `not_recalibrated` [pusty `Re-calibrationfile`] > `missing_channel` > `ok`); `load_full_coef(log_)` (A/B/C CSV + `B_1510off` z `tsd_zero_sets` + `NEWn`); `load_file_zero_set(log_)`; `zero_set_check(data, slope_channels, pgc_slopes, coef, pgc_export_set)` (rozbicie reszty na `common` = mediana po 9 czujnikach bez 1,51 m i `diff_k`; flaga gdy `max|diff_k| > ZERO_MISMATCH_THRESHOLD=15 um/m`); `load_pgc_file_data(conn, file_id)`; **`align_to_pgc(data_chainage, data_B, pgc_chainage, pgc_B) -> (lag, r)`**; `map_to_tsd_id(data_chainage, lag, pgc_chainage_sorted, pgc_tsd_id_sorted, tol=0.5) -> (tsd_id, beyond, unaligned)`; `build_blocks`, `align_block`, `reject_outlier_blocks(centers, lags, window=3, max_diff=3.0)`, `build_lag_function(centers, lags, extrap_limit=1500.0)`, `align_file_blocks(...)`, `ensure_tables`, `update_catalog`, `mikro_cross_check`, `check_golden_pair_coverage`, `main`.
- **Zrownanie pikietazu (algorytm):** profile `slope_0110` i `slope_0310` (po sprowadzeniu do zestawu B), interpolacja na siatke 1 m, srednia kroczaca 10 m (`profile_on_grid`, okno wymuszone nieparzyste), z-score obu kanalow i konkatenacja; lag -30..+30 m co 1 m, maksimum korelacji Pearsona (>= 20 punktow); zrownanie BLOKAMI 1000 m z krokiem 500 m; blok przyjety gdy `r >= R_THRESHOLD=0.9`; odrzucenie blokow odstajacych (|lag - mediana 3 sasiednich| > 3 m); lag(chainage) = interpolacja liniowa miedzy srodkami blokow + stala ekstrapolacja do 1500 m poza skrajne bloki; wiersz -> najblizszy wiersz pgc w tolerancji 0,5 m (`MATCH_TOL_M`), inaczej `tsd_id=NULL`, `flag_beyond_pgc`/`flag_unaligned`; `align_fail` gdy udzial zrownanych < 0,5; `scale_ppm = slope(lag vs centrum bloku)*1e6` (odchylenie skali pikietazu 1,4-1,6 promila w 2022/2023/2026).
- **Konwencja lagu:** `target = chainage_B + lag` -> szukany wiersz pgc (tj. `pgc_chainage = chainage_B + lag`). Przeszukiwanie +-30 m.
- Pulapki: (1) znak D (ujemne w pliku); (2) **dane D w pliku to liczby calkowite um** (kwantyzacja 1 um - wazne przy SCI/BDI, gdzie wartosci rzedu kilku um; `d0_w5` po medianie jest tez cal.); (3) kodowanie jednostek; (4) `slope_1510` jest "off" (kalibracja 1,51 m celowo przesunieta) - nie uzywac; (5) nachylenia z B_1510off niosa wspolny skladnik (`common_offset`) - do krzywizn brac z PGC po sprowadzeniu zestawu zer (docstring); z B_1510off tylko d0 i D*; (6) zaleznosc od `w2_euler` (importy `WE.*`), od pgc w bazie v4 (do `tsd_id`) i od `baza_analizy_w2.db`; (7) `Chainage` 1 m - przy `invalid_scale` (<0,5 wierszy wzgl. pgc) plik odrzucany; (8) walidacja (a) wymaga `mediana |lag blokowy - lag globalny| <= 1 m`.
- Dla N3 (nowy eksport B_1510off od IBDiM): wejscie to dokladnie ten format, ale **bez pgc** do zrownania; polozenie trzeba brac z GPS wiersza (Latitude/Longitude/GPS time) i pikietazu (patrz sekcje 12.5 i 12.6 - offset -4,8 m i `tsd_gps_data_qc`).
- Testy istniejace: `test_b1510off_v4.py` T1 parser, T2 klasyfikacja, T3-T4 wykrywanie zer / zrownanie ze znanym lagiem, T5 beyond_pgc, T7 zrownanie blokowe (skala), T8 roznicowa reszta zer.

## 11. backcal.py (574 l.) - nachylenia FWD z PCHIP, X_SIGNED (kalibracja wsteczna TSD)

- P025. Cel: kalibracja wsteczna zer TSD z FWD na mikroodcinkach (regresja `slope_TSD = c + k*slope_FWD`). **Przydatne dla N3 tylko: `X_SIGNED` i `fwd_slope_pchip`.**
- Stale: `X_SIGNED = {**AC.FRONT_X, 'm200':-0.200, 'm300':-0.300, 'm450':-0.450}` (1,51 m wlaczony); `SENSOR_ORDER`; `R_MM=(0,200,300,450,600,900,1200,1500,1800)`, `R_M`; `D_COLS=d1..d9`; `N_BOOT=1000`; `HUBER_DELTA=1.345`; `STABLE_CHANNELS`.
- **Funkcje:** `ols_fit(x,y) -> (c,k,r)`, `theilsen_fit`, `huber_fit(x,y,delta=1.345,n_iter=50,tol=1e-9)` (IRLS), `bootstrap_ols_ci(x,y,groups,n_boot=1000,seed=0)`, **`fwd_slope_pchip(dp, x)`** (`dp = PchipInterpolator(R_M, Dn).derivative()`; `v = dp(|x|)`; **znak: przod (x>0) `-v`, tyl (x<0) `+v`**), `fwd_slope_secant(secant_mid, Rm, x)`, `load_points`, `load_fwd(a)` (**`Dn = d*50/F`; mediana stacji przypisanych do punktu; wiersz tylko gdy WSZYSTKIE 9 ugiec skonczone**), `build_point_table`, `build_noc_czujnik`, `build_stabilnosc`, `build_zestawy`, `build_1510`, `analyze_1510_interaction`, wykresy, `main`.
- Pulapki: **`seed=hash((night, s, method)) % 2**31` - Python losuje hash stringow miedzy procesami (PYTHONHASHSEED) -> bootstrap NIEPOWTARZALNY**; `theilslopes` i `pearsonr` ze scipy; kalibracja zer - nie wchodzi do N3; mediana nachylenia w oknie (nie calki).
- Testy: `test_backcal.py` T1-T5.

## 11b. import_station_fwd.py (876 l.) + kontrola2_nachylenia.py (736 l.)

### 11b.1 import_station_fwd.py
- E1-0d: surowy import stacji FWD/HWD TN/Podkowa/LAMB z plikow `.mdb` (Dynatest) do `baza_stacje_v1.db`. Czytanie MDB przez `build_road_db.mdb_read_tables_safe(path,'Sessions','Stations','Drops','Histories')` (pyodbc, Access ODBC, Windows, podproces).
- Funkcje czyste: `default_station_code(filename)`, `rel_posix`, `is_dmi_flat(sm_values)`, `resolve_label(lane_raw, station_km, ab_distance_m, dmi_flat) -> (label, rule)` (|Station*1000| <= 3 -> A, |Station*1000 - AB| <= 5 -> B; AB: TN 25, Podkowa 30, LAMB 66 m), `assign_drop_seq(drop_list)` (sortuje po `DropID`, 1-indeksowane), `compute_visits(records)` (wizyta = kolejne pomiary stacji z przerwa <= 30 min; ostatni pomiar punktu `is_used=1`), `compute_gps_source`, `compute_station_points`, `load_corrections`, `load_expected`, `compare_with_expected`, `parse_mdb_file`, `build_records`, `create_schema`, `write_raw_import`, `main`.
- **Schemat MDB -> baza (przydatny dla N1):** `Stations`: `StationID, SessionID, Station [km], Lane, Time, Latitude, Longitude, Height, AsphaltTemperature, SurfaceTemperature, AirTemperature, PavementType, GPSStatus`; `Drops`: `DropID, StationID, SessionID, History (0 = dosadzenie is_seating=1, 1 = uderzenie z historia), Stress [kPa], Force [kN], D1..D9 [um]`; `Sessions`: `X1..X9` (polozenia geofonow, mm), `Trailer` (**'8002*' = FWD, '8082*' = HWD**), `Electronics`, `Program`. Widok `v_station_point_drop2` = DRUGI zrzut stacji (`drop_seq=2`) z `force_kn`, `d1..d9`, temperatury.
- Pulapki: wymaga pyodbc + sterownik Access (Windows 64-bit) - dla narzedzia N1 lepiej zostawic wejscie CSV/XLSX; `is_seating` = `History==0` (nie "pierwsze uderzenie" w sensie kolejnosci); `Station` w km, mnozone x1000; domyslna normalizacja do 50 kN dzieje sie PO imporcie (w e2a3_beta/e2b2_values).

### 11b.2 kontrola2_nachylenia.py
- Wpis 88, zadanie kontrolne 2: K1-K6 (mediany kanalow slope/deflvel/doppler w oknach +-5 m wokol punktow vs T10; nachylenia czaszy FWD vs T10; calkowanie nachylen trapezami `slope(0)=0`; dalekie kanaly vs temperatury; porownanie plikow `raw.sup.xls` vs `pgc.ibdim.xls` (107 par); tabela 1b dla kontroli recznej).
- Funkcje: `describe(T, V, rows_neg=None)` (Spearman, zmiana na C = (mediana gornego - dolnego tercyla V)/(roznica median T)), `load_db(conn)`, `windows(D, a, log_)` (okno `s_point +-5.0` na `s_ref`), `unit_night`, `passes_table`, `summary_rows`, `deflvel_consistency(D)` (sprawdza `deflvel [mm/s] ~ slope [um/m] * V[m/s] / 1000`), `fwd_rows(a)` (**nachylenia FWD sieczne `fs_i = (D_i - D_{i+1}) / ((x_{i+1}-x_i)/1000)` [um/m]**, `curv_16 = d1-d6`, `curv_18`, `curv_15`), `fwd_unit_night`, `scatter_grid`, `read_xls(path)` (xlrd; naglowek szukany po komorce zaczynajacej sie od 'Chainage'; zwraca `(hr, head, A)`), `norm(h)`, `col_of(head, pref)`, `best_lag(a, b, rng=60)`, `k5`, `k6`, `main`.
- Stale: `FRONT`, `REAR`, `DOPP` (11 kanalow Dopplera, 3,040 m...), `X_FRONT`, `X_REAR` (dodatnie), `FWD_X` [mm], `GOF_MIN=0.5`, `TSD_TO_FWD`.
- Dla pakietu: tylko `read_xls` (wejscie .xls IBDiM pgc/raw.sup) i `deflvel_consistency` (kontrola spojnosci slope/deflvel) maja wartosc; reszta to analiza jednorazowa.

---

## 12. Zaleznosci (skrypty dodatkowe, skrotowo)

### 12.1 e2a3_beta.py (E3) + e2a3i_final.py (E3F) - zrodlo `k_guide/beta_pct`
- `e2a3_visits` (848 wizyt): `D0..D1800` = `d_i*50/F` (DRUGI zrzut stacji, `drop_seq=2`; wiersz pomijany gdy jakikolwiek z 9 geofonow None), `sci300=D0-D300`, `bdi=D300-D600`, `bci=D600-D900`, `d0_d600`, `d0_d900`; temperatura: `t_mid_met` = temperatura w polowie warstwy interpolowana (czas liniowo, max luka `MAX_GAP_MIN=90` min; glebokosc `np.interp`) z czujnikow stacji MET: TN glebokosci (0,2,4,8,12,18,24,28,50) cm, `mid_depth=12.5`, grubosc 25 cm; Podkowa (0,2,4,8,12,18,23,28,50), `mid_depth=12.0`, 24 cm; pokrycie MET 2025-08-20..2026-08-20; `excl_frost = (miesiac==01)`; `has_met`.
- **`E3.fit_k_profile(T, D, groups, k_bounds=(0.0, 0.08)) -> (k_hat, a_p, ug, ok)`**: model `D_i = a_p / (1 + k*(20-T_i))`, `a_p` zamkniete WLS dla grupy, minimalizacja RSS(k) `minimize_scalar(bounded, xatol=1e-5)`; `K_BOUNDS_V2=(-0.08, 0.08)` w P040. **Nazwa `k_guide` w tabeli = DOPASOWANE k postaci liniowej (nie 0,02).**
- **`E3F.get_data(visits, indicator, scope, t_lo=5, t_hi=30) -> (T, y, pid, day, month)`**, `pm_key_of(pid, month)` (`'{pid}|{month}'`), `beta_with_ci(T, y, pm_key, day, n_boot, seed_tag, k_bounds, min_n=30)` (estymator referencyjny: QP z efektem stalym punkt x miesiac, `x=T-20`, bootstrap po dniach, 500 replik w P040), `run_k_profile`, `run_norm_test` (3 warianty: `i_k02`, `ii_beta_D0` - beta D0 na wszystkie geofony, `iii_beta_own`), `cv_groups(values, keys, min_n)`.
- `seed_for(*parts) = 1000 + crc32('|'.join(parts)) % 80000` (EE) - deterministyczny seed (bootstrap powtarzalny, w przeciwienstwie do backcal).
- Zaleznosc: `e2a3e_range.load_visits(conn, log_)` czyta `e2a3_visits` z `baza_analizy_e2a.db`.

### 12.2 e2aR2_rules_R4.py (R4 = k liniowe z k_guide scope=lacznie)
- `K_R4 = dict(D0=0.01611, D300=0.01234, D600=0.00703, D900=0.00329)` (zaokraglone z `e2a3_final_k_profile`); test pasm identyczny jak dla R1/R2/R3a; SCI300 liczone z ugiec skorygowanych regula R4 (`D0_20 - D300_20`, `run_band_fixed(..., param=0.0)`); porownanie z `R3a_z_ugiec`. Wynik: `tabele\e2aR2_rules_bands_R4.csv` (sekcja 14.2). **Uwaga:** K_R4 zaokraglone do 4-5 cyfr istotnych (np. 0,01611 vs 0,016109215).

### 12.3 w2_euler.py (stale kanalow B_1510off)
- `SLOPE_COL = {'1510':'Slope 1.510','0910':'Slope 0.910',...,'m200':'Slope -0.200','m300':'Slope -0.300','m450':'Slope -0.450'}`, `D_COLS = ['D-450','D-300','D-200','D0','D200','D300','D450','D600','D900','D1200','D1500']` (**BEZ D1800** mimo kolumny w pliku), `ALL10_SORTED = m450,m300,m200,0110..1510` (x rosnaco), `CHAN_X = {**AC.FRONT_X, **{k:-v for k,v in AC.REAR_X.items()}}`, `X_FAR_FRONT=3.040`, `BUFFER_HALF=5.0`, `GRID_STEP=0.05`. Funkcje pomocnicze importowane przez b1510off_v4_import: `strip_unit`, `profile_on_grid(x_known, y_known, grid, window_m, step)`, `interp_nan_outside`, `zscore`, `moving_mean(y, w)` (uniform_filter1d, mode='mirror').

### 12.4 e2b1_pairs.py (okna, geometria)
- `window_stats(s_sorted, tsd_id, lat, gof, center, radius)` (okno `s_ref in [center-radius, center+radius]`, searchsorted left/right = DOMKNIETE; zwraca `n, tsd_id_min, tsd_id_max, gof05_share (udzial GoF>=0.5), lat_median`), `nearest_row(s_sorted, s0)`, `layer_of(dlat, sigma_long)` (warstwy A/B/C/X par). **`gof05_share` = jedyne wbudowane "GoF >= 0,5 jako atrybut" w parowaniu** (+ w `e1_sref.tsd_bin_stats`: `gof05_n`, `gof05_share`, `d0_gof05_n`, `*_gof05_med`, `N_GOF_MIN=3`).

### 12.5 e1_sref.py (s_ref i pozycja)
- `TSD_OFFSET_M = -4.8` m (globalna korekta polozenia kanalow danych TSD, konwencja lagu E0-C: wiersz o pikietazu s dostaje GPS z pikietazu `s - lag`, tj. GPS z PRZODU o 4,8 m; niepewnosc +-1,5 m); korytarze EPSG:2180; wyrownanie przejsc profilem blokami 1 km (`ALIGN_BLOCK_M=1000`, `ALIGN_LMAX=15`, `ALIGN_R_MIN=0.8`, `ALIGN_OUTLIER_M=3.0`); `s_ref = s_ref_gps + delta(s)`; biny `bin_id = floor(s_ref / bin_m)` (domyslnie 10 m). `make_logger(path)`.
- **Dla N3: to jest konwencja "pikietazu" i "przesuniecia" - musi byc jawnie zdefiniowana w narzedziu.**

### 12.6 QC GPS-zyroskop i przesuniecie danych: `qc_gyro_gps.py`, `qc_profile_consistency.py`, `scan_tsd_gps_segments.py`
- `qc_gyro_gps.py`: `omega_from_gps(chain, lat, lon, speed, half=10)`, `xcorr_pearson(a, b)`, `signal_metrics(chain, lat, lon, speed, gyro, window=None)`, **`verdict(m, window, r_min, omega_std_min)`** -> `OK | PRZESUNIETY | NIEROZSTRZYGNIETY | BRAK_ZYROSKOPU`; konwencja przesuniecia: `lag = L`, dla ktorego `corr(gyro[i+L], omega_gps[i])` maksymalne (L<0: kurs GPS opoznia sie wzgledem zyroskopu); "sygnatura poprawna" wstepnie -5..-9 wierszy; stale `HALF=10`, `MIN_OVERLAP=2000`, `JUMP_TOL_M=0.5`, `OMEGA_ABS_MAX=1.0`, `SMALL_OVERLAP=0.2`; tabela `tsd_gps_data_qc`.
- `qc_profile_consistency.py` (zastepcza kontrola przez profil IRI, `R_MIN=0.5`, `LAG_OK_M=5`, `MAX_SHIFT_M=60`), `scan_tsd_gps_segments.py` (`MAX_DIST_M=10`, `MIN_RUN_ROWS=5`, `ZONE_MARGIN_M=50`, `SCAN_MARGIN_M=1500`, `S_CONSISTENCY_M=30`) -> `tsd_gps_bad_segments`.
- Flagi te sa implementowane jako skrypty obslugujace BAZE (zapisuja do tabel), nie jako funkcje wejscie->flaga; logike (`omega_from_gps`, `xcorr_pearson`, `verdict`) da sie wyciagnac.

### 12.7 Hampel + korekta beta=1,60 (szczegoly w sekcji 13)

---

## 13. Hampel na d0 i korekta d0 wykladnicza beta=1,60 - gdzie to jest (grep 'hampel', 'beta', '1.60')

**Nie ma jednego skryptu produkcyjnego N3.** Elementy:

### 13.1 Filtr Hampela - DWIE rozne implementacje
1. **`C:\WORK\...\tsd_2_xml\tsd_pipeline.py`** (zrodlo: projekt DK50/S8; identyczna kopia w `C:\WORK\DOKTORAT\tsd_2_xml\`): `WIN=21`, `HAMPEL_K=3.0`, `MINP=1`.
   - `_hampel_col(s)`: `med = s.rolling(21, center=True, min_periods=1).median()`; `mad = s.rolling(21, center=True, min_periods=1).apply(lambda w: nanmedian(|w - nanmedian(w)|))` (**MAD = prawdziwy MAD okna**); `thr = 3 * 1.4826 * mad`; zwraca `s.where(~((|s - med| > thr) & (thr > 0)))` (**wymaga thr>0**).
   - `smooth_bowl(d, offsets=OFFSETS_ALL, hampel=True)`: (1) tylko PELNE czasze (wszystkie 11 offsetow Tkor: -450,-300,-200,0,200,300,450,600,900,1200,1500 skonczone); (2) Hampel na D0 -> gdy D0 outlier, caly wiersz (cala czasza) = NaN; (3) srednia kroczaca `rolling(21, center=True, min_periods=1).mean()` kazdego offsetu na przetrwalych wierszach. Okno 21 WIERSZY na indeksie = +-10 m przy kroku 1 m.
   - W tsd_2_xml dane to `D ... Tkor` (temperaturowo skorygowane przez IBDiM wzorem `1 + k(20-T_XGB)`, k 0,011-0,028 zalezne od pliku; formula nieodtwarzalna - wpis 9 pliku wymiany).
2. **`bak\e2bR9_lustro_data.py`** (P071, Nov 2026): `HAMPEL_WIN_ROWS=21`, `HAMPEL_K=3.0*1.4826`; `_rolling_median_mad(x, win)` (pandas): `med = rolling(win, center=True, min_periods=1).median()`, **`mad = (s - med).abs().rolling(win, center=True, min_periods=1).median()` - czyli MAD liczony wzgledem MEDIANY KAZDEGO PUNKTU (a nie mediany tego samego okna) -> inne (przyblizone) MAD niz w tsd_pipeline**; `thr = k*mad`; `outlier = isfinite(v) & isfinite(thr) & (|v-med| > thr)` (**BEZ warunku thr>0**: przy oknie jednorodnym kazda niezerowa roznica jest outlierem); funkcje `hampel_univariate(vals, win=21, k=3*1.4826)` (Hampel na jednej serii, np. d0 B_1510off, potem `_rolling_mean` po przetrwalych) i `hampel_basin_nominal(series, win=21, k=3*1.4826)` (wymog pelnej czaszy dla offsetow `d0,d200,d300,d450,d600,d900` - 6, nie 11).
   - Uzywane w wariantach `X_b1510` / `X_nom` / `C_X` (e2bR9_lustro_warianty/kalibracja) - zadnych innych skryptow z "hampel" (grep: tylko e2bR9_*, plik wymiany, prompt P071).
3. **Decyzja projektowa (plik wymiany, wpis 2026-09-23 (7) C):** "w Etapie 2 go NIE stosujemy (decyzja Jacka: bez wygladzania i uśredniania)" - Hampel jest tylko w produkcie XML tsd_2_xml i w wariantach X lustra P071. Okna W1/W2,5/W5 (mediana, bez Hampela) to standard parowania.

### 13.2 Korekta d0 wykladnicza beta = 1,60 %/C
- `bak\z15_temp_correction.py` (P065, wpis 240): `BETA_D0_PCT = 1.6041459432458258` [CI 1,5132; 1,7267] z `e2a3_final_k_profile (lacznie, D0)`; `d20 = apply_rule(d_T, T12, 'exponential', BETA_D0)` identyczna beta dla D0 FWD i d0 TSD (zalozenie `delta_beta ~ 0`, wynik "|delta_beta| <~ 0,3 %/C"); temperatura **T12 z modelu Z15 (DOKTORAT) `Z15_temperatury_par.csv` (`fwd_t12_cal`, `tsd_t12_cal`)** - zewnetrzna zaleznosc od modelu temperatury warstwy 12 cm (BELLS3, T_XGB...). Warianty: BELLS3, operator swiezy, liniowy k=0,02, flagi kalibracji.
- `bak\e2bR9_lustro_data.py`: `BETA_D0_PCT=1.60415`, `BETA_D300_PCT=1.21602`, `LINEAR_K=0.02`; `correct_pair(fwd_val, tsd_val, fwd_t12, tsd_t12, treatment, beta_pct=BETA_D0_PCT)` -> `'none' | 'main_after' (exp, apply_rule z e2aR2_rules) | 'k02'`; NaN gdy brak T po ktorejs stronie.
- `bak\z15_curvature_correction.py` (P066): korekta wskaznikow krzywizny: FWD CB (kazdy geofon wlasnym beta: D0 1,604 / D300 1,216 / D600 0,707 / D900 0,334 %/C); TSD - A031/A0361/A6191 **wlasnym beta odpowiadajacego wskaznika FWD (OWN: SCI300 3,244 / BDI 2,870 / BCI 1,922 %/C)** przy `delta_beta=0` (CB niewykonalne dla TSD - "TSD nie ma wiarygodnego d300"); trzy poziomy usredniania: L1 para, **L2 przedzialy 100 m wzdluz `s_fwd` (`L2_BIN_M=100.0`, prog >=3 pary)**, L3 caly wspolny przebieg (>=5); `DELTA_BETA_PCT` (SCI300 -0,53, BDI -0,35, BCI +0,10 %/C).
- Agregacja 50 m: tylko w tsd_2_xml (`compare_sci_agg.py` - SCI w skalach 1 m / 50 m / 1 km, XML 10 m) i w `e1_sref` (biny 10 m); **agregacja 50/100 m siec TSD w bazie nie jest zaimplementowana jako funkcja**.
- Beta 1,60 dla d0 TSD w badaniach: `e2a4b_dbeta.py`, `e2aR7_dbeta_slopes*.py` (wnioski o `delta_beta` d0 ~ 0; plik wymiany 9977: "d0 stabilne we wszystkich wariantach -0,12..+0,05 %/C").

### 13.3 Okno +-5..10 m, GoF >= 0,5 atrybut, flagi QC
- Okno: `AC.window_medians(D, pass_id, s_point, half=5.0)` (mediana kanalow), `e2b1_pairs.window_stats` (+-1/2,5/5 m), Hampel okno 21 wierszy (+-10 m).
- GoF >= 0,5: `GOF_MIN=0.5` w `e2a_autc_1b` (informacyjnie), `e1_sref` (`gof05_*`), `e2b1_pairs.window_stats.gof05_share`; `e2b2_values` zapisuje `gof` = mediana okna; eksport B_1510off ma `GoodNess limit: 0.1500` w naglowku (nizsze GoF sa w pliku; filtracja po stronie uzytkownika - mediana GoF w e2b2_tsd_values: 0,177).
- Flagi QC: `measurement_flags` (datasets.exclusions: purposes noise/level/conversion/temperature), `tsd_gps_data_qc` (qc_gyro_gps), `tsd_gps_bad_segments` (scan_tsd_gps_segments), `tsd_profile_qc` (qc_profile_consistency), `b1510off_files.status/zero_set_mismatch`, `b1510off_alignment.align_fail`.

---

## 14. Tabele referencyjne (C:\projects\sql_tsd_fwd\tabele) - weryfikacja

### 14.1 e2a3_final_k_profile.csv - 36 wierszy (3 scope x 12 wskaznikow), UTF-8-sig, przecinek
Naglowek: `scope,indicator,beta_pct,beta_lo,beta_hi,k_guide,k_lo,k_hi,n,note`. Pochodzenie: `E3F.run_k_profile` (P040), `T_mid_met`, wizyty 5 <= T < 30 C, bez stycznia, efekt staly punkt x miesiac, 500 replik bootstrapu po dniach (CI), `n` = liczba wizyt (TN 191, PODKOWA 223, lacznie 414).
Pierwsze wiersze: `TN,D0,1.59047,1.4378,1.74341,0.0152048,0.0137238,0.0166226,191,` ; `TN,D200,1.45977,1.36871,1.58823,0.0141064,0.0133381,0.015099,191,`.

**WSZYSTKIE wiersze scope = `lacznie` (n = 414):**

| indicator | beta_pct [%/C] | beta_lo | beta_hi | k_guide | k_lo | k_hi | n |
|---|---|---|---|---|---|---|---|
| D0 | 1.60415 | 1.51323 | 1.72669 | 0.0161092 | 0.0152731 | 0.0173327 | 414 |
| D200 | 1.38103 | 1.25461 | 1.51033 | 0.0140162 | 0.0128732 | 0.0152014 | 414 |
| D300 | 1.21602 | 1.12022 | 1.37435 | 0.0123428 | 0.0113233 | 0.0138767 | 414 |
| D450 | 0.954185 | 0.851253 | 1.10514 | 0.00958895 | 0.00851219 | 0.0110354 | 414 |
| D600 | 0.70652 | 0.593622 | 0.884902 | 0.00702971 | 0.00588382 | 0.0087788 | 414 |
| D900 | 0.333874 | 0.223235 | 0.465406 | 0.00328817 | 0.00218109 | 0.00465979 | 414 |
| D1200 | 0.216493 | 0.130381 | 0.33268 | 0.00214063 | 0.0012807 | 0.00330877 | 414 |
| D1500 | 0.215758 | 0.156292 | 0.306327 | 0.00215554 | 0.00154917 | 0.00306097 | 414 |
| D1800 | 0.269251 | 0.205415 | 0.341394 | 0.00271306 | 0.00206866 | 0.00343276 | 414 |
| SCI300 | 3.24407 | 2.89378 | 3.63484 | 0.0301423 | 0.0270265 | 0.0337078 | 414 |
| BDI | 2.8704 | 2.67064 | 3.09901 | 0.0283985 | 0.026562 | 0.0305925 | 414 |
| BCI | 1.92233 | 1.72608 | 2.15002 | 0.0187039 | 0.0170104 | 0.0209908 | 414 |

**Sprawdzenie wartosci zadanych (zgodnosc z plikiem - TAK):**
- D0: k_guide **0,0161092** (plik 0.0161092; baza 0.016109215) / beta_pct **1,60415** (plik 1.60415; baza 1.6041459) - ZGODNE.
- D300: k_guide **0,0123428** / beta_pct **1,21602** - ZGODNE.
- D900: k_guide **0,00328817** / beta_pct **0,333874** - ZGODNE.
- Dodatkowo odtworzylem je NIEZALEZNIE z `e2a3_visits` (baza analiz, mode=ro) czystym numpy: beta_pct D0/D200/D300/D900/SCI300/BDI/BCI = 1,60415 / 1,38103 / 1,21602 / 0,33387 / 3,24407 / 2,87040 / 1,92233 (**zgodne z plikiem co do 5 cyfr**); k: D0 0,0161094, D300 0,0123426, D900 0,0032876, SCI300 0,0301413 (rozbieznosc <= 1e-6 - wynik mojej zlotej sekcji vs `minimize_scalar(xatol=1e-5)`; tolerancja testu na k: 3e-6 przy innym minimalizatorze, 1e-7 przy scipy). n=414 wizyt (T_mid w [5;30), bez stycznia, has_met).
- **Uwaga zakresu:** powyzsze k_guide i beta sa dopasowane na **5 <= T < 30 C** (obie postaci). Zalozenie z opisu N1 ("wariant A liniowy k_i 5-25 C, wariant B wykladniczy beta_i 5-30 C") NIE pokrywa sie z tabela: `e2a3_final_k_profile.csv` nie ma wspolczynnikow 5-25. Wspolczynniki 5-25 sa tylko w `e2aR4_coefs.csv` (wykladnicze, scope TN/PODKOWA/lacznie, D0/D300/D600/D900; lacznie D0 1,63984; D300 1,17339; D600 0,661777; D900 0,28078) i w e2aR4/e2a3f jako wyniki wewnetrzne (liniowe k 5-25 nie sa zapisane; moje przeliczenie dla D0 daje k=0,01753 przy 5-25 vs 0,01611 przy 5-30). Wartosci referencyjne k_i dla 5-25 C trzeba brac z raportu PW.S-1063 lub przeliczyc (`fit_params`).
- Jednostka: `beta_pct` w %/C (dzielic przez 100 przed `exp[beta*(20-T)]`); `k_guide` bezwymiarowe (1/C).

### 14.2 e2aR2_rules_bands_R4.csv - 160 wierszy, 16 kolumn
Naglowek: `scope,group_variant,indicator,rule,band,thaw_variant,n_all,n_with_ref,estimate,ci90_lo,ci90_hi,ci95_lo,ci95_hi,in_ref_band,delta,verdict`. **Wszystkie 160 wierszy: scope=`lacznie`, group_variant='', thaw_variant=`no_thaw`**; wskazniki: D0, D300, D900 (po 32 wiersze, rule `R4`), SCI300 (64 wiersze: `R4` i `R3a_z_ugiec`); 8 pasm x 4 delty (1,37; 2; 3; 5). Pierwszy wiersz: `lacznie,,D0,R4,0_5,no_thaw,28,0,nan,nan,nan,nan,nan,0,1.37,BRAK_DANYCH`. Werdykty: BRAK_DANYCH 80, ROWNOWAZNE 48, NIEROZSTRZYGNIETE 24, ROZNE 6, ROWNOWAZNE_ROZNE_OD_0 2. Estimate = sredni blad korekty [%] (`100*(lnD20 - ref)`), CI z bootstrapu po dniach. Skroty werdyktow: RW = ROWNOWAZNE, NR = NIEROZSTRZYGNIETE, RO = ROZNE, RW!0 = ROWNOWAZNE_ROZNE_OD_0, BD = BRAK_DANYCH (kolejnosc d = 1,37/2/3/5).

(tabela wygenerowana ze skryptu z pliku CSV; wartosci estimate nie zalezne od delty)

| wskaznik | regula | pasmo T | n_all | n_ref | estimate [%] | CI90 | CI95 | werdykt d=1,37/2/3/5 |
|---|---|---|---|---|---|---|---|---|
| D0 | R4 | 0_5 | 28 | 0 | nan | - | - | BD/BD/BD/BD |
| D0 | R4 | 5_10 | 56 | 0 | nan | - | - | BD/BD/BD/BD |
| D0 | R4 | 10_15 | 49 | 18 | nan | - | - | BD/BD/BD/BD |
| D0 | R4 | 15_20 | 110 | 108 | -0.224 | [-0.494; 0.095] | [-0.539; 0.140] | RW/RW/RW/RW |
| D0 | R4 | 20_25 | 110 | 110 | 0.220 | [-0.096; 0.491] | [-0.151; 0.539] | RW/RW/RW/RW |
| D0 | R4 | 25_30 | 49 | 49 | -1.064 | [-2.073; -0.047] | [-2.322; 0.125] | NR/NR/RW/RW |
| D0 | R4 | 30_35 | 25 | 25 | -3.762 | [-6.835; -1.198] | [-7.826; -0.744] | RO/RO/RO/RO |
| D0 | R4 | gt35 | 18 | 18 | nan | - | - | BD/BD/BD/BD |
| D300 | R4 | 15_20 | 110 | 108 | -0.089 | [-0.426; 0.218] | [-0.491; 0.273] | RW/RW/RW/RW |
| D300 | R4 | 20_25 | 110 | 110 | 0.087 | [-0.201; 0.430] | [-0.249; 0.485] | RW/RW/RW/RW |
| D300 | R4 | 25_30 | 49 | 49 | -0.231 | [-1.064; 0.496] | [-1.232; 0.670] | RW/RW/RW/RW |
| D300 | R4 | 30_35 | 25 | 25 | -1.358 | [-2.258; -0.390] | [-2.446; -0.245] | RO/RO/RW!0/RW!0 |
| D900 | R4 | 15_20 | 110 | 108 | 0.131 | [-0.182; 0.423] | [-0.229; 0.522] | RW/RW/RW/RW |
| D900 | R4 | 20_25 | 110 | 110 | -0.129 | [-0.398; 0.196] | [-0.471; 0.246] | RW/RW/RW/RW |
| D900 | R4 | 25_30 | 49 | 49 | 0.563 | [-0.245; 1.414] | [-0.417; 1.613] | NR/RW/RW/RW |
| D900 | R4 | 30_35 | 25 | 25 | 0.368 | [-1.027; 1.878] | [-1.295; 2.105] | NR/RW/RW/RW |
| SCI300 | R4 (z ugiec) | 15_20 | 110 | 108 | -0.683 | [-1.618; 0.399] | [-1.823; 0.583] | NR/RW/RW/RW |
| SCI300 | R4 (z ugiec) | 20_25 | 110 | 110 | 0.671 | [-0.418; 1.476] | [-0.658; 1.641] | NR/RW/RW/RW |
| SCI300 | R4 (z ugiec) | 25_30 | 49 | 49 | -6.021 | [-12.257; -0.369] | [-13.408; 0.375] | NR/NR/NR/NR |
| SCI300 | R4 (z ugiec) | 30_35 | 25 | 24 | -18.525 | [-45.415; 0.433] | [-53.038; 2.203] | NR/NR/NR/NR |
| SCI300 | R3a_z_ugiec | 15_20 | 110 | 108 | -0.639 | [-1.545; 0.375] | [-1.782; 0.560] | NR/RW/RW/RW |
| SCI300 | R3a_z_ugiec | 20_25 | 110 | 110 | 0.628 | [-0.402; 1.438] | [-0.593; 1.585] | NR/RW/RW/RW |
| SCI300 | R3a_z_ugiec | 25_30 | 49 | 49 | -4.130 | [-10.303; 1.425] | [-11.498; 2.606] | NR/NR/NR/NR |
| SCI300 | R3a_z_ugiec | 30_35 | 25 | 24 | -11.690 | [-34.935; 6.202] | [-41.004; 8.638] | NR/NR/NR/NR |

(Pasma 0_5, 5_10, 10_15 i gt35 maja estimate=nan i BRAK_DANYCH dla wszystkich wskaznikow - brak referencji 15-25 C w grupie punkt x miesiac. W tabeli D300/D900/SCI300 pominieto te wiersze dla zwartosci; sa w pliku.)
Wazne dla N1: **stacje nie pozwalaja zweryfikowac korekty ponizej ~15 C** (n_with_ref=0/18); wspolczynniki dla T<15 C pochodza z dopasowania (5-30), nie z testu.
Plik uzupelniajacy `e2aR2_rules_bands.csv` (3328 wierszy; scope TN/PODKOWA/lacznie, R1/R2/R3a): np. lacznie, D0, no_thaw, delta=2, pasmo 25_30: R1 -3,95655 (ROZNE), R2 +3,27835 (ROZNE), R3a -0,30588 (ROWNOWAZNE); 20_25: R1 -0,436849, R2 +1,2482, R3a +0,239473; 15_20: R1 +0,444939, R2 -1,27131, R3a -0,243907. Te wartosci sa tez twardo wpisane jako kontrola w `e2aR2_rules_R4.py` (`EXPECTED_BAND2530`: R1 -3,95655, R2 3,27835, R3a -0,30588).

### 14.3 e2b2_tsd_values.csv - 9201 wierszy, 60 kolumn (UTF-8-sig)
Naglowek: `pair_id` + dla reprezentacji `p`, `w1`, `w2_5`, `w5`: `d0_<r>, n_d0_<r>, gof_<r>, speed_<r>, d0_valid_<r>, a031_<r>, a0361_<r>, a6191_<r>, a061_<r>, a091_<r>, n_curv_<r>, temp_road_<r>, curv_valid_<r>` (13 kolumn x 4 = 52), oraz wariant falkowy `a031_w5_dn, a0361_w5_dn, a6191_w5_dn, a061_w5_dn, a091_w5_dn, n_curv_w5_dn, curv_w5_dn_valid` (7). Jednostki: d0, a*** [um], gof bezwym., speed [m/s], temp_road [C].
Przyklad (pair_id 5288): `d0_p=181, gof_p=0.616677, speed_p=20.1557, a031_p=23.663, a0361_p=37.9248, a6191_p=56.5792, a061_p=61.5878, a091_p=118.167, temp_road_p=40.4685; d0_w5=153 (n=8), a031_w5=28.7412, a0361_w5=38.1424, a6191_w5=37.9944, a061_w5=79.3549, a091_w5=112.049 (n_curv=10), temp_road_w5=40.4002; a031_w5_dn=28.3854, a0361_w5_dn=35.4718...`. Pair 5289: `d0_p=150`, `a031_p=31.989`, `a061_p=65.6594`. Pair 5287: ma tylko P (`d0_p=167`, `a031_p=-1.24447`; okna puste).
Statystyki (do testow regresji): `d0_p` 4725 wartosci (mediana 66,0); `d0_w5` 8676 (mediana 63,0; `d0_valid_w5=1` w 8141 wierszach); `a031_w5` 9059 (mediana 2,1458; min -38,36; max 239,8); `a0361_w5` mediana 4,2161; `a6191_w5` 4,613; `a061_w5` 6,2958; `a091_w5` 11,0002; `gof_w5` mediana 0,177; `a031_w5_dn` mediana 1,5574 (9036); `curv_valid_w5=1` w 9050 wierszach.
Uwaga: `a0361_w5` != `a061_w5 - a031_w5` (mediany calek) - rownosc w 49 z 9059 wierszy.
Powiazane: `e2b2_lambda.csv`: `d0,sigma_tsd=0.296408,median_diff_log=-0.0755076,sigma_fwd=0.101763,lambda=0.11787,n_pairs_tsd=2015,n_fwd_pairs=128,scale_m=10`; `a031` 0,0294772 (611 par), `a0361` 0,0346035, `a6191` 0,0270222, `a061` 0,0354317, `a091` 0,0377235.

### 14.4 e2a2_autc_var.csv - 1308 wierszy, 22 kolumn (punkt x noc, mikroodcinki 1a,1b,1c,2a,2b,3,4,5; 15 nocy)
Naglowek: `section_code,series_date,point_k,t10,t_a031,t_a061,t_a091,t_a0361,t_a6191,p0_a031,p0_a061,p0_a091,p0_a0361,p0_a6191,x_max,x_max_missing,px_a031,px_a061,px_a091,px_a0361,px_a6191,ar045`. Rozklad: odcinek 3: 300, 2a: 195, 1b: 178, 4: 163, 1a: 154, 5: 138, 1c: 90, 2b: 90. `x_max_missing=1` w 64 wierszach (x_max/px_*/ar045 puste).
Pierwsze wiersze: `1a,2025-09-04,0,25.5,22.6437,39.7148,43.7941,17.0711,4.07923,21.6023,39.0758,41.5524,17.4735,2.47669,0.0398413,0,22.1996,39.6731,42.1498,17.4735,2.47669,43.4581`; `1a,2025-09-04,1,25.5,23.4522,52.86,70.0658,29.4078,17.2058,26.998,57.0239,74.2292,30.0259,17.2053,-0.0384173,0,27.8631,57.889,75.0943,30.0259,17.2053,49.6239`.
Mediany: `t_a031` 35,69; `t_a061` 66,13; `t_a091` 85,64; `p0_a031` 39,51; `p0_a061` 70,28; `p0_a091` 92,29; `px_a031` 44,01 (n=1244); `x_max` -0,034 m (mediana); `ar045` 68,07.
Tozsamosci do testow: `t_a0361 = t_a061 - t_a031`, `t_a6191 = t_a091 - t_a061`, `p0_a0361 = p0_a061 - p0_a031` (pasuja w tym wierszu: 39,0758-21,6023 = 17,4735; 39,7148-22,6437 = 17,0711), `px_a0361 = p0_a0361` i `px_a6191 = p0_a6191` (to calki 0,31-0,61 i 0,61-0,91 m, niezalezne od dolnej granicy calkowania).

### 14.5 Pozostale pliki referencyjne (nazwy; do ew. wykorzystania w testach)
`autc_1b_punkty/noce/trendy.csv`, `backcal_*.csv`, `b1510off_v2_{files,zero_check,alignment,align_blocks,qc}.csv`, `e2aR4_{indices_bands,indices_norm,coefs}.csv`, `e2a3_final_norm_test.csv` (np. lacznie D0: `i_k02` CV miesiac 0,0303553, trend resztkowy -0,691303; `iii_beta_own` 0,0259466 / -0,00100344, n=414), `e2b2_{pairs,fwd_values,null_values,agreement,temp_corr,lambda}.csv`, `z15_korekta_TSD_FWD_*.csv`, `z15_krzywizna_TSD_FWD_*.csv`, `e2bR9_lustro_*.csv`, `z15_pary_wejscia.csv` (5511 par sieciowych).

---

## Wnioski dla projektu

### A. Proponowany podzial na moduly pakietu `tsdfwd_tools`

```
tsdfwd_tools/
  common/
    constants.py     T_REF=20.0; CHANNELS_9 / X_POS (znak!) / FRONT_X; D_OFFSETS_MM; FWD_STANDARD_LAYOUT; GOF_MIN=0.5; INTSTEP=0.001
    coefficients.py  pakietowy CSV z e2a3_final_k_profile.csv (12 wskaznikow x 3 scope, z CI, n, zakresem dopasowania 5-30 C, T=T_mid) + loader + walidacja schematu
    io_utils.py      czytanie CSV (utf-8-sig, ; vs ,), nmed, NaN-bezpieczne mediany; BEZ write_csv/insert do baz
  rules.py           apply_rule (enum: LINEAR/EXPONENTIAL, bez cichego fallbacku), factor(T, form, param), walidacja T (5-25/5-30 jako OSTRZEZENIE), z e2aR2_rules.apply_rule + e2aR4.apply_f + l20_error.f_t
  fwd/
    io.py            wczytanie FWD z CSV/XLSX (kolumny Force, D1..D9, X1..X9, Time, AsphaltTemperature); opcjonalnie MDB (pyodbc) - wzor: import_station_fwd/build_road_db
    normalize.py     normalizacja do 50 kN (D*50/F), wybor zrzutu (is_seating=History==0; 2. zrzut vs srednia nieosiadczych - parametr), dopasowanie geofonow (match_geophone_indices, is_standard_layout) z e2b2_values
    indices.py       SCI300, BDI, BCI, D0-D600, D0-D900 z ugiec (po korekcie geofon po geofonie - build_index20 z e2aR4)
    tempcorr.py      N1: wariant A (liniowy k_i), wariant B (wykladniczy beta_i), 20 C; wejscie temperatury (kolumna uzytkownika), flaga temp_entry/carried z e0_fwd_temp.classify_session; wyjscie: D20_i + SCI/BDI/BCI z ugiec skorygowanych
    fit.py           (opcjonalne) qp_fit_nd / fit_k_profile (e2a2b/e2a3_beta) - tylko gdy narzedzie ma wyznaczac wlasne k/beta; wymaga scipy
  tsd/
    io.py            parser raw.sup.txt (z b1510off_v4_import.parse_raw_sup_txt: "Headers:/Parameters:/Data:", separator ", ", strip_unit, znak D, kodowanie) + pgc xls (kontrola2.read_xls)
    zero_sets.py     apply_variant (z e2a_autc_1b), load_coefficients (CSV ;); tylko jesli wejscie nie jest juz B_1510off
    integrals.py     dense_integral, p0_integrals (a031, a0361, a6191, a061, a091 z 9 kanalow, PCHIP, 1 mm) z e2a2b_beta + e2b2_values.row_curv_integrals; autc_front (T) jako wariant kontrolny
    filters.py       Hampel (JEDNA, jawnie zdefiniowana: window=21 wierszy, k=3*1.4826, MAD okna, thr>0, odrzut calej czaszy), rolling mean; parametry z tsd_2_xml.tsd_pipeline (NIE z e2bR9)
    window.py        mediany w oknie +-5..10 m po wspolrzednej korytarza; GoF>=0.5 jako atrybut (gof05_share, n_gof05), n_valid >= 3 (MIN_WINDOW_N)
    aggregate.py     agregacja 50 / 100 m (mediana/srednia wazona, prog n); bin = floor(s/step) po wspolrzednej korytarza
    tempcorr.py      N3: korekta d0 beta=1,60 %/C (BETA_D0_PCT=1.60415 z coefficients) wykladnicza do 20 C
    qc.py            flagi: GPS-zyroskop (omega_from_gps, xcorr_pearson, verdict z qc_gyro_gps), przesuniecie kanalow (lag, konwencja jak w e1_sref/qc_gyro_gps), flaga zlych segmentow GPS (scan_tsd_gps_segments - uproszczone)
  cli/ fwd_tempcorr.py, tsd_network.py
tests/ (patrz C)
```

Co skad przeniesc (konkretnie):
- `e2aR2_rules.apply_rule`, `e2aR4.apply_f`, `build_index20` -> `rules.py` / `fwd/indices.py`.
- `e2a3_final_k_profile.csv` -> `common/coefficients.py` (dane pakietowe; zaznaczyc "k i beta dopasowane 5<=T<30 C na T_mid MET; wzor na D(20) = D(T)*[1+k(20-T)] lub *exp[beta(20-T)]").
- `e2a2b_beta.dense_integral` + `CHANNELS_9`, `XS_SORTED`, `INTSTEP`, `e2b2_values.row_curv_integrals` -> `tsd/integrals.py`.
- `b1510off_v4_import.parse_raw_sup_txt` (+ `strip_unit`, `classify_file`) -> `tsd/io.py`; zrownanie blokami (`align_*`) NIE przenosic - dotyczy laczenia z pgc (specyfika bazy projektu).
- `e2b2_values.match_geophone_indices`, `is_standard_layout`, `mad_robust_sd` -> `fwd/normalize.py`, `common`.
- Hampel: z `tsd_pipeline._hampel_col`/`smooth_bowl` (z poprawka: vectorized MAD okna), nie z `e2bR9`.
- `e0_fwd_temp.classify_session` -> `fwd/io.py` jako flaga jakosci temperatury operatora (opcjonalnie).
- `qc_gyro_gps.omega_from_gps / xcorr_pearson / verdict` -> `tsd/qc.py`.

### B. Co jest zbyt "badawcze" i wymaga przeredagowania

1. **Wszystko zwiazane z baza projektu:** `datasets.py` (widoki v_all_*, ATTACH), `paths.py` (release_guard, `--allow-release-write` zdejmowane z sys.argv przy imporcie), `md5_r2`, kopie `_pre_pNNN.db`, `paths.release_guard`, `insert/write_csv` do baz, `e0_runs`, `catalog` - pakiet ma pracowac na plikach wejsciowych (CSV/TXT/XLS), bez baz i bez wydan.
2. **Bootstrap, CI, werdykty rownowaznosci, pasma temperatury, trendy wewnatrzdobowe, thaw/no_thaw** (e2aR2_rules, e2a3f_range, e2aR4_indices, e2x_*): cele publikacyjne. W N1 wystarczy opcjonalna "diagnostyka l20_error" dla uzytkownika.
3. **Globalny `OUT = {}` + `log()` piszacy do pliku, `sys.path.insert`, `sys.exit(2)`/`SystemExit` jako kontrola poprawnosci, kontrole "STOP" z twardo wpisanymi liczbami (`LAMBDA_D0_CONTROL=0.118`, `EXPECTED_BAND2530`)** - zamienic na `logging`, wyjatki typowane, testy.
4. **Niespojnosci konwencji do ujednolicenia:** granice zakresu dopasowania (`<=25` vs `<25`, `<30`); pozycje kanalow (`REAR_X` modul vs `X_POS`/`X_SIGNED` znak); okno +-5 m domkniete (sort/searchsorted); wartosc FWD stacji: 2. zrzut vs srednia nieosiadczych; `T` (T_mid MET 12,5/12 cm vs T10 mikroodcinkow vs T12 modelu Z15 vs asphalt_temp operatora) - **N1/N3 musza jawnie definiowac, jaka temperatura wchodzi do wzoru**.
5. **`apply_rule`: ciche fallback na exp.** `apply_variant`: `KeyError` dla zestawu spoza A/B/C; `zestaw_pliku` oparte o daty nocy (mikro).
6. **Hampel: dwie rozne definicje** (MAD okna i warunek thr>0 vs przyblizony MAD i brak warunku); `smooth_bowl` zeruje cala czasze wg D0 - decyzja projektowa wymaga potwierdzenia (czy N3 filtruje tylko d0, czy cala czasze/9 kanalow nachylen).
7. **Nieodtwarzalnosc:** `backcal.bootstrap` uzywa `hash(...)` (losowy miedzy procesami); `e2b2_values.K_D0` martwa stala; `e2aR4_coefs.n` = liczba replik; D z B_1510off jako calkowite um (kwantyzacja przy SCI/BDI).
8. **Zaleznosc od modelu temperatury warstwy z DOKTORAT** (`Z15_temperatury_par.csv`, T12_cal; BELLS3/T_XGB): w repo nie ma implementacji modelu temperatury TSD w postaci biblioteki - N3 musi albo dostac T jako kolumne wejsciowa, albo zaimplementowac model (to jest decyzja zakresu).
9. **N3: brak gotowej implementacji** agregacji 50/100 m, filtra Hampela na d0 w produkcie, flag QC jako funkcji wejscie->wyjscie - trzeba napisac nowe moduly na bazie fragmentow (sekcja 13).

### C. Testy regresji z wartosciami referencyjnymi - co jest wykonalne

Z istniejacych plikow `test_*.py` mozna przeniesc logike syntetyczna; oprocz tego nowe testy na liczbach z tabel (dane referencyjne w repo, bez dostepu do baz):

1. **Wspolczynniki (N1):** test, ze `coefficients` zwraca z pliku wartosci dokladnie jak w `e2a3_final_k_profile.csv`: D0 `k=0.0161092`, `beta=1.60415 %/C`; D300 `0.0123428`/`1.21602`; D900 `0.00328817`/`0.333874`; SCI300 beta 3.24407; BDI 2.8704; BCI 1.92233 (tolerancja 1e-6 / 1e-5).
2. **Formula korekty:** analityczne testy `apply_rule`: `exp`: `D_T=100`, `T=10`, beta=0,0160415 -> `100*exp(0.0160415*10) = 117.4...`; `guideline` k=0,02, T=15 -> `100*(1+0.02*5)=110`; identycznosc przy T=20; odwracalnosc (D_T -> D20 -> D_T); `fwd_tempcorr` SCI300 = `D0_20 - D300_20` (korekta geofon po geofonie) vs `D0_20 - D300_20` recznie (zgodne z `build_index20`); normalizacja `D*50/F`.
3. **Odtworzenie estymatorow (wymaga fixture `e2a3_visits`, 848 wierszy, wyeksportowany z bazy do CSV):** `qp_fit_nd` na `D0` (lacznie, 5<=T<30, 414 wizyt) -> `beta_pct = 1.60415 +- 5e-5`; `fit_k_profile` -> `k = 0.0161092 +- 3e-6`; ten test mozna wykonac numpy-only (zweryfikowane powyzej). Warunkowo test CI bootstrapu (500 replik, seed `seed_for('kprof:lacznie:D0','boot')`): `[1.51323; 1.72669]` - tylko przy tej samej wersji numpy (`default_rng` PCG64).
4. **Test bledu korekty (opcjonalny):** `l20_error` + `band_mean` na `e2a3_visits` reprodukuja `e2aR2_rules_bands.csv`/`..._R4.csv`: np. lacznie, D0, R4, pasmo 20_25: `+0.220 %`, 15_20: `-0.224 %`, 25_30: `-1.064 %`, 30_35: `-3.762 %` (n_with_ref 110/108/49/25); R1 D0 25_30 `-3.95655`, R2 `+3.27835`, R3a `-0.30588` (jako testy bez CI, bez bootstrapu - deterministyczne).
5. **Calki P0 (N3):** (a) analityczne z `test_e2a2b.test_t2` (profil liniowy `a*(x-x0)`: `P0(x1) = a*(x1^2/2 - x0*x1)`, tol. 1%+0,05), (b) wiersz referencyjny: z `e2a2_autc_var.csv` (1a, 2025-09-04, punkt 0): `p0_a031=21.6023, p0_a061=39.0758, p0_a091=41.5524, p0_a0361=17.4735, p0_a6191=2.47669, t_a031=22.6437, t_a061=39.7148` - wymaga nachylen 9 kanalow z `e2a2_slopes.csv` (jest w tabelach; kolumny `slope_m450..slope_0910`) - czysty test numeryczny `dense_integral` + `autc_front` (tol. 1e-3 um), (c) tozsamosci `a0361 = a061 - a031` dla P0 i T, (d) NaN gdy jakikolwiek kanal NaN, (e) niezmienniczosc na stale przesuniecie zer (`apply_variant`, `test_autc.test_t3`).
6. **Medianowanie w oknie (N3):** wiersz z `e2b2_tsd_values.csv` (pair 5288, W5): `d0_w5 = 153` (mediana 8 wierszy), `a031_w5=28.7412` jako MEDIANA calek - potrzebny fixture wierszy B_1510off/PGC pary (z bazy `b1510off_measurements`; wydobyc raz do pliku testowego). Alternatywnie test syntetyczny: mediana calek != calka z mediany (kontra-test regresyjny).
7. **Hampel:** synteza (ciag stały + pojedynczy outlier + okno 21) -> outlier usuniety; zgodnosc z `tsd_pipeline._hampel_col` na wektorze referencyjnym (pandas); test, ze implementacja pakietu NIE flaguje przy `thr==0`.
8. **Parser raw.sup.txt:** `test_b1510off_v4.test_t1_parser` (znak D, liczba kolumn 86, `strip_unit`, wiersze 1 m: plik T4202008060001 ma ok. 6104 wiersze danych, pierwszy `Chainage=0.00, D0=-8342, D300=-7695, Slope 0.110=1453.5559, GoF=0.23790418, Lat 50.091676027, Lon 19.813605221`).
9. **Lambda / agregacja:** `e2b2_lambda.csv` d0 (`lambda=0.11787`, sigma_tsd=0.296408, sigma_fwd=0.101763) - tylko jako test `mad_robust_sd` na syntetycznych parach (znana sigma -> `1.4826*MAD/sqrt(2)`), bez baz.
10. **Przejscia ktorych NIE da sie wykonac bez dostepu do baz:** reprodukcja `e2b2_tsd_values` w calosci, zrownanie blokowe b1510off (wymaga pgc), QC GPS-zyroskop na pelnych plikach - uzyc 1-2 plikow testowych jako fixture (zewnetrzny katalog, MD5 w tescie).

### D. Ryzyka / decyzje do podjecia przed implementacja
- Jedna konwencja temperatury i zakresu dopasowania (5-25 vs 5-30; `<` vs `<=`) i ustalenie, czy wspolczynniki k_i (A) maja byc 5-25 (wtedy trzeba je przeliczyc, nie ma ich w tabeli) czy z tabeli P040 (5-30).
- Ktora definicja wartosci FWD stacji (2. zrzut vs srednia nieosiadczych) i czy uwzgledniac flage `temp_entry`.
- Hampel: ktora wersja, na jakich kanalach.
- Pikietaz: wspolrzedna korytarza vs chainage pliku; offset -4,8 m (+-1,5 m) i konwencja lagu; GPS w B_1510off jest w pliku (Latitude/Longitude), ale obecny importer go pomija.
- scipy jako zaleznosc (lub reimplementacja numpy: bisekcja QP + zlota sekcja k, jak w verify_k.py - gotowe, 40 linii).
