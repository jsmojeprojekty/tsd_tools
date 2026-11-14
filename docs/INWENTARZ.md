# INWENTARZ zrodel dla narzedzi N1-N4 (etap E0)

Data: 2026-11-13. Stan: E0 (inwentarz i projekt, bez kodu produkcyjnego).
Metoda: odczyt zrodel (tylko do odczytu; bazy SQLite wylacznie `file:...?mode=ro`) przez szesc przebiegow audytowych,
zakres: dokumentacja bazy, skrypty N1/N3, skrypty N4, raport PW.S-1063 v1.12, `temp_model`, `tsd_2_xml`.
Pelne notatki robocze (sygnatury, wzory, cytaty wierszy tabel): `docs\notatki_E0\E0_A..F_*.md` — odsylam do nich jako [A], [B], [C], [D], [E], [F].
Oznaczenia pulapek: `P-N1-xx` = wpis/wniosek w bazie ([A] sekcja 3), `S-xx` = pulapka znaleziona w kodzie.
Zasady zrodlowe, ktore obowiazuja w calym inwentarzu: korekta temperaturowa najpierw na kazdym czujniku/kanale, wskazniki krzywizny
wylacznie z ugiec skorygowanych; parowanie TSD-FWD wylacznie geometryczne; BELLS3_BT i BELLS3_O wylaczone; eksport nominalny TSD
(z czujnikiem 1,51 m) tylko jako wejscie kontrolne.

---------------------------------------------------------------------------------------------------

## 0. Zasoby wspolne

### 0.1 Srodowisko (stan zastany)
- Systemowy Python: miniconda 3.13 (numpy 2.4.2, pandas 3.0.1, xlrd 2.0.2; BRAK scipy, openpyxl, matplotlib), Python 3.14 x2 (bez numpy).
  Skrypty zrodlowe wymagaja scipy (brentq, minimize_scalar, PchipInterpolator, pearsonr/spearmanr/theilslopes), numpy >= 2.0 (`np.trapezoid`).
  Pakiet musi jawnie zadeklarowac zaleznosci: numpy>=2, pandas, scipy, pyyaml, xlrd, openpyxl, requests (tylko N2), pyodbc (opcjonalnie, MDB).
- Srodowisko docelowe: `C:\ENV\narzedzia_tsd_fwd` (conda, python 3.11) — do utworzenia w E1. Istniejace: `ROW_defects_iter1, autoresearch, doktorat, pkgs, py-base, sqltsdfwd` (nie ruszac).

### 0.2 Formaty plikow wejsciowych ([A] sekcja 2, [F] sekcja 3)
| Format | Co zawiera | Pulapki |
|---|---|---|
| TSD `T*.pgc.ibdim.xls` (10 m) i `_1m.xls` (1 m) | pgc IBDiM: Chainage, GPS, DateTime, IRI, Dr.Speed, Strain Gauge, Temp Road/Air, 10 x `Slope x.xxx [um/m]`, D* producenta | naglowek danych w wierszu 0-based 60 (1 m) lub 61 (10 m); nazwy slope z kropka (1 m) / przecinkiem (10 m); `.xls` ucina przejazdy na ~65 478 wierszach (S-N3-04) |
| TSD eksport `B_1510off` (`*.raw.sup.txt`) | 86 kolumn: d0, nachylenia 10 kanalow (z 1,51 m, ale 1,51 wylaczony w obliczeniach), GoF, predkosc, temperatury, GPS (Lat/Lon w pliku); naglowek `Headers:/Parameters:/Data:`, separator ", " | D ujemne i calkowite [um] (kwantyzacja); GoodNess limit 0,15 w naglowku; D300..D1500 producenta bezuzyteczne (P-N3-05); importer bazy pomija GPS (nie w pakiecie) |
| FWD Dynatest `.mdb` | sesje, stacje, zrzuty, historie czasowe | czytac TYLKO przez pyodbc/ODBC ReadOnly=1; `access_parser` przesuwa pola tekstowe; limit ~32 zadan JET |
| FWD eksport `Drops*.xlsx` (arkusz `Drops`) + `stations*.xlsx` (arkusz `Stations`) | zrzuty (Force kN, Stress kPa, D1..D9, Asphalt) i stacje (Asphalt/AsphaltTemperature, Surface, Air, GPS) | pierwsza stacja ma w `Drops.Asphalt` sentinel -3,4028e38; 2 zrzuty na stacje (uzywany 2.); temperatura asfaltu stala dla odcinka (18/18/20 C) |
| CSV zrodlowe projektu bazy | `z15_pary_wejscia.csv` (5511 par), `e2b2_*.csv`, `e2a3_final_k_profile.csv` | BOM UTF-8 (`utf-8-sig`), separator `,` (poza `tsd_wspolczynniki.csv`: `;`) |

