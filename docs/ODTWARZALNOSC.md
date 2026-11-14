# Zalacznik: odtwarzalnosc obliczen narzedzi tsdfwd_tools wzgledem raportu PW.S-1063 (Etap II)

Dokument jest **generowany** (`docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py`) z kodu, planu testow (`docs/PROJEKT.md`, p. 6) i faktycznego przebiegu testow; nie jest pisany recznie, wiec nie rozjezdza sie z kodem. Narzedzia N1-N4 odtwarzaja metody raportu i sa jednoczesnie ich dokumentacja wykonawcza: dla wartosci referencyjnych z raportu i z bazy zrodlowej podano test, ktory je odtwarza, wraz z tolerancja i wynikiem.

## 1. Wersja i srodowisko

- pakiet `tsdfwd_tools` 0.1.0; commit kodu (HEAD w chwili generowania): `dd96a4e8078e` (drzewo robocze czyste)
- data wygenerowania: 2026-11-14; Python 3.11.18 (Windows); numpy 2.4.6, scipy 1.17.1, pandas 3.1.1, pyyaml 6.0.3, openpyxl 3.1.5
- testy z danymi referencyjnymi poza repozytorium (@reference): wykonane (dostepne dane zrodlowe, tylko odczyt)
- wynik calego przebiegu: 264 testow: 262 zaliczonych, 0 niezaliczonych, 2 oczekiwanych niepowodzen (znana rozbieznosc), 0 pominietych

## 2. Narzedzia i punkty raportu

| Narzedzie | Modul | Punkty raportu / zrodlo metody |
|---|---|---|
| N1 | `fwd_tempcorr` | p. 7.1 (Tab. 7.1) |
| N2 | `layer_temp` | model fizyczny TN (p. 7 - niepewnosc) |
| N3 | `tsd_network` | p. 6.1-6.2, 7.3; zal. H p. 4.2 (XML) |
| N4 | `tsd_fwd_compare` | p. 6.2-6.3, 7.3; p. 3 i 3a (tryby); Tab. 3.2 (odcinki) |

## 3. Macierz odtwarzalnosci

Kolumny: numer testu | co sprawdza | wartosc referencyjna (z raportu lub bazy zrodlowej) | tolerancja | rodzaj | liczba testow (zaliczone/pominiete/niezaliczone) | wynik. Rodzaj: `@reference` = porownanie z danymi zrodlowymi projektu (wymaga dostepu do nich); `@unit` = obliczenie analityczne lub dane syntetyczne w repozytorium.


### 3.1 N1 - fwd_tempcorr

| Test | Co sprawdza | Wartosc referencyjna | Tolerancja | Rodzaj | Przypadki: ok / xfail / pominiete / fail | Wynik |
|---|---|---|---|---|---|---|
| T-N1-01 | Wspolczynniki z pakietowego CSV zgodne z `e2a3_final_k_profile.csv` (scope lacznie) | D0 k 0,0161092 / beta 1,60415; D300 0,0123428 / 1,21602; D900 0,00328817 / 0,333874; D200 0,0140162 / 1,38103; D450 0,00958895 / 0,954185; D600 0,00702971 / 0,70652; D1200 0,00214063 / 0,216493; D1500 0,00215554 / 0,215758; D1800 0,00271306 / 0,269251 | 1e-9 (identyczne pliki) | @unit | 13 / 0 / 0 / 0 | **zgodny** |
| T-N1-02 | `apply_correction` linear/exp analitycznie; identycznosc przy T=20; odwracalnosc | D0=200, T=10: A 232,000 / B 234,702; T=5: A 248,000 / B 254,250; T=25: A 184,000 / B 184,623; T=30: A 168,000 / B 170,429; D300=150, T=10: A 168,000 / B 169,463 | 1e-3 (obl. wlasne) | @unit | 8 / 0 / 0 / 0 | **zgodny** |
| T-N1-03 | Zgodnosc z `e2aR2_rules.apply_rule` dla tych samych wejsc (kod zrodlowy w `tests\data\ref_apply_rule.py` z naglowkiem pochodzenia) | wartosc identyczna | 1e-9 | @unit | 5 / 0 / 0 / 0 | **zgodny** |
| T-N1-04 | Wskazniki: SCI300_20 = D0_20 - D300_20, BDI, BCI; przyklad D0=200, D300=150, T=10: A 64,000 / B 65,239 | j.w. | 1e-3 | @unit | 2 / 0 / 0 / 0 | **zgodny** |
| T-N1-05 | Normalizacja 50 kN: D*50/F; zrzuty nieosadcze; wybor zrzutu | analitycznie | 1e-9 | @unit | 3 / 0 / 0 / 0 | **zgodny** |
| T-N1-06 | Flagi: T<5, T poza zakresem A/B, brak T, 20,4, przeniesiona (klasyfikacja `classify_session` na wycinku sesji) | oczekiwane etykiety | dokladnie | @unit | 6 / 0 / 0 / 0 | **zgodny** |
| T-N1-07 | Fit: `qp_fit_nd` / `fit_k_profile` na `e2a3_visits` (848 wizyt; 414 z T_mid 5-30 bez stycznia) odtwarzaja wspolczynniki | D0 beta 1,60415 +-5e-5; k 0,0161092 +-3e-6; SCI300 beta 3,24407; BDI 2,8704; BCI 1,92233 | j.w. | @reference | 10 / 0 / 0 / 0 | **zgodny** |
| T-N1-08 | Pasma R4 (`l20_error` + `band_mean` na `e2a3_visits`): D0 lacznie no_thaw | 15-20: -0,224 %; 20-25: +0,220 %; 25-30: -1,064 %; 30-35: -3,762 % (n_with_ref 108/110/49/25) | 0,01 pp | @reference | 5 / 0 / 0 / 0 | **zgodny** |
| T-N1-09 | Regresja na pliku FWD (XLSX Drops/stations 50_1M): pelny potok; porownanie z recznym obliczeniem | 121 stacji; stacja 1: D0 = srednia 2 zrzutow znormalizowanych do 50 kN; D0_20 = D0*exp(0,0160415*(20-T)); SCI300_20 = D0_20 - D300_20 | 1e-3 (D0), 1e-9 (SCI) | @unit | 3 / 0 / 0 / 0 | **zgodny** |

### 3.2 N2 - layer_temp

| Test | Co sprawdza | Wartosc referencyjna | Tolerancja | Rodzaj | Przypadki: ok / xfail / pominiete / fail | Wynik |
|---|---|---|---|---|---|---|
| T-N2-01 | Glowny: H v2 (549 obs., 226 sesji), fizyka + kalibracja jednorazowa, 12 cm | RMSE 1,7486 (1,75) [1,6193; 1,8689]; MAE 1,4039; bias +0,2653 | 0,001 (zrodlowa replika: 1,7488 / 1,4042 / +0,2649) | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N2-02 | Liczebnosci i flagi kalibracji | n 549; sesji 226; ok 294, bound_hi 244, gate 11, bound_lo 0 | dokladnie | @reference | 2 / 0 / 0 / 0 | **zgodny** |
| T-N2-03 | Po obserwacji vs `phys_single_masa` (`Z14c_candidates.parquet`) | 544/549 zgodne do 1e-6 C; 5 obs. po 23:00 (S-N2-4): <= 0,2 C | wg opisu | @reference | 2 / 0 / 0 / 0 | **zgodny** |
| T-N2-04 | Komparatory | fizyka bez kalibracji 2,0872 / 1,6974 / +0,9455; BELLS3 2,4065 / 1,8160 / -0,3432 | 0,001 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N2-05 | RMSE wg pory | 2,167 (n 49) / 1,378 (n 226) / 1,889 (n 237) / 2,167 (n 37) | 0,005 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N2-06 | Solver: stan stacjonarny, bilans energii, round-trip kalibracji (Ts(a*)=target -> a~a*) | analitycznie | 1e-3 | @unit | 12 / 0 / 0 / 0 | **zgodny** |
| T-N2-07 | Czas/DST/UTC: `om_utc_to_local` (godzina podwojna, luka wiosenna), pomiar o 23:30 | wg opisu | dokladnie | @unit | 5 / 0 / 0 / 0 | **zgodny** |
| T-N2-08 | Tryb sieciowy: atrapa `http_get` (klient na `urllib`, bez `requests`): `timezone=UTC`, `wind_speed_unit=ms`, 6 zmiennych, okno [start-1 d, end+1 d]; retry 429; tryb offline bez zapytan | wg opisu | dokladnie | @unit | 5 / 0 / 0 / 0 | **zgodny** |
| T-N2-09 | Dryf parametrow: hash `params_TN.json` | wg zrodla | dokladnie | @unit | 2 / 0 / 0 / 0 | **zgodny** |
| T-N2-10 | Z15 (2. poziom): 200 par `{fwd,tsd}_t12_cal` vs `Z15_temperatury_par.csv` | zgodne < 1e-6 | 1e-6 | @reference | 1 / 0 / 0 / 0 | **zgodny** |