### 0.3 Dane referencyjne w bazie (do odczytu; sciezki w konfiguracji, nie kopiowane)
- `C:\projects\sql_tsd_fwd\tabele\` (268 plikow CSV; BOM) — wyniki referencyjne; male wycinki testowe kopiujemy do `tests\data\` z opisem pochodzenia.
- Bazy w `C:\projects\sql_tsd_fwd\bazy\`: `baza_odcinki_v4.db` (13,65 GB; tsd_measurements, fwd_*, tsd_fwd_sections 445, `tsd_fwd_section_review` 167 `confirmed`, `v_stage2_sections` 167),
  `baza_produkty_v1.db` (tsd_sref, fwd_sref, ref_corridor_points, tsd_position_offset = -4,8 m +-1,5), `baza_analizy_e2a.db` (e2a3_visits 848 wizyt), `baza_analizy_e2b.db` (golden_pair_candidates, e2b2_*),
  `baza_odcinki_b1510off_v2.db`. Dostep: tylko `mode=ro`.
- Dane spoza projektu bazy: `C:\WORK\DOKTORAT\wymiana\wyniki\z15\Z15_temperatury_par.csv` (T12 obu stron, wynik modelu temperatury) — wejscie testowe N4.

### 0.4 Wartosci referencyjne — stan weryfikacji w E0 (wszystkie odczytem)
| Wartosc zadana w prompcie | Wynik weryfikacji | Status |
|---|---|---|
| N1: D0 k 0,0161092 / beta 1,60415; D300 0,0123428 / 1,21602; D900 0,00328817 / 0,333874 | zgodne z `e2a3_final_k_profile.csv` scope `lacznie`; odtworzone niezaleznie z `e2a3_visits` (n=414) czystym numpy: beta do 5 cyfr, k do 1e-6 | OK |
| N1: pasma R4 D0 25-30 C = -1,06 % | -1,064 (CI90 [-2,073; -0,047], n_with_ref 49); 15-20: -0,224; 20-25: +0,220; 30-35: -3,762 | OK |
| N4: W5 main_after mediana 1,6158; 5511 par; 36 sesji | `z15_korekta_TSD_FWD_main.csv`: 1,61584 [1,5382; 1,68335]; przeliczone niezaleznie z `z15_pary_wejscia.csv` + T12: 1,615841 (do 1e-6) | OK |
| N4: r w obrebie sesji W5 0,403 | `e2bR9_lustro_warianty.csv`: 0,403905 | OK |
| N4: pary zerowe 0,155 / 0,135 / 0,096 | zgodne z `e2bR9_lustro_warianty.csv` (`null_shift_minus200` / `plus200` / `permutation`), ALE niezalezne przeliczenie z `e2b2_null_values.csv` daje 0,114 / 0,134 / 0,027 (zgodne z `e2b2b_null_test_paired.csv`: 0,118 / 0,141 / 0,023) | ROZBIEZNOSC -> STOP-pytanie Q-N4-1 |
| N4: 167 zatwierdzonych odcinkow | `tsd_fwd_section_review` 167 `confirmed`, `v_stage2_sections` 167 (87 same/same + 80 same/adjacent); sekcji w v4: 445 | OK |
| N3: d0 W5 i calki P0 zgodne z `e2b2_tsd_values.csv` (1e-6) | plik 9201 wierszy x 60 kolumn; test wymaga fixture wierszy B_1510off danych par (do wyciagniecia z bazy raz, do `tests\data`) | wykonalne, fixture do przygotowania |
| N3: calki T/P0/PX zgodne z `e2a2_autc_var.csv` | plik 1308 wierszy; test czysto numeryczny z `e2a2_slopes.csv` (9 kanalow); wiersz kontrolny: 1a, 2025-09-04, pt 0: p0_a031 21,6023, p0_a061 39,0758, t_a031 22,6437 | wykonalne |
| N2: RMSE 1,75 [1,62; 1,87], MAE 1,40, bias +0,27, 549 obs., 226 sesji | plik: `C:\WORK\DOKTORAT\temp_model\output\z14lite\z14d\E3-T46_z14d_H_v2.csv`, wiersz "fizyka TN, kalibracja jednorazowa (IR_masa)": rmse 1,74865, mae 1,40387, bias +0,26525, CI [1,6193; 1,8689]; niezalezna replika (numpy/pandas/scipy ~100 linii) daje 1,7488 / 1,4042 / +0,2649 | OK; uwaga merytoryczna P-N2-13 |

---------------------------------------------------------------------------------------------------

## 1. N1 fwd_tempcorr — korekta temperaturowa ugiec FWD

### 1.1 Kroki, zrodla, wejscia

| # | Krok | Zrodlo (skrypt:funkcja) | Wejscie (kolumny/jednostki) | Zaleznosci | Uwagi / pulapki |
|---|---|---|---|---|---|
| 1 | Wczytanie FWD | `import_station_fwd.py`, `build_road_db.py`, `e2b2_values.match_geophone_indices/is_standard_layout` ([B] 11b, [C]); wzorzec XLSX: `tsd_2_xml` Drops/stations ([F] 3.5) | Force [kN], D1..D9 [um], X1..X9 [mm], Time, temperatury; geofony mapowac po `x1..x9` sesji | xlrd, openpyxl, pyodbc (MDB) | D9 = 1800 mm nie ma odpowiednika w TSD; P-N1-13, P-N1-18 (czas lokalny Europe/Warsaw z DST, GPS 2026 niewazny w 11,5 % pomiarow) |
| 2 | Wybor zrzutu | `e2b2_values` (siec: srednia zrzutow nieosadczych), `v_station_point_drop2` (stanowiska: 2. zrzut) | `is_seating`, `force_kn > 0` | — | Regula RÓŻNA miedzy zbiorami; decyzja nieostateczna (Q-N1-3) |
| 3 | Normalizacja do 50 kN | `e2a_autc_1b.load_fwd`, `e2b2_values`: `D * 50 / F` | D [um], F [kN] | — | Tylko zrzuty nieosadcze |
| 4 | Temperatura wejsciowa + flagi jakosci | `e0_fwd_temp.classify_session(st, gap_factor=3.0, gap_min_s=150, gap_q=0.90, min_regular=5)`, `placeholder_runs(st,key,values=(20.4,),tol=1e-3,near=3)`, `trust_rules(...)` ([B] 3) | asphalt_temp (wpis operatora), surface/air (czujnik) | — | Statusy: `entry_first`, `entry_change`, `entry_possible`, `carried`, `missing`. Wartosci zastepcze: 20,4 C (powietrze 8002-369; asfalt s258), 18/20 C stale DK50/S8, -3,4e38 (Drops xlsx). Tylko ~1,1 % stacji ma swiezy wpis (P-N1-05) |
| 5 | Wspolczynniki | `tabele\e2a3_final_k_profile.csv` (scope `lacznie`; 12 wskaznikow: D0..D1800, SCI300, BDI, BCI); zrodlo wyznaczenia: `e2a3_beta.py`, `e2a3i_final.py` (P040) ([B] 14.1) | k_guide [1/C], beta_pct [%/C], CI, n=414 | — | Dopasowanie 5 <= T < 30 C, T_mid z czujnikow MET, punkt x miesiac, log-link (quasi-Poisson). **Raport Tab. 7.1 = wartosci zaokraglone** (D450 0,0096->0,010 (+4 %), D900 0,00329->0,003 (-9 %), D300 0,01234->0,012). Wspolczynnikow 5-25 C w tabeli NIE MA (tylko `e2aR4_coefs.csv`: exp, D0/D300/D600/D900) — Q-N1-1 |
| 6 | Korekta | `e2aR2_rules.apply_rule(y, T, form, param)`: `guideline` -> `y*(1+param*(20-T))`, kazde inne `form` -> `y*exp(param*(20-T))`; `e2aR4_indices.apply_f` | D [um], T [C], param (k lub beta/100) | numpy | **S-N1-1: ciche przejscie na postac wykladnicza dla kazdego `form != 'guideline'`** — w pakiecie enum + wyjatek. T_ref = 20.0 wpisane literalnie. Konwencja: D20 = D_T * f(T), beta > 0 = wzrost ugiecia z temperatura |
| 7 | Wskazniki z ugiec skorygowanych | `e2aR4_indices.build_index20(T, geo, param, form)`: SCI300 = D0_20 - D300_20, BDI = D300_20 - D600_20, BCI = D600_20 - D900_20 | skorygowane D0, D300, D600, D900 | — | Wymaga wszystkich 4 geofonow > 0. Wskaznik moze byc <= 0 (2/515 w exp, 7/515 w lin; wszystkie > 30 C) -> nie logarytmowac. Zasada: nigdy wlasny wspolczynnik wskaznika (OWN: SCI300 3,244; BDI 2,870; BCI 1,922 %/C — tylko kontrolnie) |
| 8 | Zakres i flagi | raport 7.1, R5.4; `e2a3f_range.fit_params/l20_error` (diagnostyka) | T_mid | — | A: 5-25 C, B: 5-30 C; < 5 C brak zastosowania (stan podloza; mroz/roztopy); SCI300 powyzej ok. 25 C zanizony (B: ok. -7 % w 25-30; -17,8 % w 30-35 nierozstrzygniete); D900-D1800 orientacyjne |

### 1.2 Znane pulapki N1 (priorytetowe; pelna lista 18 pozycji w [A] 3)
- P-N1-01/02: jeden k=0,02 na wszystkich geofonach jest bledny (trend resztkowy 6-8x, CV 2x); beta osobno per geofon, wskazniki dopiero po korekcie.
- P-N1-03: SCI300/krzywizny NIE korygowac powyzej ok. 25 C; D0 dziala do ok. 30-32 C.
- P-N1-04: < 10 C reguly nieweryfikowalne na stacjach (brak referencji 15-25 C w tym samym miesiacu: 0/18 wizyt w 10-15 C); wazne wynika z dopasowania, nie z testu pasmowego.
- P-N1-05: temperatura FWD v4 to wpis operatora przenoszony na kolejne stacje (99,1 % `operator_carried`); ewentualnie T z N2. Flagi w `measurement_flags` dla wartosci zastepczych NIE istnieja — filtrowac samemu.
- P-N1-06: sonda 12 cm na Podkowie zawyza +2,55 C; do wyznaczania beta tylko czujniki MET (T_mid). Dla uzytkownika N1: T_mid z sondy = ryzyko ~5 % bledu korekty na 1 otwor.
- P-N1-07: beta zalezy od grubosci pakietu; nie przenosic poza 15-30 cm. Wspolczynniki wyznaczone na 24-25 cm (TN, Podkowa), jeden rok danych.
- P-N1-08: jedno beta na caly rok (decyzja Jacka); brak wspolczynnikow sezonowych.
- S-N1-2: niespojne granice zakresu dopasowania w kodzie (`<=25` w `e2a3f_range.fit_params`, `<25` w `e2aR4.fit_params_range`, `<30` w `E3F`) — w pakiecie JEDNA konwencja (proponuje: dolna domknieta, gorna otwarta dla dopasowan; dla flag zakresu — domknieta, patrz PROJEKT 4.1).
- S-N1-3: `e2aR4_coefs.csv` kolumna `n` = liczba replik bootstrapu, nie liczba danych.

### 1.3 Co przeniesc / co pominac
Przeniesc: `apply_rule` (z enumem), `apply_f`, `build_index20`, `classify_session` (jako flaga jakosci temperatury), dane `e2a3_final_k_profile.csv` (jako pliki danych pakietu z naglowkiem pochodzenia), logike `normalize 50 kN`, mapowanie geofonow.
Pominac: bootstrap, CI, werdykty rownowaznosci, pasma temperaturowe, thaw/no_thaw, zapis do baz (`paths.release_guard`, `md5_r2`, `insert`, kopie `_pre_pNNN.db`), `datasets.py`, `paths.py` (sprzezone ze schematem bazy).
Opcjonalnie (modul `fit`): `qp_fit_nd` / `fit_k_profile` — tylko jesli uzytkownik ma wyznaczac wlasne k/beta; wymaga scipy lub reimplementacji numpy (bisekcja QP + zlota sekcja dla k, ok. 40 linii, zweryfikowana w E0 — `verify_k.py` w notatkach).

---------------------------------------------------------------------------------------------------

## 2. N2 layer_temp — temperatura warstwy asfaltowej

### 2.1 Sciezka kodu referencyjnego ([E] sekcja 1, 3)
```
z14c_candidates.process_unit (mode single, target masa)
  -> z14b_single_shot.calibrate (brentq po a_sw, bramka |Ts(a=1)-Ts(a=0.03)| < 1.0 C -> flaga gate)
  -> z14lite_validate.predict_block
  -> depth_thickness_study.sim_eb_all_depths -> energy_balance_bc.simulate_eb