### 3.3 N3 - tsd_network

| Test | Co sprawdza | Wartosc referencyjna | Tolerancja | Rodzaj | Przypadki: ok / xfail / pominiete / fail | Wynik |
|---|---|---|---|---|---|---|
| T-N3-01 | `p0_integrals` na 9 kanalach z `e2a2_slopes.csv`; wiersz 1a, 2025-09-04, pt 0 | p0_a031 21,6023; p0_a061 39,0758; p0_a091 41,5524; p0_a0361 17,4735; p0_a6191 2,47669; t_a031 22,6437; t_a061 39,7148 | 1e-3 um | @reference/@unit | 1 / 0 / 0 / 0 | **zgodny** |
| T-N3-02 | Tozsamosci: A0361 = A061 - A031; A6191 = A091 - A061 (P0, T); NaN gdy jakikolwiek kanal NaN; stale przesuniecie zer (`apply_variant`) nie zmienia calek | analitycznie / `test_autc.py` T1-T6 | 1e-9 | @unit | 4 / 0 / 0 / 0 | **zgodny** |
| T-N3-03 | Calka profilu liniowego `a*(x-x0)`: `P0(x1) = a*(x1^2/2 - x0*x1)` | analitycznie | 1 % + 0,05 | @unit | 2 / 0 / 0 / 0 | **zgodny** |
| T-N3-04 | d0 W5 i calki P0 w oknie dla par sieciowych vs `e2b2_tsd_values.csv`; para 5288: d0_w5 153 (n=8), a031_w5 28,7412, a0361_w5 38,1424, a6191_w5 37,9944, a061_w5 79,3549, a091_w5 112,049 | wartosci z pliku (mediany calek w oknie) | 1e-6 dla tych samych wierszy | @reference | 2 / 0 / 0 / 0 | **zgodny** |
| T-N3-05 | Hampel: szereg staly + outlier; zgodnosc z `tsd_pipeline._hampel_col` na wektorze referencyjnym; brak flagowania przy thr == 0; odrzut calej czaszy | wg zrodla | dokladnie | @unit | 3 / 0 / 0 / 0 | **zgodny** |
| T-N3-06 | Korekta d0: `d0*exp(0,016*(20-T))`; zakres 5-30 flagowany | analitycznie; T12 TSD mediana 21,8 -> 1,152 przy 8,86 C roznicy | 1e-6 | @unit | 2 / 0 / 0 / 0 | **zgodny** |
| T-N3-07 | Parser `raw.sup.txt` (plik T4202008060001: 86 kolumn, znak D, `strip_unit`, ok. 6104 wiersze; wiersz 1: Chainage 0, D0 -8342, D300 -7695, Slope 0.110 1453,5559, GoF 0,23790418, Lat 50,091676027, Lon 19,813605221) | wg zrodla | dokladnie | @reference/@unit | 4 / 0 / 0 / 0 | **zgodny** |
| T-N3-08 | Eksport XML: golden-structure test (struktura z `UC_50_1_M_1.2026.xml`: root, 43 pola, kolejnosc, regexy formatow, puste tylko PROFIL_1/OBC_KPA/blok D-SCI-U_STD, DYSTANS krok 10, `\|dKM\|`=0,010, UTF-8 bez BOM, LF) + regresja 29 pol typu K na 3 odcinkach | wg [F] 8.2 | dokladnie | @unit/@reference | 5 / 0 / 0 / 0 | **zgodny** |
| T-N3-09 | Agregacja 50/100 m: bin = floor(s/step), mediana, prog n; flagi | syntetyczne | dokladnie | @unit | 1 / 0 / 0 / 0 | **zgodny** |
| T-N3-10 | Przeliczenie D0_FWD,20 = m*d0_20 (m 1,62; wartosc odniesienia 1,61584 [1,5382; 1,68335]) | analitycznie | 1e-9 | @unit | 1 / 0 / 0 / 0 | **zgodny** |

### 3.4 N4 - tsd_fwd_compare

| Test | Co sprawdza | Wartosc referencyjna | Tolerancja | Rodzaj | Przypadki: ok / xfail / pominiete / fail | Wynik |
|---|---|---|---|---|---|---|
| T-N4-01 | `z15_pary_wejscia.csv` + `Z15_temperatury_par.csv` -> `main_after`: mediana ilorazu, SD log, r, rho, CCC, Deming | 1,61584 (SD log 0,321151; r 0,659578; rho 0,580602; CCC 0,346871; Deming log-log 0,958655 / 0,642298); 5511 par; 36 sesji | punktowe 1e-5; mediana 0,01 | @reference | 4 / 0 / 0 / 0 | **zgodny** |
| T-N4-02 | `main_before` | 1,40644; SD 0,342756; r 0,611999; rho 0,503964; CCC 0,424149; Deming 1,05235 / 0,106303; lambda 0,1178696 | 1e-5 | @reference | 3 / 0 / 0 / 0 | **zgodny** |
| T-N4-03 | r i rho w obrebie sesji W5 (z `lustro`) | r 0,403905 (0,403); rho 0,338739; none 0,407298; k02 0,402391 | 5e-4 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-04 | Pary zerowe (`e2b2_null_values` + z15): mediana ilorazu, r globalne | 1,5952 / 1,6098 / 1,5932; r 0,5169 / 0,5242 / 0,4076 | 2e-3 | @reference | 3 / 0 / 0 / 0 | **zgodny** |
| T-N4-05 | r w obrebie sesji dla par zerowych W5 | wartosci lustro 0,155 / 0,135 / 0,096 vs e2b2b 0,118 / 0,141 / 0,023 — **znana rozbieznosc (Q-N4-1)**; test oznaczony `xfail` do decyzji, zapisuje obie wartosci | wg decyzji | @reference | 5 / 2 / 0 / 0 | **znana rozbieznosc** |
| T-N4-06 | Niepewnosc W3: sesyjny M0, WCU, CR2 | M0 [1,53804; 1,65362]; WCU [1,53793; 1,6602] (WCR p 0,9393); CR2 [1,53689; 1,66116] dof 20,5; seed `seed_for('e2x_w3_lacznie', 'wcu'/'wcr')` | 0,01 | @reference | 2 / 0 / 0 / 0 | **zgodny** |
| T-N4-07 | Warunki (dt, GoF, przeciecie) | dt 0-1: r 0,857391 (119); 2-30: 0,322221 (1873); >30: 0,366773 (3268); GoF>=0,8: 0,814548 (1481); przeciecie 0,83682 (99) | 1e-3 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-08 | Kalibracja mnoznika, LOSO (k02) | a 1,4222; MAE 27,6747; LOSO MAE 27,7366; mediana abs log 0,227208 / 0,227888 | 0,01 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-09 | Lambda d0 | 0,11787 (sigma_TSD 0,296408; sigma_FWD 0,101763; n 2015/128) | 1e-4 | @reference | 2 / 0 / 0 / 0 | **zgodny** |
| T-N4-10 | Syntetyczne: Deming (a=1,3, b=-0,15, sx 0,10, sy 0,18), CCC (bias 2), BA (bias 2, SD 0), pokrycie CI dla 5/15/35/73 klastrow | wg `test_e2b2.py`, `test_e2x_uncertainty.py` | 0,05/0,08; pokrycie 95 % +-3 pp | @unit | 19 / 0 / 0 / 0 | **zgodny** |
| T-N4-11 | Geometria (tryb B, jesli w zakresie): `detect_sections` z progami Tab. 3.2 na danych v4 | 445 sekcji; 167 `confirmed`; recall/precision wzgledem 167 | wg decyzji | @reference | 10 / 0 / 0 / 0 | **zgodny** |
| T-N4-12 | Zgodnosc z `e1`/`e2b1` testami syntetycznymi (to_2180, kierunek odwrocony, podzial ciagow, warstwy A/B/C/X, pary zerowe) | wg `test_e1.py`, `test_e2b1.py` | wg zrodla | @unit | 51 / 0 / 0 / 0 | **zgodny** |
| T-N4-13 | Polozenie plyty FWD, 46826 stacji `odcinki` vs `fwd_plate_position_e2b` | `s_fwd`, `sigma_long`, `era`, `pos_source`, `direction`, `run_id` | 1e-6 (sigma_long 1e-4) | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-14 | Kandydaci na pary i pary zerowe, korytarze 0..29 (prefiks `pair_id` 1..5632) vs `golden_pair_candidates`, `e2b1_null_map` | 5632 par; 16659 par zerowych; seed 20261017 | 1e-6 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-15 | Przypisanie wierszy TSD do korytarzy (`prepare_run` + `assign_run`) vs `tsd_sref` | korytarz > 99,95 %; `s_ref_gps` 0,02 m; `lateral_m` 0,003 m | jw. | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-16 | Mediana d0 w oknie W5 po `s_ref` vs `d0_tsd` Z15 | >= 99 % par zgodnych < 1e-6 (2888/2895 dla korytarzy 0..80) | 1e-6 | @reference | 1 / 0 / 0 / 0 | **zgodny** |
| T-N4-17 | Wyrownanie przejsc profilem (7 korytarzy, 100 przejsc) vs `tsd_passes`, `tsd_sref` | zrodlo wyrownania, liczba blokow, centrowanie, `s_ref` | `s_ref` 5 mm; centrowanie 1e-4 | @reference | 7 / 0 / 0 / 0 | **zgodny** |
| T-N4-18 | Os od zera z 239 plikow TSD ze scalaniem duplikatow pasa vs baza produktow | 165 korytarzy, 43 scalenia, 6 956 291 wierszy, 25 219 punktow wide | dlugosci 1e-3; `s_ref_gps` 1e-3 | @reference | 1 / 0 / 0 / 0 | **zgodny** |