```
Wynik: kolumna `phys_single_masa` w `Z14c_candidates.parquet`. Ta sama funkcja w produkcyjnym prototypie `z15_temperatures.predict_side` (`t12_cal`). Dotyczy wylacznie klasy terenu TN ("otwarta"); hybryda i XGBoost nie wchodza do wartosci referencyjnej (hybryda B pogarsza H: 2,12 vs 1,75).

### 2.2 Wejscia i parametry zamrozone
- Wejscie obserwacji: czas lokalny (naiwny, Europe/Warsaw z DST), lat, lon, `t_surface` (IR/pirometr aparatu), `t_air`. Siatka OM: lat/lon zaokraglone do 0,05 st.
- Open-Meteo: `https://archive-api.open-meteo.com/v1/archive`, `timezone=UTC` OBOWIAZKOWO (erratum czasu 2026-11-04: `Europe/Warsaw` przesuwa etykiety o ~1 h), `wind_speed_unit=ms`, okno [dzien-35 d, dzien+1] (end_date = dzien+1, inaczej ogon cache po 23:00 -> S-N2-4); zmienne uzywane: `temperature_2m, dew_point_2m, wind_speed_10m, cloud_cover, shortwave_radiation` (+ `snow_depth` wymagane technicznie przez `meteo_to_10min`; pozostale 9 zmiennych w repo to balast).
  Cache `output\z14lite\openmeteo_cache_utc\` 21 MB (332 okna H; wystarczy offline do testu).
- Parametry zamrozone (do `params_TN.json` z hashem zrodla; [E] sekcja 2): alpha 1,118e-6 m2/s; EB: a_sw 1,0 (gorna granica), h0 13,7037, h1 0,86360, c_vol 2,49167e6, svf 1,0; beta50 (5 wspolczynnikow t50), beta_ir (5 wspolczynnikow korekty IR->masa); stale solvera: DZ=0,01 m, NZ=51, DT=600 s, SPINUP 288 krokow, LEAD 3 doby, HIST 35 d, GATE_C 1,0, XTOL 1e-3, EPS 0,95.

### 2.3 Pulapki N2 (14 pozycji w [E] sekcja 7; wazniejsze)
- P-N2-1: brak guardu sezonu IV-X i sniegu w samym potoku (parametry z calego roku jednej stacji TN/Warszawa) — pakiet musi dodac flagi `out_of_season` (XI-III) i `snow` (snow_depth > 0,005 m).
- P-N2-2: kalibracja jednorazowa nie dziala w nocy (bramka); a_sw tylko w gore ograniczone (<=1,0) -> w H 44 % obserwacji = `bound_hi` (kalibracja nasycona); RMSE wg pory: 0-6 h 2,17; 6-12 h 1,38; 12-18 h 1,89; 18-24 h 2,17 (bias +1,48).
- P-N2-3: klasa terenu domyslnie "otwarta"; na terenie zacienionym (Podkowa) model TN ma bias +3..+5 C; brak danych o zacienieniu przejazdow.
- P-N2-6: czas aparatu FWD "niepotwierdzony"; zegar TSD `local_export_IBDiM_unverified`; 43 % par ma godzine < 5 lub >= 21.
- P-N2-8: `predict_block` interpoluje tylko 4/8/12 cm; N2 wymaga pelnej siatki 0-50 cm z solvera (rozszerzenie zwracania).
- P-N2-9: stan globalny (`ca.configure`, `z14c_omfix.apply`, `STATION_META`) — nie powielac; `main()` skryptow zapisuja do `output\` (nie wolac).
- P-N2-13: **referencja 1,75 to zbior H (eksploracyjny — metode zaprojektowano na tym zbiorze), NIE niezalezna walidacja**; na niezaleznym zbiorze C ta sama metoda: RMSE 2,73 [2,44; 2,98], v2 3,08; numeracja tabel: w kodzie H v2 = "Tab. 4.2", "Tab. 4.3" = C v2 (Q-N2-1).
- P-N2-11: beta50 dopasowane do jednego roku jednej stacji (Warszawa).

### 2.4 Co przeniesc / pominac
Przeniesc: solver EB 1D (`energy_balance_bc.simulate_eb`; numeryka bez zmian, z pelna siatka), `meteo_to_10min`, kalibracja brentq, klient Open-Meteo + cache, `om_utc_to_local`, parametry zamrozone, BELLS3 (komparator opcjonalny).
Pominac: hybryda A/B/C, XGBoost, foldy, bootstrap, E2-kalibracje, `surface_calib`, `ir_mass_relation`, Z14*/Z15b raportowe, K1-K5, tryb `session`, BELLS3_BT, BELLS3_O (wylaczone z wnioskow).

---------------------------------------------------------------------------------------------------

## 3. N3 tsd_network — przetwarzanie TSD na sieci + eksport XML

### 3.1 Stan: brak jednego skryptu produkcyjnego ([B] sekcja 13)
Elementy rozproszone: Hampel (`tsd_pipeline._hampel_col/smooth_bowl`; `e2bR9_lustro_data.hampel_*`), korekta beta=1,60 (`z15_temp_correction.py`, `e2bR9_lustro_data.correct_pair`), calki P0 (`e2a2b_beta.dense_integral`), okno i GoF (`e2b2_values`), QC (`qc_gyro_gps.py`, `qc_profile_consistency.py`, `scan_tsd_gps_segments.py`), pozycja (`e1_sref.py`), eksport XML (`tsd_to_xml.py`). Agregacja 50/100 m w bazie nie jest zaimplementowana jako funkcja (tylko SCI w skalach 1 m/50 m/1 km w `compare_sci_agg.py`).

### 3.2 Kroki, zrodla, wejscia

| # | Krok | Zrodlo | Wejscie | Uwagi / pulapki |
|---|---|---|---|---|
| 1 | Import B_1510off | `b1510off_v4_import.parse_raw_sup_txt` (+ `strip_unit`, `classify_file`) | `raw.sup.txt`: Chainage, D0, Slope x.xxx, GoF, Lat, Lon | test: plik T4202008060001, ok. 6104 wiersze, pierwszy wiersz Chainage 0,00, D0 -8342, Slope 0.110 = 1453,5559, GoF 0,23790418; zrownanie blokami z pgc (`align_*`) NIE przenosic (specyfika bazy) |
| 2 | Zestaw zer | `e2a_autc_1b.load_coefficients` (CSV `;`), `apply_variant`; zestawy A, B, C (`tsd_wspolczynniki.csv`), B_1510off, NEW1-NEW6 | `file_set`, nachylenia 10 kanalow [um/m] | P-N3-01: zestaw wyznaczac z danych, nie z nazwy pliku rekalibracji; `KeyError` dla zestawu spoza A/B/C; `zestaw_pliku()` oparty o date nocy — tylko mikro. Dla N3: wejscie to JUZ eksport B_1510off, zestaw zer = atrybut przejazdu |
| 3 | Calki P0 | `e2a2b_beta.dense_integral`, `CHANNELS_9`, `XS_SORTED`, `INTSTEP=0.001`; `e2b2_values.row_curv_integrals` | nachylenia 9 kanalow BEZ 1,51 m: -0,45, -0,30, -0,20, 0,11, 0,21, 0,31, 0,46, 0,61, 0,91 m; PCHIP, calka od x=0 | segmenty: A031 (0-0,31) ~ SCI300, A0361 (0,31-0,61) ~ BDI, A6191 (0,61-0,91) ~ BCI, A061, A091. **S-N3-1: P0 nie wymusza slope(0)=0; trapez `autc_front` (T) wymusza -> rozne wyniki** (mediana ilorazu SCI300 0,967 P0 vs 1,087 T). `REAR_X` dodatnie (modul), `X_POS/X_SIGNED` ze znakiem — latwa pomylka. Wartosci <= 0: A031/A0361/A6191 41/33/32 % par sieciowych — nie logarytmowac |
| 4 | Korekta d0 | `z15_temp_correction.py`: `d20 = apply_rule(d_T, T12, 'exponential', 0.01604146)`; `BETA_D0_PCT=1.6041459432458258` | d0 [um], T12 [C] z N2 | tylko d0 B_1510off (dla nominalnego d0 delta-beta -1,78 %/C — bledne); zakres 5-30 C, poza — flaga; temperatura powierzchni/pirometru NIE jako T warstwy; ta sama beta co D0 FWD (|delta-beta| <~ 0,3) |
| 5 | Hampel + okno | `tsd_pipeline._hampel_col`: `WIN=21` wierszy, `k=3.0*1.4826`, MAD prawdziwy okna, `thr>0`; `smooth_bowl` (tylko pelne czasze; Hampel na D0 -> odrzut CALEJ czaszy; srednia kroczaca 21 wierszy). Okno W5: `e2a_autc_1b.window_medians(half=5.0)` (domkniete); `e2b2_values` — mediana CALEK w oknie | wiersze 1 m po wspolrzednej korytarza | **S-N3-2: DWIE niezgodne implementacje Hampela** (`e2bR9_lustro_data`: przyblizony MAD wzgledem mediany kazdego punktu, bez warunku thr>0). Raport nie podaje parametrow (Q-N3-1). Okno 21 wierszy = +-10 m tylko przy kroku 1 m — w pakiecie okno w METRACH. Decyzja Jacka (etap 2): bez wygladzania w badaniach par; Hampel tylko w produkcie XML. Mediana okna: `a0361_w5 != a061_w5 - a031_w5` (mediany calek; rownosc w 49 z 9059 wierszy) |
| 6 | GoF | `GOF_MIN=0.5` (`e2a_autc_1b`, `e1_sref`, `e2b1_pairs.window_stats.gof05_share`) | mediana GoF okna | atrybut, nie filtr (filtr po poziomie okna: r 0,81, po wierszu: brak poprawy); nagl. `GoodNess limit 0.1500`, mediana GoF okna 0,177; wypelnienie d0 B_1510off 44-61 % vs pgc 95 % |
| 7 | Flagi QC | `qc_gyro_gps.omega_from_gps/xcorr_pearson/verdict`; `qc_profile_consistency.py`; `scan_tsd_gps_segments.py`; `tsd_position_offset` (-4,8 m, +-1,5 m, globalny) | kurs z zyroskopu vs GPS, opoznienie -7,9 m (tylko QC) | przesuniecie kanalow TSD; B_1510off ma przesuniecie pikietazu 20-50 m na starcie (2026), skala 1,4-1,6 promila; brak zyroskopu w niektorych eksportach (test zastepczy IRI) — B_1510off `.txt` nie ma kanalu zyroskopu/IRI! (P-N3-18) |
| 8 | Agregacja 50/100 m | brak implementacji; wzorce: `e1_sref` (biny 10 m = floor(s_ref/10)), `z15_curvature_correction` (L2 100 m, prog >= 3 pary), `compare_sci_agg.py` | wspolrzedna korytarza | wymaga napisania; bin po `s_ref`/wspolrzednej korytarza, NIE po pikietazu pliku (lambda po `chainage_m` dawala sigma_TSD 0,445 zamiast 0,30); szum d0: sigma_within(log) 0,36 (10 m), 0,19 (50 m), 0,14 (100 m), 0,10 (200 m) — agregowac na skali >= 200 m dla wnioskow, 50/100 m do produktu |
| 9 | Przeliczenie na skale FWD | `z15_korekta_TSD_FWD_conversion.csv`: `D0_20 = 1,61584 * d0_20` [1,5382; 1,68335] | d0_TSD,20 | mnoznik, nie afiniczna (Deming log-log 0,96 [0,90; 1,06]); wazny dla wartosci odcinkowych (>= 100 m); zmienne grupy aparat x rok 0,98-1,31 (Tab. 6.4); m z konfiguracji, domyslnie 1,62 |
| 10 | Eksport XML UC | `tsd_to_xml.py` (`write xml`, `smooth_bowl`, `sample_10m`, `convert_affine`), `format pliku UC.docx`, `UC_*.2026.xml` | 43 pola `DANE` | patrz 3.3 |

### 3.3 Eksport XML UC ([F] sekcje 4-5)
- 43 elementow `DANE` w stalej kolejnosci (identyczna w dokumencie i w XML): KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1, PREDKOSC, STRAIN_GAUGE, T_DROGI, T_DROGI_OBL, T_POW, F_P, OBC_KN, OBC_KPA, SCI_200, SCI_300, U_STD, D_minus_450, D_minus_300, D_minus_200, D_0, D_200, D_300, D_450, D_600, D_900, D_1200, D_1500, SLOPE_1_510, SLOPE_0_910, SLOPE_0_610, SLOPE_0_460, SLOPE_0_310, SLOPE_0_210, SLOPE_0_110, SLOPE_minus_0_200, SLOPE_minus_0_300, SLOPE_minus_0_450.
- Atrybuty korzenia: `KOD_ODDZ` (stala: "WA" w produkcji, "OP" w przykladzie docx), `ROK` ("2026"), `xsi:noNamespaceSchemaLocation="UC_Schema.xsd"` (plik schematu NIEDOSTEPNY w katalogu).
- Precyzje: KM 3, DYSTANS 0 (calkowity metr), LAT/LON 6, IRI 6, PREDKOSC 6 (m/s*3,6), STRAIN 3, T_* 1, F_P "1.0", OBC_KN 1, SCI/U_STD/D_* 3, SLOPE 4. UTF-8 bez BOM, LF, puste `<TAG></TAG>`.
- Pola z mapowania: 29 pol wprost ze zrodla 1 m (zgodne w 100 % rekordow na 3 odcinkach: 0 niezgodnosci), 14 pol do obliczenia z d0/P0: 11 x D_*, SCI_200, SCI_300, U_STD ([F] 4).
- **Problem projektowy (do decyzji): D_-450, D_-300, D_-200, D_450, D_1200, D_1500 NIE sa wyznaczalne z d0 + calek P0 (P0 daje D0 - D(x) tylko dla x w [0; 0,91] m; D300..D1500 producenta bezuzyteczne; wlasny model czaszy odrzucony — P-N3-05).** Wyznaczalne (wniosek wlasny, do potwierdzenia): D_0 (z d0), D_300 ~ d0 - A031, D_600 ~ d0 - A061, D_900 ~ d0 - A091 (calka P0 do x); D_200 wymagaloby calki 0-0,2 m (nie jest zdefiniowana w raporcie). Pytanie Q-N3-2.
- U_STD: w dokumencie UC = D_0 skorygowane temperaturowo do 20 C (k=0,02, T_DROGI_OBL), bez normalizacji obciazenia; w obecnym `tsd_to_xml.py` = D_0 po Tkor i afinicznej. SCI w przykladzie docx liczone z nieskorygowanych D.
- 'D Tkor' w plikach 1 m: liczby calkowite (puste przy bliskich zeru -> traci sie 5-16 % czasz) — nowe wejscie ich nie uzywa.
- Pulapki wejscia: kolumna 21 `T_XGB(120)` wpisana indeksem; w eksporcie 10 m i 1 m rozni sie o srednio +0,8/+2,6/+0,05 C; nagl. xls w wierszu 60/61; `tsd_to_xml.py` nie dziala na eksporcie 10 m bez zmian; KM z pierwszego markera Event (dryf do 24 m); `compare_tsd_fwd.py` liczy przy imporcie i zapisuje PNG; sciezka zapasowa `/sessions/hopeful-great-noether/mnt/outputs` wpisana na sztywno.
- Nie przenosic: `calibrate_conversion.py` / `conversion_coeffs.json` (kalibracja afiniczna na Tkor, DK50 a=0,849 b=+24,35; S8 a=0,473 b=+41,72), `compare_*` (wybor punktow po wartosciach FWD), `inject_dfwd.py`.
- Test struktury (golden-structure, [F] 8.2): root `UC`, 43 elementow w kolejnosci wzorca, regexy formatow, puste dozwolone tylko PROFIL_1, OBC_KPA i blok D/SCI/U_STD, DYSTANS krok 10, |dKM|=0,010 stalego znaku, D_0 >= D_200 >= ... >= D_1500 > 0; regresja na 29 polach K (3 odcinki).

### 3.4 Pozostale pulapki N3 (priorytetowe)
- P-N3-02: B_1510off dostepny tylko dla lat 2024-2026 (82 pliki, 1916,6 km); 2020-2021 `invalid_scale`, 2022-05-18 `missing_channel`, 2023-10/11 `not_recalibrated`; `align_fail` 16/82. B_1510off jest OBEJSCIEM modelu producenta, nie poprawna kalibracja.
- P-N3-03: przeliczenie innym plikiem wnosi wspolne przesuniecie nachylen (`common_offset_um_m`: 2024 +20,3, 2025 +21,0, 2026 +0,1) i inna skale pikietazu; porownywac tylko mediany okien.
- P-N3-04: `.xls` ucina przejazdy na 65 478/65 489 wierszach — importowac z `raw.sup.txt`.
- P-N3-05: d900/d1500 producenta w B_1510off bezuzyteczne; d0 eksportu nominalnego NIE do analiz temperaturowych.
- P-N3-09: 'Tkor' z tsd_2_xml nie jest odtwarzalna (T_XGB(120) nieobecna w plikach IBDiM); konwersja afiniczna nieuniwersalna.
- P-N3-11: A031/A0361/A6191 TSD <= 0 w 41/33/32 % par sieciowych; BDI 2024-2025 z nachylen eksportu oryginalnego obciazone (27-54 % <= 0) -> bierz z przeliczenia B_1510off.
- P-N3-12: wspolny adres `s_ref` (208 korytarzy, 2473 km; 98,45 % punktow); pulapki: 44 korytarze rownolegle ~2 m, 98 korytarzy < 1 km, 28 przejsc bez bloku r >= 0,8.
- P-N3-13: korekta polozenia TSD globalna -4,8 m (+-1,5 m); zyroskop-GPS -7,9 m tylko QC.
- P-N3-14: poziom TSD zalezy od wersji rejestratora (1.7/1.0.x/2.0.17.0) i przedzialu kalibracji (`calib_interval`: K2024-03-01, K2025-05-27, K2026-05-19); kampania `1.0|2023-10-23` = exclude.
- P-N3-17: strefa betonu A2 (842 151 punktow TSD); stacje FWD w strefie traktowane jako asfalt; sigma_within na betonie 1,6x wieksza.

---------------------------------------------------------------------------------------------------

## 4. N4 tsd_fwd_compare — porownanie TSD-FWD

### 4.1 Lancuch zrodlowy ([C] sekcja 1) i tryby wejscia
```
build_road_db -> tsd_fwd_sections (detect_sections, Tab. 3.2) -> review (167 confirmed) -> match_sections -> e1_sref (s_ref, korytarze)
 -> e2b1_geometry (polozenie plyty FWD) -> e2b1_pairs (kandydaci A/B/C/X, pary zerowe) -> e2b2_values (wartosci par, lambda)
 -> e2b2_agreement (miary) -> z15_pairs_export -> z15_temp_correction (korekta do 20 C) -> e2x_uncertainty_methods (WCU/WCR, CR2)
 -> e2bR9_lustro_* (warianty reprezentacji, warunki, kalibracja poza proba)