## 4. Rozbieznosci wzgledem zrodel (wyjasnione)

| Oznaczenie | Opis | Test |
|---|---|---|
| S-N4-4 | Okno W5 liczone po s_ref, a nie po zakresie tsd_id: 7 z 2895 wartosci d0 par (korytarze 0..80) roznych od tabeli Z15; roznica wynika z definicji okna. | T-N4-16 |
| Q-N4-1 | r w obrebie sesji dla par zerowych W5: wartosci z raportu odtwarzaja sie z e2b2_null_values; wariant e2b2b daje inne liczby (znana rozbieznosc zrodel). | T-N4-05 |
| S-N2-4 | 5 obserwacji po godz. 23:00 roznych od kandydata zrodlowego do 0,2 C (reszta 544/549 zgodna do 1e-6 C). | T-N2-03 |
| Tab. 7.1 | Tab. 7.1 raportu jest zaokraglona (D450 +4 %, D900 -9 % wzgledem pelnej precyzji); domyslnie e2a3_full, tab71 dostepna jako zestaw. | T-N1-01 |

Powyzsze rozbieznosci sa jedynymi znanymi; szczegoly decyzji sa w `docs/DZIENNIK.md` i `docs/PROJEKT.md`.

## 5. Ograniczenia

- T-N2-01 odtwarza zbior eksploracyjny H v2 (powtarzalnosc obliczen), nie jest deklaracja dokladnosci produktu; dokladnosc na zbiorze niezaleznym C v2: RMSE 2,73 C [2,44; 2,98].
- Plik XML (N3) jest sprawdzany wewnetrznie wzgledem opisu z zalacznika H p. 4.2; walidacja wzgledem UC_Schema.xsd zostanie dodana po dostarczeniu schematu.
- Dane pomiarowe nie sa czescia repozytorium; testy @reference czytaja je w trybie tylko do odczytu ze sciezek podanych w tests/local_paths.yaml i bez tych danych sa pomijane.
- Alignment profilem i os korytarzy zalezy od zestawu przejsc podanych na wejsciu (referencja = najdluzsze przejscie; budowa zachlanna).

## 6. Testy uzupelniajace (bez numeru T)

Konfiguracja, wejscie/wyjscie, CLI i przypadki brzegowe, ktore nie odpowiadaja liczbie z raportu:

| Modul testowy | zaliczone | pominiete | niezaliczone |
|---|---|---|---|
| test_config_io_cli | 19 | 0 | 0 |
| test_fit | 10 | 0 | 0 |
| test_fwd_pipeline_units | 2 | 0 | 0 |
| test_n2_units | 5 | 0 | 0 |
| test_n3_units | 3 | 0 | 0 |
| test_rules_and_coefficients | 1 | 0 | 0 |

## 7. Jak odtworzyc

```bash
python -m pytest                                  # wszystkie testy (testy @reference tylko przy dostepnych danych zrodlowych)
python docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py  # przebieg + odswiezenie tego dokumentu
```

Testy @reference wymagaja pliku `tests/local_paths.yaml` (wzor: `tests/local_paths.example.yaml`) ze sciezkami do danych projektu; dane sa tylko czytane. Testy @unit i przyklady w `demo/` dzialaja bez danych zewnetrznych.