```
- **Tryb A (pary gotowe)**: wejscie = `z15_pary_wejscia.csv` + T12 obu stron (`Z15_temperatury_par.csv`) + `e2b2_pairs.csv` (dt_days, win5_gof05_share, device, era, calib_interval, sigma_long_fwd). Realny do wdrozenia od razu.
- **Tryb B (z geometrii)**: pelna procedura od wspolnych odcinkow do par; wymaga przeniesienia ok. 3500 linii (`e1_sref`, `e2b1_geometry`, `e2b1_pairs`, `detect_sections`). Minimalny schemat wejsc: [C] sekcja 5.

### 4.2 Kroki i zrodla

| # | Krok | Zrodlo | Pulapki |
|---|---|---|---|
| 1 | Wspolne odcinki (Tab. 3.2) | `build_road_db.detect_sections` (l. 2206-2500) przez `rebuild_sections.py --section-radius 8`; `min_coverage_pct`, `min_matched_stations=5`, `min_overlap_len_m=500`, `min_abs_corr=0,80`, `bearing_tol_deg=30`, `lane_same_max_m=0,75`, `lane_adjacent_max_m=2,0`, `same_year_only` | S-N4-1: **rho >= 0,80 to |Spearman(station_m, chainage_m)| (monotonicznosc), nie korelacja ugiec**; `match_sections` (`stage1_capture`) uzywa promienia 30 m, nie 8 m; plaskie przyblizenie 111320 m/st (zmieni wynik w progu 8 m minimalnie) |
| 2 | Raport "linia do linii" | `section_manual_checks.py`, `verify_sections.py`, `plot_tsd_fwd_sections.py` (przeglad reczny 167 `confirmed`) | N4 ma zastapic raportem + wykresy na odcinek |
| 3 | Pozycja FWD | `e2b1_geometry.py` (regula anteny, kierunek z danych, ciagi, `sigma_era`), `e1_sref.py` (`s_ref`, korytarze, przesuniecie TSD -4,8 m) | S-N4-2: **niespojne reguly anteny 8002-367: 5,0 m od 2025-01-01 (`e1_sref`) vs 5,5 m do 2025-10-09 (`e2b1_geometry`, P043b); lustro uzywa jeszcze 2025-10-01** — domyslnie P043b (5,5 m, 2025-10-09); HWD 8082-119 d=1,0 m; 8002-369 d=1 m (niepotwierdzone); kierunek sesji z danych (iloraz ds_ant/dstation), nie z pola bazy (zgodnosc 65,9 %); zalozenie station_m rosnie zgodnie z jazda |
| 3a | Pozycja TSD | `e1_sref` + `tsd_position_offset` | S-N4-3: nie wiadomo, czy -4,8 m jest wliczone w `s_ref`/okna W5 i w jakiej konwencji znaku (Q-N4-3) |
| 4 | Pary geometryczne W5 (W10) | `e2b1_pairs.window_stats`, `e2b2_values.tsd_values_for_window`, `lustro_warianty.build_b1510_reps`; okno po `s_ref`, `searchsorted`, przedzial domkniety, >= 3 wiersze niepuste; mediana okna | S-N4-4: `e2b2_values` uzywa zakresu `tsd_id_min..max` zamiast odleglosci — ma inna definicje okna niz lustro (hipoteza rozbieznosci par zerowych); W5 = glowny, zawezanie okna POGARSZA zgodnosc; wybor po wartosciach (C) tylko diagnostycznie z flaga |
| 5 | Pary zerowe | `e2b1_pairs.build_null_pairs` (K8): +-200 m i permutacja >= 300 m, seed 20261017; `e2b2_values.build_null_values`; `e2b2_agreement.build_null_test`; `e2b2b_extra.paired_bootstrap_null`; `lustro_warianty` (krok 4) | `e2b1_null_*` jako SKRYPT nie istnieje (tylko tabele); sparowany bootstrap sesji (prawda - zero) obowiazkowy — skladanie CI maskowalo efekt |
| 6 | Korekta do 20 C obu stron | `z15_temp_correction.py`, `e2aR2_rules.apply_rule`, `lustro_data.correct_pair(fwd_val, tsd_val, fwd_t12, tsd_t12, treatment, beta_pct)` treatment in {none, main_after (exp 1,60415), k02} | T12 po obu stronach z modelu (N2/DOKTORAT); `build_temp_variants` wycofane (wpis 180) |
| 7 | Miary zgodnosci | `e2b2_agreement.point_stats`, `deming`, `bootstrap_ci`; `ccc`, Bland-Altman (ilorazu: GM*exp(+-1,96*SD ln)), mediana ilorazu, SD log-ilorazu, r/rho w obrebie sesji | Deming: x=TSD, y=FWD, lambda=Var(err_FWD)/Var(err_TSD), log-log; wynik silnie zalezy od lambda (lambda x2 -> 0,93; lambda=1 -> 0,61); lambda d0 = 0,11787 (sigma_TSD 0,296408 z 2015 par binow po `s_ref`, sigma_FWD 0,101763 z `e12_lambda`, n=128) — `katalog_produktow.md` zabrania 0,09 (zawyzona) |
| 8 | Niepewnosc | `e2b2_agreement.bootstrap_ci` (po sesjach, 1000-2000 replik, percentylowy); `e2x_uncertainty_methods.py`: dziki bootstrap klastrowy Webba (WCU/WCR 9999), CR2 + Satterthwaite, klaster tygodniowy ISO; `seed_for` (crc32) | percentyl przy 36 klastrach niedoszacowuje; dla malej liczby klastrow (3-15) M1-M3 1,3-2,0x szersze |
| 9 | Tabela warunkow | `e2bR9_lustro_warunki.py`: dt (0-1 d, 2-30, >30), udzial GoF, CV D0 odcinka (tercyle), aparat x rok | S-N4-5: pomija 251 par z ujemnym dt (suma 5260 z 5511); uzywa `tsd_year` zamiast `calib_interval` (K2024-03-01, K2025-05-27, K2026-05-19); CV(D0) na powtarzanych wartosciach stacji — liczyc na unikalnych stacjach |
| 10 | Kalibracja poza proba | `e2bR9_lustro_kalibracja.py`: `fit_multiplier`, `fit_affine`, `leave_one_group_out` (po sesji) | mnoznik W5 k02 w probie a=1,4222, MAE 27,6747; LOSO MAE 27,7366 |

### 4.3 Wartosci kontrolne N4 ([C] sekcja 3, 7.3)
- `main_before`: mediana 1,40644 [1,31686; 1,48572], SD log 0,342756, r 0,611999, rho 0,503964, CCC 0,424149, Deming log-log 1,05235 / 0,106303 (lambda 0,11786960).
- `main_after`: mediana 1,61584 [1,5382; 1,68335], SD log 0,321151, r 0,659578, rho 0,580602, CCC 0,346871, Deming log-log 0,958655 [0,902308; 1,05999], intercept 0,642298, Deming liniowy 1,41861 / 8,16356; 5511 par, 36 sesji; grupy: old_2025 1805, hwd_2024 1546, old_2024 1087, hwd_2026 703, unconfirmed_2026 370.
- Niepewnosc W3: M0 [1,53804; 1,65362], WCU [1,53793; 1,6602] (WCR p 0,9393), CR2 [1,53689; 1,66116] dof 20,5.
- Warunki (lustro): dt 0-1 d: r 0,857391 (n 119); 2-30 d: 0,322221 (1873); >30 d: 0,366773 (3268); GoF >= 0,8: 0,814548 (1481); przeciecie 0,83682 (99).
- Syntetyczne: `test_e2b2.py` T1/T2 (Deming: a=1,3, b=-0,15, sigma_x 0,10, sigma_y 0,18); `test_e2x_uncertainty.py` (pokrycie 95 % dla 5/15/35/73 klastrow); `test_e1.py`, `test_e2b1.py` — przeniesc prawie 1:1.

### 4.4 Pulapki N4 (priorytetowe)
- P-N4-01: parowanie wylacznie geometryczne; wybor wg FWD cyrkularny (r 0,754 prawda vs 0,726 zero; CCC 0,42 -> 0,75).
- P-N4-02: niepewnosc polozenia FWD (antena/odbiornik GPS): `sigma_era` nowy 0,38 m / stary 1,93 m / HWD 0,195 m; warstwy A/B/C/X.
- P-N4-03: ten sam rok kalendarzowy (`same_year=1`); `lane_match='same'` zbior podstawowy; liczby: 9201 par (e2b2_pairs) / 9132 kandydatow 2024-26 / 6087 par A+B / 5511 par z waznym W5 — NIE mylic.
- P-N4-07: pary lacza rozne pory roku (mediana odstepu 75 d); iloraz bez korekty T to nie wspolczynnik przeliczeniowy; normalizacja temperatura powierzchni = porazka metodyczna.
- P-N4-08: krzywizny: proporcjonalnosc ODRZUCONA (Deming log-log SCI300 0,567/0,479/0,249 na L1/L2/L3); TSD <= 0 w 41/33/32 % par.
- P-N4-10: zgodnosc silnie zalezy od warunkow (dt, GoF, zmiennosc) — raportowac warstwowo.
- P-N4-12: czas FWD: 43 % par z godzina < 5 lub >= 21 (zerowany zegar, 9 sesji).
- S-N4-6: globalny logger `UM.OUT['fh']`, `sys.path.insert`, `release_guard`, kontrole `ctrl_stop/sys.exit` w srodku obliczen, `backcal.bootstrap` z `hash()` jako seed (nieodtwarzalne) — przeredagowac; cache pickle -> Parquet/CSV.
- S-N4-7: konwencje: `lateral_m` + = lewo (`e1_sref`) vs `cross_track_signed_m` + = prawo (`match_sections`) — ujednolicic; uklad EPSG:2180 (x=E, y=N).

---------------------------------------------------------------------------------------------------

## 5. Rozbieznosci miedzy promptem/raportem a zrodlami (do informacji Jacka)

1. **Tab. 7.1 vs `e2a3_final_k_profile.csv`**: raport Tab. 7.1 ma wartosci zaokraglone (k 0,016/0,014/0,012/0,010/0,007/0,003/0,002/0,002/0,003; beta 1,60/1,38/1,22/0,95/0,71/0,33/0,22/0,22/0,27); testy akceptacyjne z promptu odnosza sie do pelnej precyzji z CSV. Wspolczynniki wariantu A "5-25 C" nie istnieja jako osobne dopasowanie (CSV = 5-30 C; k D0 5-25 C po przeliczeniu 0,01753 vs 0,01611). Raport R7.1 opisuje A i B zakresami walidacji, nie osobnymi dopasowaniami.
2. **Test pasmowy R4**: nie weryfikuje korekty ponizej 15 C (n_with_ref = 0 dla < 10 C, 18 dla 10-15 C); test pasm w E1 (jesli w zakresie) wymaga fixture `e2a3_visits` (848 wizyt, export z bazy do CSV) i `l20_error`.
3. **N2**: raport (4.3 i 4.10) nie zawiera wystarczajacych danych do implementacji (a_SW domyslne i granice, svf, h0, h1, c_vol, dolny BC, korekta IR) — dane sa w `temp_model` ([E] sekcja 2).
4. **N3**: raport nie opisuje formatu XML UC (pojecie "UC" nie wystepuje w raporcie; odsylacz do `tsd_2_xml`), nie podaje parametrow filtra Hampela, nie definiuje algorytmu przeliczenia d0 TSD bez czujnika 1,51 m dla lat 2024-2026 (wymaga programu producenta -> `baza_B_1510off`, poza zakresem narzedzia).
5. **N3**: korekta temperaturowa calek P0 jest nieokreslona (raport: "nie korygowac wspolczynnikami FWD", R6.3 skorygowal wlasnym beta wskaznika FWD).
6. **N4**: mnoznik 1,62 policzony dla wszystkich 5511 par, takze z T12 poza 5-30 C (4,2 i 30,8 C), a R7.3 nakazuje flagowac; zbior DK50/S8 jest zarazem zbiorem kalibracji i referencyjnym testu.
7. **Numeracja i liczby**: sesje FWD odcinkow 253/251/250; sekcje 444 (v3)/445 (v4); pary 9201/9132/6087/5511; pliki `.mdb` 124/126/127.
8. Wiecej: [A] sekcja 5 (20 pytan), [D] sekcja 7 (37 pozycji), [E] E (13), [F] 8.3 (13).

---------------------------------------------------------------------------------------------------

## 6. Zrodla przeczytane

- `C:\WORK\DOKTORAT\publikacje_monografia\raport_PWS-1063\raport_PWS-1063_tekst.md` (v1.12; 95 komentarzy HTML) — [D].
- `C:\projects\sql_tsd_fwd`: README.md, raport_metodyka_baza_TSD_FWD.md, raport_techniczny_baza_TSD_FWD.md, plik_wymiany_informacji.md, pomysy_idee_plany\etap2_koncepcja_dopasowania.md, monografie\rejestr_wnioskow.md, katalog_produktow.md, bak\ (ok. 40 skryptow), tabele\ (wyniki referencyjne) — [A], [B], [C].
- `C:\WORK\DOKTORAT\temp_model`: CLAUDE.md, requirements.txt, src\ (m.in. fourier_1d, energy_balance_bc, operational_bc, surface_calib, ir_mass_relation, fetch_openmeteo, z14lite_*, z14b/c/d_*, z15_temperatures, validation_protocol), output\z14lite\ — [E].
- `C:\WORK\DOKTORAT\tsd_2_xml`: README_workflow.md, tsd_pipeline.py, tsd_to_xml.py, calibrate_conversion.py, compare_tsd_fwd.py, compare_sci_agg.py, inject_dfwd.py, conversion_coeffs.json, format pliku UC.docx, UC_*.xml, Drops*.xlsx, stations*.xlsx, T*.pgc.ibdim*.xls(x) — [F].
- Nie znaleziono: `e2b1_null_*` jako skryptu (pary zerowe w `e2b1_pairs.py`, `e2b2_values.py`, `e2b2_agreement.py`, `e2b2b_extra.py`, `e2bR9_lustro_warianty.py`); `kontrola2_*.py` — jest tylko `kontrola2_nachylenia.py`; jednego skryptu realizujacego caly lancuch N3; `UC_Schema.xsd`.
- Kontrola integralnosci zrodel: w E0 nic nie zapisano w `C:\projects\sql_tsd_fwd` ani `C:\WORK\DOKTORAT` (patrz DZIENNIK, E0).

---------------------------------------------------------------------------------------------------

## 7. Katalog `inne\` — materialy historyczne (przeglad 2026-11-14)

Katalog: 604 pliki, 238 MB, **nie sledzony w git i poza pakietem** (w `.gitignore`). Ocena wg przydatnosci dla N1-N4. Pliki czytane: wszystkie skrypty i dokumenty z `AUTC`, `TSDLayerIQ`, `xml\main.py`, `xml\arch\*.xsd` + przykladowy XML, `soft_xgb`, `tsd_xgbr`, `autoresearch` (README, program.md, wyniki), `skrypty\skrypty_arch\scrap_mdb_alldata.py`, naglowki `skrypty\main.py`, `gps_tsd\SPIDnavi.py`, `tsdpath\readme.txt`. Tylko po nazwie/naglowku ocenione: reszta `skrypty\skrypty_arch` (audio_to_doc, arch_audio, statystyki*, testy, exe_creator, imageViewer, sql alchemy), pliki `*.xlsx`/`*.png`/`*.wav`, biblioteka generateDS (kod cudzy, wersja 2.43.3).

### 7.1 Przydatne (wplywa na projekt)

| Katalog | Co to jest | Wniosek dla N1-N4 |
|---|---|---|
| `xml\arch\` (`dane_elem_tsd.xsd`, `dane_elementarne.xsd`, `dane_podstawowe.xsd`, `xml\gml\gmlProfileDSN.xsd`, `xml\xlink\xlinks.xsd`, przyklad `G02_08280001_PP-U.xml`, wygenerowane `dane_elem_tsd.py`/`dane_elementarne.py` przez generateDS) | **Schemat DSN (Heller IG, namespace `http://www.heller-ig.com/wdsn/1.0.0`) dla ugiec TSD (podprojekt `PP-U`)**: `daneElementarnePPUgeo` (geograficzne) i `daneElementarnePPUSiec` (sieciowe); `RekordPPUTyp`: atrybuty `A` (odl. od prawej krawedzi pasa [m]), `D0`, `D300` [um], `F` [kN], `tWarstwAsfaltowych`, `tOtoczenia`, `V`, `odlegloscOdOstPomiaru`, `D0FWD`, `D300FWD`, `srPlyty`; naglowek: `parametryPomiaru` (`numerRejestracyjny`, `systemPomiarowy`, `producentUrzadzeniaPomiarowego` = Greenwood, `metodaOkreslaniaPolozeniaGeograficznego` = GPS+INS, `liniaPomiarowa` = slad prawego kola, odstep 1 wartosc co 100 m). Przyklad z TSD 2023-08-28 (`T4202308280001`): 1720 rekordow, w strumieniach co 10 m po 10 rekordow z TA SAMA wartoscia (odlegloscOdOstPomiaru 0-9), `D0FWD`/`D300FWD` = wartosci w skali FWD, `A="X"`, `srPlyty=""`, `V=""`. **To INNY format niz `UC_*.xml` z `tsd_2_xml` (43 plaskie pola `DANE`, atrybuty `KOD_ODDZ`/`ROK`).** W DSN wystarczy `D0` i `D300` (wyznaczalne z d0 i A031) — problem pol D_-450...D_1500 z p. 3.3 w tym formacie nie wystepuje. `UC_Schema.xsd` nadal nieznany. Pytanie Q-N3-10 (ktory format jest docelowy dla N3: UC, DSN-wdsn, oba) |
| `TSDLayerIQ\` (PyQt, 2025-11; `app\core\pipeline.py`, `io_fwd.py`, `io_tsd.py`, `models.py`, modele `XGBoost_Bell3_opt.*`, `model_xgb_interpolacja.json`, `RNN_interpolacja_v3_bez_rainfall.h5`) | **Zrodlo "procedury", z ktorej wywodza sie `tsd_2_xml` i kolumny `T_XGB(120)`, `*Tkor`, `*FWD`**: (a) `T_XGB(120)` = model XGBoost "Bell3_opt" (glebokosc 120 mm; wejscia: `one_day` = srednia dobowa temp. powietrza dnia poprzedniego WPISYWANA RECZNIE w GUI, `IR` (temp. powierzchni), `Air_T`, `depth`, `sSin155`, `sSin135` = sinusoidy czasu dobowego); (b) `Tkor` dla TSD = `D * (1 + coef*(20 - T)) * 5000/(0,981*Strain[kg])` (normalizacja do 50 kN, `coef` 0,02 droga publiczna / 0,01 autostrada); (c) `*FWD` = przeliczenie potegowe `D_FWD = 4,1497 * D_Tkor^0,7747` (funkcja przeliczeniowa TSD->FWD, wczesniejsza niz mnoznik 1,62); (d) `SCI300_FWD = D0 - D300` ze skorygowanych, `BB_max = 1,24 * D0`; (e) FWD z MDB: korekta `D*(1+coef*(20-T))*50/F`, dla FWD wspolczynnik `coef` tez 0,02/0,01 (komentarz w docstringu odwrotnie niz w kodzie: kod `0.01 if highway else 0.02`). **Dla N1:** odczyt MDB przez pyodbc: `Stations` (StationID, Station [km], AsphaltTemperature, SurfaceTemperature, AirTemperature, Time, Latitude, Longitude) i `Drops` (StationID, DropID, History, Stress, Force, D1..D15), filtr `History` in (PRAWDA, TRUE, 1) = zrzuty uzywane (zgodne z `is_seating = 0` w bazie), mapowanie D1..D8 -> D0, D200, D300, D450, D600, D900, D1200, D1500; D9 = 1800 mm w `scrap_mdb_alldata.py`. **To jest zrodlo legacy-reguly k=0,02 (R1) i k=0,01 autostrady (R2)** — kod, nie tekst przepisu (Q-N1-4 nadal otwarte). **Dla N3:** potwierdza, ze `D * Tkor` z plikow 1 m jest wynikiem modelu XGB (nie BELLS3_BT) — raport wymienia "BELLS3_BT"; rozbieznosc nazw (Q-N3-11) |
| `skrypty\skrypty_arch\scrap_mdb_alldata.py` | Odczyt wielu `.mdb` (stations + drops, `history = True`, D1..D9) do jednego XLSX | Wzorzec czytnika MDB (to samo co wyzej); kod do przeredagowania, nie do kopiowania (bez `ReadOnly=1`, sciezki na sztywno) |
| `AUTC\main.py`, `main1.py`, `main3.py` | Najwczesniejsze prototypy calki nachylen: PCHIP przez nachylenia (kanaly 0,11-1,51 m), warunki brzegowe slope=0 przy 0 m i przy 3,04/3,51 m, ugiecie = odwrotna calka |nachylenia| z "ogona" czaszy do osi, warianty do x=0 / x_przeciecia / x=-0,2 | Poprzednik P0/T/PX; metoda rekonstrukcji pelnej czaszy z nachylen (z ogonem w 3 m) ODRZUCONA w projekcie (blad systematyczny +106/+197 % lub -51/-78 %, P-N3-05; wlasny model czaszy odrzucony). Nie przenosic; kod uzywa `scipy.integrate.cumtrapz` (usuniete w nowym scipy) |

### 7.2 Nieprzydatne lub poza zakresem (nie przenosic)

| Katalog | Powod |
|---|---|
| `autoresearch\` | Eksperyment ML: odtwarzanie D900/D1200/BCI ze zmiany geometrii belki TSD 2018->2024 (RF/ExtraTrees/MLP, petla "agent" z OpenAI API; `.env.example` z pustym kluczem). Wyniki slabe (CV MAE D900 ok. 48 um, BCI-geometria). Nie jest czescia metod raportu; zakaz: modele ML i zewnetrzne API (poza Open-Meteo). Dwa pliki `T42018_08260019`/`T42024_06050019.pgc.ibdim.xls` to dane tego eksperymentu |
| `soft_xgb\main_xgb.py`, `tsd_xgbr\main_xgb.py` | Starsze, jednoplikowe wersje procedury TSD (XLS->XLSX, T_XGB(120), Tkor, FWD, SCI300_FWD, BB_max); zawieraja literowki wspolczynnikow w `tsd_xgbr` (`0.2000` zamiast `0.02`, `5750` zamiast `5000`) — historyczne, zastapione przez TSDLayerIQ. `soft_xgb\T420250917pic3.pgc.ibdim.xls` (53 KB) = maly przyklad pgc IBDiM (mozliwy fixture do testu parsera, po zgodzie) |
| `skrypty\main.py`, `modeling_gui.py`, `modeling_tools.py`, `skrypty\arch main\` | PyQt5: ogolna aplikacja statystyczna (OLS, ElasticNet, Keras, k-fold) — poza zakresem |
| `skrypty\skrypty_arch\` (poza `scrap_mdb_alldata.py`) | Rozne skrypty pomocnicze: transkrypcja audio (`audio_to_doc`, `arch_audio`, `temp.wav` 6 MB), statystyki, GUI, `exe_creator`, SQLAlchemy, dane `BEELS3_*`/`dane do modelu BELLS3_*` (dane/wyniki modelu BELLS3 — wylaczone), `gpr_test_km.xlsx` (GPR), obrazki |
| `skrypty\oryginały do temperatur\stacja_pogodowa.csv`, `skrypty\skrypty_arch\stacja_pogodowa.csv` | Stare dane stacji pogodowej (16 753 wiersze; temp. 0/20/300 cm, wilgotnosc, opad, profile P1..P13 na 2-22 cm); dwie wersje roznia sie od 2. wiersza. Dane zrodlowe modeli BELLS3/XGB; N2 opiera sie na danych TN/Podkowa z `temp_model\` i parametrach zamrozonych — nie uzywac |
| `gps_tsd\` | `SPIDnavi` (Flask, GPS z portu COM, KML, mapa) + gotowe `.exe` (2 x 17 MB) i artefakty PyInstaller (`build\`) — narzedzie nawigacyjne operatora, poza N1-N4 |
| `tsdpath\` | System nawigacji pokrycia LCMS na lotnisku (Node.js, `bin\node.exe` 89 MB, `Lotnisko Chopina.pdf` 18 MB, GNSS 10.224.2.9:28001) — inny projekt; dodatkowo `.claude\settings.local.json` z uprawnieniami |
| `xml\generateDS-2.43.3\` | Kopia biblioteki generateDS (generator klas z XSD); potencjalnie uzyteczna tylko jako narzedzie do WALIDACJI/generacji, nie do pakietu. W pakiecie: wlasna deklaratywna tabela pol + walidacja XSD przez `lxml` (opcjonalnie), bez zaleznosci od generateDS |
| `xml\main.py` | Prototyp XML `daneElementarnePPFgeo` (zdjecia, kamera) — dane fotograficzne, nie ugiecia |
| `*\.idea\`, `__pycache__\`, `build\` | Artefakty IDE/kompilacji |

### 7.3 Wnioski
1. **Nowa informacja istotna dla N3:** dwa formaty XML (UC vs DSN wdsn PP-U) i schematy XSD DSN sa dostepne lokalnie (`inne\xml\arch\*.xsd`). Dopisano pytania Q-N3-10 i Q-N3-11 do `PROJEKT.md`.
2. **Wyjasnienie pochodzenia `T_XGB(120)`, `Tkor`, `*FWD`:** procedura TSDLayerIQ/`soft_xgb`; potwierdza P-N3-09 (Tkor nieodtwarzalna bez modelu i recznego `one_day`) i ze wczesniejsza funkcja przeliczeniowa TSD->FWD byla potegowa (4,1497 * D^0,7747), nie mnoznikiem.
3. **Dla N1:** wzorzec odczytu MDB (tabele i kolumny) i zrodlo legacy-regul 0,02/0,01.
4. Reszta jest historyczna lub poza zakresem; nic nie zostanie przeniesione do pakietu poza ewentualnym fixturem pgc (po zgodzie).
5. Ryzyka: 238 MB i pliki binarne (`.exe`, `node.exe`, `.h5`, `.model`) — katalog wylaczony z git (`.gitignore`); w `.env.example` brak prawdziwego klucza; skan wzorcow kluczy/hasel (`sk-...`, `api_key=`, `password=`, klucze prywatne) nie wykryl sekretow.
