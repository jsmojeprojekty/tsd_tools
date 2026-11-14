# DZIENNIK projektu narzedzia_tsd_fwd

## 2026-11-13 — E0: inwentarz i projekt

**Co zrobiono**
- `git init` w `C:\projects\narzedzia_tsd_fwd` (lokalnie; zdalnego repozytorium nie tworzono).
- Przeczytano zrodla (tylko odczyt): raport PW.S-1063 v1.12 (95 komentarzy HTML), dokumentacja `sql_tsd_fwd` (README, raport metodyczny i techniczny,
  plik wymiany, rejestr wnioskow, katalog produktow, koncepcja dopasowania), ok. 40 skryptow z `bak\`, tabele referencyjne, `temp_model` (src, output),
  `tsd_2_xml` (skrypty, pliki XLS/XLSX, UC_*.xml, format UC.docx).
- Utworzono: `docs\INWENTARZ.md` (kroki N1-N4: skrypt/funkcja zrodlowa, wejscia, zaleznosci, pulapki), `docs\PROJEKT.md` (struktura pakietu, schemat konfiguracji,
  sygnatury, formaty wyjsc, plan testow z wartosciami referencyjnymi, pytania do Jacka), `docs\notatki_E0\` (szesc notatek roboczych z audytu — sygnatury, cytaty wierszy tabel).
- Nie utworzono srodowiska ani kodu produkcyjnego (zgodnie z E0).

**Co sprawdzono (liczby)**
| Wartosc referencyjna (prompt) | Uzyskana (odczyt) | Roznica | Status |
|---|---|---|---|
| N1 D0 k 0,0161092 / beta 1,60415 | 0,0161092 / 1,60415 (`e2a3_final_k_profile.csv`, lacznie); niezaleznie z `e2a3_visits` n=414: beta 1,60415, k 0,0161094 | <= 1e-6 | OK |
| N1 D300 0,0123428 / 1,21602 | 0,0123428 / 1,21602 | 0 | OK |
| N1 D900 0,00328817 / 0,333874 | 0,00328817 / 0,333874 | 0 | OK |
| N1 pasmo R4 D0 25-30 C -1,06 % | -1,064 % (CI90 [-2,073; -0,047], n_with_ref 49) | 0,004 pp | OK |
| N4 W5 main_after mediana 1,6158 | 1,61584 (`z15_korekta_TSD_FWD_main.csv`); przeliczone niezaleznie 1,615841 | <= 1e-5 | OK |
| N4 5511 par, 36 sesji | 5511 / 36 | 0 | OK |
| N4 r w obrebie sesji W5 0,403 | 0,403905 (`e2bR9_lustro_warianty.csv`) | 0,0009 | OK |
| N4 pary zerowe 0,155 / 0,135 / 0,096 | zgodne z `e2bR9_lustro_warianty.csv`; niezalezne przeliczenie z `e2b2_null_values` daje 0,114 / 0,134 / 0,027 | do 0,07 | ROZBIEZNOSC — patrz STOP |
| N4 167 zatwierdzonych odcinkow | 167 `confirmed` w `tsd_fwd_section_review` (445 sekcji v4) | 0 | OK |
| N2 RMSE 1,75 / MAE 1,40 / bias +0,27 (549 obs., 226 sesji) | 1,7486 / 1,4039 / +0,2653 (`E3-T46_z14d_H_v2.csv`); replika niezalezna 1,7488 / 1,4042 / +0,2649 | <= 0,0005 | OK (zbior H eksploracyjny) |
| N3 d0 W5 / calki P0 vs `e2b2_tsd_values.csv`, `e2a2_autc_var.csv` | nie weryfikowano w E0 (wymaga fixture wierszy B_1510off i nachylen) | — | do E3 |
Integralnosc zrodel: po zakonczeniu audytu w `C:\projects\sql_tsd_fwd` ani `C:\WORK\DOKTORAT` nie ma plikow zmienionych po starcie pracy (kontrola `find -newermt`). Bazy SQLite otwierano wylacznie `mode=ro`.

**Najwazniejsze ustalenia**
1. N1: wspolczynniki z `e2a3_final_k_profile.csv` (5-30 C) sa pelnej precyzji; Tab. 7.1 raportu jest zaokraglona. Wspolczynnikow wariantu A "5-25 C" jako osobnego dopasowania nie ma.
2. N3: brak jednego skryptu produkcyjnego; dwie niezgodne implementacje Hampela; calki P0 z PCHIP bez wymuszenia slope(0)=0, wariant T wymusza; **D_-450, D_-300, D_-200, D_450, D_1200, D_1500 w XML UC nie sa wyznaczalne z d0 + calek P0**; `U_STD` w dokumencie UC to D_0 skorygowane temperaturowo, w `tsd_to_xml.py` = D_0.
3. N4: kryterium "rho >= 0,80" to |Spearman(station_m, chainage_m)| (monotonicznosc), nie korelacja ugiec; niespojne reguly anteny FWD (5,0 m od 2025-01-01 vs 5,5 m do 2025-10-09); tabela warunkow pomija 251 par z ujemnym dt i uzywa `tsd_year` zamiast `calib_interval`.
4. N2: referencja 1,75 to zbior H, na ktorym dobierano metode; na niezaleznym zbiorze C ta sama metoda ma RMSE 2,73 (v2: 3,08); 44 % H = `bound_hi` (kalibracja nasycona). Rdzen N2 jest maly (solver EB 1D, 5 zmiennych Open-Meteo, parametry zamrozone).
5. Srodowisko: w systemowym Pythonie brak scipy/openpyxl/matplotlib; kod zrodlowy wymaga scipy i numpy >= 2.

**Co zostaje:** zatwierdzenie projektu przez Jacka; potem E1 (szkielet + N1).

**STOP — decyzja (E0)**
Praca zatrzymana po E0 zgodnie z promptem. Do decyzji (pelna lista: `docs\PROJEKT.md` sekcja 8):
- Blokujace E1: Q-N1-1 (zestaw wspolczynnikow: e2a3 pelna precyzja vs Tab. 7.1), Q-N1-3 (regula zrzutu), Q-N1-5 (indeksy > 25 C), Q-N1-6 (czy potrzebne MDB w E1).
- Blokujace kolejne etapy: Q-N4-1 (kanoniczne wartosci par zerowych), Q-N4-4 (zakres trybu `geometry`), Q-N3-2 (jak wypelnic pola D_* w XML), Q-N3-3 (definicja U_STD/SCI), Q-N2-1 (referencja H v2 vs C v2).

## 2026-11-14 — E0 (uzupelnienie): przeglad katalogu `inne\`

**Co zrobiono**
- Przejrzano `inne\` (604 pliki, 238 MB): AUTC, TSDLayerIQ, autoresearch, gps_tsd, skrypty, soft_xgb, tsd_xgbr, tsdpath, xml (w tym generateDS i schematy DSN). Wyniki: `docs\INWENTARZ.md` sekcja 7. Nic w `inne\` nie zmieniono.
- `inne\` dodano do `.gitignore` (238 MB, pliki binarne: `.exe`, `node.exe`, `.h5`, `.model`); skan wzorcow sekretow bez wynikow, `.env.example` z pustym kluczem.
- Dopisano do `docs\PROJEKT.md` pytania Q-N3-10, Q-N3-11, Q-N1-7 i uzupelniono Q-N1-4.

**Co sprawdzono**
- `inne\xml\arch\dane_elem_tsd.xsd` + przyklad `G02_08280001_PP-U.xml` (TSD 2023-08-28): inny format XML (DSN wdsn 1.0.0, rekord z D0, D300, D0FWD, D300FWD...) niz `UC_*.xml` — 1720 rekordow, strumienie co 10 m.
- `TSDLayerIQ\app\core\pipeline.py`: wyjasnia pochodzenie `T_XGB(120)`, `Tkor` (`D*(1+coef*(20-T))*5000/(0,981*Strain)`, coef 0,02/0,01), `*FWD` (`4,1497*D^0,7747`), `SCI300_FWD`, `BB_max = 1,24*D0`; struktura MDB (`Stations`, `Drops`, `History`).

**Wplyw na projekt:** zadnych zmian w kodzie (E1 nie ruszono); do decyzji: Q-N3-10 (format docelowy XML), Q-N3-11 (nazwa modelu temperatury). Pozostale pytania z E0 bez zmian.

**STOP — decyzja**: patrz E0 + Q-N3-10, Q-N3-11, Q-N1-7.

## 2026-11-14 — E0 (korekta): format XML = DSN zal. H p. 4.2

**Co ustalono**
- Jacek wskazal `inne\DSN_Zal.H.pdf` (str. 24): docelowy format XML = DSN. Odczytano zal. H (pdftotext): p. 4.2 definiuje `UC` (21 pol: KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1, PREDKOSC, STRAIN_GAUGE, T_DROGI, T_POW, SCI_200, SCI_300, SCI_SUB, D_0, D_200, D_300; atrybuty KOD_ODDZ, ROK), p. 4.1 definiuje `UP` (FWD/KUAB).
- Poprzedni wpis (przeglad `inne\`) blednie przedstawial "UC vs DSN" jako dwa formaty: UC jest formatem DSN; schematy `wdsn` Hellera w `inne\xml\arch\` to inny, starszy format. Skorygowano INWENTARZ (7.1, 7.3) i PROJEKT.
- `UC_Schema.xsd` dostarczy Jacek; w XSD zal. H element glowny to `TSD`, w przykladzie `UC` (rozstrzygnie dostarczony plik).
- Wplyw: Q-N3-10 rozstrzygniete (profil `dsn_h42`, 21 pol); problem Q-N3-2 znika dla tego profilu (potrzebne D_0, D_200, D_300 z d0 i calek P0 do 0,2/0,31 m); nowe pytania Q-N3-12 (SCI_SUB, skala), Q-N3-13 (czy `extended43`), Q-N1-8 (opcjonalny eksport `UP`).
- Wyciag z zalacznika: `docs\notatki_E0\DSN_zal_H_4_1_UP_4_2_UC.txt`.

**STOP — decyzja:** odpowiedzi na pytania z `docs\PROJEKT.md` sekcja 8 (w szczegolnosci Q-N1-1, Q-N1-3, Q-N1-5, Q-N1-6/7, Q-N3-12).

## 2026-11-14 — E0: decyzje Jacka (pytania z PROJEKT.md sekcja 8)

Jacek przeszedl po kolei wszystkie pytania; zapis: `docs\PROJEKT.md` sekcja 8.0. Skrot:
- N1: pelna precyzja `e2a3`; `T_mid` od uzytkownika; srednia zrzutow nieosadczych; tryb legacy `k=0,02` oraz dla autostrad `k=0,01` (`road_type`); wskazniki > 25 C liczone i flagowane; czytnik MDB w E1 (testy bez MDB); bez eksportu `UP` w E1.
- N4: `xfail` dla r par zerowych; antena P043b; sprawdzenie offsetu -4,8 m w E2; najpierw `pairs`, potem E2b `geometry`; lambda 0,11787 z konfiguracji; `calib_interval` + `device`; T12 z Z15 (E2) / z N2.
- N3: profil `dsn_h42`; Hampel jak `tsd_pipeline` po korekcie; pikietaz jak w produkcji; stale XML wymagane w konfiguracji; pliki problemowe flagowane; P0 bez korekty; "D Tkor" = BELLS3_BT (wg Jacka); `SCI_SUB = D_0 - D_900` (do potwierdzenia), skala TSD.
- N2: H v2 + uczciwa dokladnosc; parametry sprzed poprawki OM; `NIGHT` z SW; tylko archiwum OM; u95 z RMSE pory; `CALIB_BOUND_HI`; tylko TN, glebokosc z flaga; cache OM jako sciezka.
- Ogolne: scipy; sciezki + skip; liczby normatywne 5511/36/167/445; rozbieznosci jako notatki.
Uwaga: w pytaniu Q-N4-1 w opisie opcji pomylkowo zapisalem "-1200 m"; chodzi o pary zerowe -200 m / +200 m / permutacja (tresc w PROJEKT.md poprawna).

Otwarte do E2/E3: Q-N4-3 (offset -4,8 m), dostarczenie `UC_Schema.xsd` i potwierdzenie `SCI_SUB`.

## 2026-11-14 — E1: szkielet pakietu + N1 `fwd_tempcorr`

**Co zrobiono**
- Srodowisko `C:\ENV\narzedzia_tsd_fwd` (conda, Python 3.11; numpy 2.4.6, pandas 3.1.1, scipy 1.17.1, xlrd, openpyxl, pyodbc, pytest), `pyproject.toml`, `requirements.txt`, `README.md`.
- Pakiet `src\tsdfwd_tools`: `common` (stale, config YAML ze scisla walidacja kluczy, `rules` z enumem `CorrectionForm` — bez cichego przejscia na postac wykladnicza, `coefficients`, `flags`), `data` (kopia `e2a3_final_k_profile.csv` MD5 `ac5f657401c75b81d67b74ace4fbb7b0`, `tab71.csv`, `PROVENANCE.md`), `fwd` (`io`: XLSX Drops/Stations, MDB przez pyodbc ReadOnly, CSV; `normalize`; `quality`; `tempcorr`; `indices`; `diagnostics`; `pipeline`; `output`), `cli` (`python -m tsdfwd_tools fwd_tempcorr --config ...`, `--dry-run`, `--strict`).
- Decyzje z E0 wdrozone: wspolczynniki pelnej precyzji (`tab71` jako opcja), `T_mid` z kolumny pliku / csv / stala, bez interpolacji, regula `mean_nonseating`, tryb `legacy` (k=0,02 / k=0,01 wg `road_type`), wskazniki > 25 C liczone i flagowane (`INDEX_ABOVE_RANGE`), T < 5 C: korekta bez zastosowania (D*_20 puste, `T_BELOW_5C`), czytnik MDB w E1.
- Kod przeniesiony ze zrodel (naglowki `zrodlo: <sciezka>, stan c67f7fe / data`): `apply_rule`/`apply_f` (rules), `classify_session`/`placeholder_runs` (quality), `load_fwd_values` (normalize), `l20_error`/`band_mean` (diagnostics).

**Co sprawdzono (testy; 67 zielonych: 59 jednostkowych + 8 regresji @reference)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| D0 k 0,0161092 / beta 1,60415 %/C | 0,0161092 / 1,60415 | 0 | OK |
| D300 0,0123428 / 1,21602 | 0,0123428 / 1,21602 | 0 | OK |
| D900 0,00328817 / 0,333874 | 0,00328817 / 0,333874 | 0 | OK |
| CSV pakietu = CSV zrodla | MD5 identyczne | 0 | OK |
| `apply_rule` zrodla vs pakiet (linear/exp, 5 wspolczynnikow, 200 losowych) | zgodne | <= 1e-9 | OK |
| R4 pasma, D0 (lacznie, no_thaw): 15-20 / 20-25 / 25-30 / 30-35 | -0,224 / +0,220 / -1,064 / -3,762 % (n 108/110/49/25) | <= 0,001 pp | OK |
| R4 pasma, D300 | -0,089 / +0,087 / -0,231 / -1,358 % | <= 0,001 pp | OK |
| R4 pasma, D900 | +0,131 / -0,129 / +0,563 / +0,368 % | <= 0,001 pp | OK |
| R4 SCI300 z ugiec skorygowanych (n 108/110/49/24) | -0,683 / +0,671 / -6,021 / -18,525 % | <= 0,001 pp | OK |
| Wzory: D0=200, T=10: A 232,000 / B 234,702; T=5: 248,000 / 254,250; T=30: 168,000 / 170,429 | zgodne | <= 1e-3 | OK |
| SCI300_20 (D0=200, D300=150, T=10): A 64,000 / B 65,239 | zgodne | <= 1e-3 | OK |
| Stacje bez referencji ponizej 10 C | `keep` puste dla T < 10 C | — | OK |
| Odczyt MDB (MOP_Kepinica.mdb, tylko odczyt): 10 stacji, D0 po normalizacji 50 kN, uklad geofonow po x1..x9 | zgodne z obliczeniem recznym | <= 1e-3 | OK |
| Potok XLSX (DK50 50_1M, 121 stacji, T=18 C): D0 st. 1 = 171,087; D0_20 = 176,665 (= exp(0,0160415*2)) | zgodne | <= 1e-3 | OK |
Test `T-N1-07` (estymatory `qp_fit_nd` / `fit_k_profile` na `e2a3_visits`) NIE wykonany — modul `fit` jest poza zakresem E1 (nie byl wymagany w prompcie; zapisane jako opcja, wymaga decyzji).

**Uwagi i decyzje implementacyjne (bez zmiany metod)**
- Kolumny wyjsciowe: `D0..D1800`, `D0_20..D1800_20`, `SCI300_20`, `BDI_20`, `BCI_20` (wielkie litery, w PROJEKT.md bylo `d0..`), plus `flags`, `flags_text`, `t_status`, `t_age_min`, `t_source`.
- `T_ABOVE_RANGE`: korekta wykonana i oznaczona; `T_BELOW_5C`: korekta niewykonana (zgodnie z raportem: stan podloza).
- W przykladowym pliku DK50 temperatura asfaltu jest wpisana raz (18 C) i przenoszona — 99 % stacji ma flage `T_CARRIED`, 50 % `T_STALE` (> 60 min); to oczekiwane zachowanie regul jakosci, nie blad.
- Granice zakresu: dopasowania (modul zrodlowy) `5 <= T < 30`, flagi zakresu waznosci domkniete `[5, 25]` / `[5, 30]` (S-N1-2 ujednolicone w PROJEKT 4.1).
- Integralnosc zrodel: brak plikow zmienionych w `sql_tsd_fwd` i `DOKTORAT` po 2026-11-14 00:00 (`find -newermt`); bazy otwierano `mode=ro` / ODBC `ReadOnly=1`.

**Co zostaje:** modul `fit` (opcjonalnie), instrukcja N1 (E5), E2 (N4: tryb `pairs`).

**STOP — decyzja:** brak decyzji blokujacych E2; do potwierdzenia: czy dodac opcjonalny modul `fit` (wlasne k/beta z danych uzytkownika) do N1 teraz, czy odlozyc.

## 2026-11-14 — E1 (uzupelnienie): modul `fit` (opcjonalny, N1)

**Co zrobiono**
- `fwd/fit.py` (zrodlo: `e2a2b_beta.py` — `_prep_groups`, `qp_fit_nd`, `bootstrap_draws`; `e2a3_beta.py` — `fit_k_profile`; `e2a3i_final.py` — `get_data`, `beta_with_ci`, `run_k_profile`; `e2a3e_range.py` — `seed_for`; stan c67f7fe): log-link (quasi-Poisson) z efektem stalym punkt x miesiac, postac liniowa (WLS + minimalizacja RSS), bootstrap blokowy po dniach (percentyle 2,5/97,5, seed crc32).
- Nowe narzedzie `fwd_fit` (alias `n1fit`): CSV/XLSX z wizytami -> `*_coefficients.csv` (format `e2a3_final_k_profile.csv`) + `*_meta.json`. `configs\fwd_fit_example.yaml`.
- N1: `correction.coefficient_set: file` + `coefficients_file`, `coefficients_scope` — korekta wlasnymi wspolczynnikami (np. z `fwd_fit`).

**Co sprawdzono (T-N1-07; 87 testow zielonych: 59 + 10 jednostkowych fit/N1-file + 18 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| beta_pct, 12 wskaznikow (D0..D1800, SCI300, BDI, BCI), scope lacznie, n = 414 | zgodne z `e2a3_final_k_profile.csv` | max 4,7e-6 %/C (tolerancja 5e-5) | OK |
| k_guide, 12 wskaznikow | zgodne | max 4,3e-8 (tolerancja 3e-6) | OK |
| D0 beta 1,60415 / SCI300 3,24407 / BDI 2,8704 / BCI 1,92233 %/C | 1,60415 / 3,24407 / 2,8704 / 1,92233 | <= 5e-5 | OK |
| przedzial beta D0 (bootstrap 500 replik, seed crc32): [1,51323; 1,72669] | [1,51323; 1,72669] (D0); wszystkie wskazniki: max roznica 0,0023 pp | tolerancja 0,01 pp | OK |
Testy jednostkowe: odtworzenie znanej beta (0,016 i 0,012, efekt grupy), deterministycznosc seedu, za malo danych, filtry zakresu, przekazanie pliku wspolczynnikow do N1 (np. beta 2 %/C, T = 18 C -> exp(0,04)).

**Uwagi:** przedzialy ufnosci odtwarzaja sie dokladnie tylko przy tej samej wersji numpy/scipy (solver `root`); w tescie tolerancja 0,01 pp. Wspolczynniki SCI300/BDI/BCI z `fit` maja charakter diagnostyczny — nie sa uzywane do korekty (zasada metodyczna). Zrodla nie zmienione (kontrola `find -newermt`).

**STOP — decyzja:** brak; nastepny krok E2 (N4, tryb `pairs`).

## 2026-11-14 — E2: N4 `tsd_fwd_compare` (tryb `pairs`)

**Co zrobiono**
- Pakiet `compare\`: `agreement` (mediana ilorazu, SD log-ilorazu, Pearson/Spearman, r i rho w obrebie sesji, CCC Lina, Bland-Altman ilorazu, Deming log-log i liniowy, miary odporne, bootstrap po sesjach), `corrections` (korekta obu stron do 20 C: `none` / `main_after` (wykladnicza beta D0) / `k02`), `uncertainty` (dziki bootstrap klastrowy Webba WCU/WCR, CR2 z dof Satterthwaite, bootstrap sesji, bootstrap sparowany przed/po), `nulls` (kontrola zerowa; roznica prawda - zero ze wspolnym losowaniem sesji), `conditions` (tabela warunkow), `calibration` (mnoznik/afiniczna, ocena z pominieciem sesji), `pipeline`, `output` (CSV, `meta.json`, `report.html`).
- Konfiguracja `config_n4.py` (mapowanie kolumn, warianty korekty, lambda z konfiguracji = 0,11786960, seedy jak w zrodle), CLI `tsd_fwd_compare` / `n4`, `configs\n4_pairs_example.yaml`. Tryb `geometry` odrzucany komunikatem (E2b).
- Kod przeniesiony ze zrodel z naglowkami (`e2b2_agreement.py`, `z15_temp_correction.py`, `e2x_uncertainty_methods.py`, `e2bR9_lustro_warianty.py`, `e2bR9_lustro_warunki.py`, `e2bR9_lustro_kalibracja.py`, `e2b2b_extra.py`; stan c67f7fe).
- Zmiany wzgledem zrodla (bez zmiany metod): ujemne `dt` nie sa gubione (przedzial `<0`; w zrodle 251 par wypadalo z tabeli); warunek "aparat x okres kalibracji" = `device` x `calib_interval` (zrodlo: `tsd_year`; mozliwe przez `group_by`); CV(D0) odcinka domyslnie na wartosciach par (jak w zrodle, odtwarza raport), opcja `cv_unit: stations` (unikalne stacje); pary z T12 poza 5-30 C lub bez T12 sa flagowane w `pairs_corrected.csv` i `meta.json` (mnoznik liczony takze dla nich - zastrzezenie raportu 7.3).

**Co sprawdzono (124 testy zielone + 2 `xfail`; w tym 18 testow regresji N4 na danych referencyjnych, tylko odczyt)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| main_after: mediana ilorazu 1,61584 [1,5382; 1,68335]; 5511 par; 36 sesji | 1,615841 [1,538195; 1,683348] | <= 1e-5 | OK |
| main_after: SD log 0,321151; r 0,659578; rho 0,580602; CCC 0,346871 | identyczne | <= 1e-6 | OK |
| main_after: Deming log-log 0,958655 / 0,642298; liniowy 1,41861 / 8,16356 | 0,958655 / 0,642298; 1,418613 / 8,163564 | <= 1e-5 | OK |
| main_before: 1,40644; SD 0,342756; r 0,611999; CCC 0,424149; Deming 1,05235 / 0,106303 | identyczne | <= 1e-5 | OK |
| r w obrebie sesji W5: none / main_after / k02 (lustro) 0,407298 / 0,403905 / 0,402391 | 0,407041 / 0,403624 / 0,402107 | <= 3e-4 (tol. 5e-4) | OK |
| pary zerowe, mediana ilorazu 1,59507 / 1,61026 / 1,59451 | 1,59522 / 1,60978 / 1,59316 | <= 1,4e-3 (tol. 2e-3) | OK |
| pary zerowe, r globalne 0,517 / 0,525 / 0,408 | 0,5169 / 0,5242 / 0,4076 | <= 1e-3 | OK |
| pary zerowe, r w obrebie sesji 0,155242 / 0,13524 / 0,0962062 | 0,15527 / 0,13446 / 0,09581 | <= 8e-4 | OK (patrz uwaga) |
| niepewnosc W3: M0 [1,53804; 1,65362]; WCU [1,53793; 1,6602]; WCR p 0,9393; CR2 [1,53689; 1,66116], dof 20,5 | identyczne (9999 replik) | <= 1e-5 | OK |
| grupy aparat x rok (Tab. 6.4): mediany przed i po, liczby sesji | identyczne | <= 1e-4 | OK |
| Q1: SD log po-przed -0,0216 [-0,0366; -0,0064]; Q2: rozstep -0,2069, SD median grup -0,0854 | identyczne | <= 2e-4 | OK |
| warunki: dt 0-1 r 0,857391 (n 119); 2-30 0,322221; >30 0,366773; GoF >= 0,8 0,814548; przeciecie 0,83682 (n 99) | 0,85739; 0,32216; 0,36609; 0,81461; 0,83682 (99) | <= 7e-4 (tol. 2e-3); n identyczne | OK |
| kalibracja mnoznika W5 (k02): a 1,4222; MAE 27,6747 / LOSO 27,7366; mediana abs log 0,227208 / 0,227888 | 1,42212; 27,6777 / 27,7397; 0,22740 / 0,22815 | <= 3e-3 (tol. 0,01) | OK |
| lambda d0 0,11787 (sigma_TSD 0,296408; sigma_FWD 0,101763) | z konfiguracji 0,1178696 | <= 1e-5 | OK |

**Uwaga - Q-N4-1 wyjasnione:** rozbieznosc z E0 dotyczyla porownania z `e2b2b_null_test_paired.csv` (pary BEZ korekty temperaturowej, inna definicja r w obrebie sesji). N4 odtwarza wartosci raportu (lustro P071: 0,155 / 0,135 / 0,096) z `e2b2_null_values` + Z15 przy korekcie `main_after`; wartosci e2b2b odtwarza tylko dla +200 m (0,1411); dla -200 m i permutacji nie (0,157 / 0,090 vs 0,118 / 0,023) - te dwa przypadki zostaja `xfail` (informacyjnie).
**Uwaga:** `C:\WORK\DOKTORAT\.git\FETCH_HEAD` ma czas modyfikacji 2026-11-14 09:53 - to automatyczny `git fetch` srodowiska (nie uruchamialem git w tym katalogu); pliki zrodlowe `DOKTORAT` i `sql_tsd_fwd` nie zostaly zmienione (kontrola `find -newermt`).
**Czego tryb `pairs` nie robi:** nie buduje par z geometrii (E2b), nie liczy lambdy z powtorzen (Q-N4-5), nie przelicza krzywizn SCI300/BDI/BCI (raport 6.3: tylko orientacyjnie) i nie wybiera rekordu TSD wg wartosci FWD.

**STOP - decyzja:** brak decyzji blokujacych E3; Q-N4-3 (offset -4,8 m) dopiero przy trybie `geometry` (E2b).

## 2026-11-14 — E3: N3 `tsd_network` (TSD na sieci + XML DSN)

**Co zrobiono**
- Pakiet `tsd\`: `io` (odczyt B_1510off `*.raw.sup.txt`: sekcje Headers/Parameters/Data, znak D, GPS, data z nazwy pliku, flagi pliku), `integrals` (calki P0: PCHIP zwektoryzowany po wierszach, siatka 1 mm, trapezy; wariant T), `tempcorr` (korekta d0 wykladnicza beta D0 = 1,60415 %/C, zakres T12 5-30 C; mnoznik 1,62 opcjonalnie), `filters` (jedna implementacja Hampela jak `tsd_pipeline`: MAD okna, prog > 0, okno w metrach), `window` (mediany w oknie +-5 m — mediana calek; agregacja 50/100 m), `qc` (test zyroskop-GPS z `qc_gyro_gps`), `uc_export` (XML DSN `UC`, zal. H p. 4.2, + kontrola struktury), `pipeline`, `output`, CLI `tsd_network` / `n3`, `configs\n3_example.yaml`.
- Kolejnosc operacji (decyzje Jacka): korekta d0 do 20 C (T12 z N2/modelu; nigdy pirometr) -> Hampel na d0_20 z odrzutem calej czaszy (d0 i calki) -> mediany +-5 m -> agregacja 50/100 m -> XML. Calki P0 bez korekty temperaturowej (flaga `P0_UNCORRECTED`). Skala TSD.
- XML `dsn_h42` (21 pol): D_0 = d0_20 (mediana), D_200 = D_0 - P0(0,20), D_300 = D_0 - P0(0,30), SCI_200 = P0(0,20), SCI_300 = P0(0,30), SCI_SUB = P0(0,90) (= D_0 - D_900); IRI_1/PROFIL_1 puste; KOD_ODDZ, ROK, DROGA, JEZDNIA, PAS, km_start wymagane w konfiguracji; uklad pliku jak `tsd_to_xml.py` (UTF-8 bez BOM, LF, puste elementy zamiast nan).
- Flagi N3: brak/niska/wysoka T12, d0 niewazne, outlier Hampela, brak nachylenia, calki <= 0, za malo wierszy w oknie, udzial GoF < 50 %, GPS, plik nie-B_1510off / brak kanalu / podejrzana skala / rok < 2024, test zyroskop-GPS.

**Co sprawdzono (150 testow zielonych + 2 `xfail` z E2; 13 nowych regresji i 21 jednostkowych N3)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| calki P0 z 9 nachylen (1308 wierszy `e2a2_slopes.csv`) vs `e2a2_autc_var.csv`: p0_a031/a061/a091/a0361/a6191 oraz t_* | zgodne | max 8e-4 um (zaokraglenie nachylen w CSV do 6 cyfr; tol. 2e-3) | OK |
| wiersz kontrolny 1a, 2025-09-04, pkt 0: p0_a031 21,6023; a061 39,0758; a091 41,5524; a0361 17,4735; a6191 2,47669; t_a031 22,6437; t_a061 39,7148 | zgodne | <= 1e-3 | OK |
| mediany: p0_a031 39,51; t_a031 35,69 | zgodne | <= 0,01 | OK |
| zwektoryzowany PCHIP vs `scipy.interpolate.PchipInterpolator` (gesta siatka 1 mm) | zgodne | <= 4e-13 | OK |
| profil liniowy a*(x-x0): P0(x1) = a*(x1^2/2 - x0*x1) | zgodne | <= 1e-6 | OK |
| Hampel vs kopia `_hampel_col` z `tsd_pipeline` (600 punktow, outliery i NaN) | identyczna maska | 0 | OK |
| parser `T4202008060001.raw.sup.txt`: 6103 wiersze; wiersz 1: Chainage 0, D0 -8342 (d0 8342), Slope 0.110 1453,5559, GoF 0,23790418, Lat 50,091676027, Lon 19,813605221 | zgodne | 0 | OK |
| parser vs `b1510off_measurements` (plik 2025-04-23 nr 12, 1698 wierszy: pikietaz, d0, 9 nachylen, GoF, predkosc, temperatury) | identyczne | 0 | OK |
| okno pary 5288 (10 wierszy B_1510off): mediana d0 153, n 8, mediana GoF 0,621656 (`e2b2_tsd_values.csv`) | 153,0; n 8; 0,621656 | <= 1e-6 | OK |
| test zyroskop-GPS, plik 2025-04-23 nr 12 (1698 wierszy) | werdykt OK | — | OK |
| XML dsn_h42 z prawdziwego pliku 2025 (169 rekordow co 10 m): struktura, kolejnosc 21 pol, formaty, DYSTANS krok 10, KM monotoniczne | zgodny | — | OK |
Calki P0 z B_1510off dla `a031_w5` pary 5288 (30,43) NIE odtwarzaja `e2b2_tsd_values.csv` (28,74): tam liczono je z nachylen eksportu pgc (inny zestaw zer) — to nie blad, lecz inne zrodlo nachylen (Q-N3-14).

**Decyzje implementacyjne (bez zmiany metod) i uwagi**
- KM: eksport B_1510off nie ma markerow `Event`, `DateTime` ani IRI — KM = `km_start` + znak * pikietaz/1000 (konfiguracja); data z nazwy pliku; godzina z `GPS time` (Q-N3-15). Przesuniecie polozenia ugiec (`position_offset_m`) domyslnie 0 — konwencja znaku -4,8 m nadal nierozstrzygnieta (Q-N4-3).
- D_300 liczone dla 0,30 m (nie 0,31 m, polozenia czujnika) — Q-N3-16. SCI_SUB = P0(0,90) wg wstepnej definicji D0 - D900 (do potwierdzenia po `UC_Schema.xsd`).
- Struktura XML sprawdzana wzgledem zalacznika H i ukladu `tsd_to_xml.py`; walidacja XSD po dostarczeniu `UC_Schema.xsd` (w XSD zalacznika element glowny to `TSD`, w przykladzie `UC`).
- Zrodla niezmienione (kontrola `find -newermt`; pliki B_1510off tylko do odczytu).

**Co zostaje:** E4 (N2: temperatura warstwy), E2b (tryb `geometry` N4), E5 (instrukcje); do ustalenia: Q-N3-14, Q-N3-15, Q-N3-16, `UC_Schema.xsd`.

**STOP — decyzja:** brak decyzji blokujacych E4.

## 2026-11-14 — E4: N2 `layer_temp` (temperatura warstwy asfaltowej)

**Co zrobiono**
- Pakiet `layer_temp\`: `constants`, `params` (+ `data\params_TN.json`, hash SHA-256 sekcji `parameters`: 36780ba8...f4d04, test dryfu), `meteo` (klient Open-Meteo na `urllib`, `om_utc_to_local`, `MeteoStore` z cache parquet/csv+json, plan okien), `frame` (siatka 10 min, promieniowanie dlugofalowe, cechy dolnego BC, korekta IR do "masy", SW_ma6), `solver` (1-D przewodzenie + bilans energii powierzchni, siatka 1 cm 0-50 cm, rozbieg 288 krokow), `calibrate` (kalibracja jednorazowa a_sw: brentq, bramka 1 C, granice 0,03-1,0), `predict` (`CellDay`, `predict_at`, `layer_temperature`, `run_survey` z grupowaniem po komorce i dobie), `bells3` (komparator opcjonalny, tylko wspolczynniki oryginalne), `uncertainty`, `flags` (15 flag `LayerFlag`), `pipeline`, `output`; `common\config_n2.py`, CLI `layer_temp` / `n2`, `configs\n2_example.yaml`.
- Parametry zamrozone: klasa terenu otwartego (stacja TN), wersja sprzed poprawki czasu OM (Q-N2-2, domyslnie), alpha 1,11809e-6 m2/s, EB (h0 13,7037; h1 0,8636; c_vol 2,4917e6), dolny BC t50 (OLS: doy sin/cos, MA7, MA30), korekta IR (beta_ir, 5 skladnikow). Zrodla: E2-T01/T05/T07 projektu temp_model, replika z audytu E0.
- Decyzje implementacyjne bez zmiany metody: (1) klient HTTP na `urllib` zamiast `requests` (mniej zaleznosci; ten sam adres, parametry i zachowanie: `timezone=UTC`, `wind_speed_unit=ms`, 6 zmiennych, retry 429); (2) zapytanie konczy sie dniem pomiaru + 1 — ogon po 23:00 jest pokryty danymi (referencyjny cache konczy sie dniem pomiaru; tam chwile po 23:00 dostaja flage `TAIL_EXTRAPOLATED`); (3) cache zapisywany jako CSV+JSON (bez pyarrow), cache referencyjny (parquet) czytany — dodatek `parquet` w `pyproject.toml`; (4) symulacja jest przyczynowa, wiec jedna ramka i symulacje graniczne (a_sw = 0,03 i 1,0) obsluguja wszystkie chwile tej samej komorki i doby (549 obserwacji w 16 s); (5) wynik zawiera kolumne `t12_c` (dla 12 cm) i przepisywane kolumny (`passthrough`, np. `chainage_m`), wiec jest wejsciem temperatury warstwy dla N3.
- Odpowiedzi na Q-N2-1..9 (przyjete domyslne, do wgladu Jacka): H v2 jako test regresji z uczciwa nota o dokladnosci na zbiorze C (2,73 C) w meta wyniku; pre-omfix; NIGHT = SW_ma6 < 5 W/m2 (jak w zrodle: rolling 36, min_periods 18); tylko archiwum (dane z ostatnich ~5 dni ostrzezenie w logu); u95 = 2*RMSE wg pory doby, nie mniej niz 2,2 C (heurystyka, tak opisana); a_sw <= 1 jako flaga `CALIB_BOUND_HI`; klasa zacieniona pominieta (flaga zarezerwowana, nie wykrywana); glebokosc poza 10/12 cm z flaga `DEPTH_NOT_VALIDATED`; cache testowy czytany z `doktorat_root` (bez kopiowania).

**Co sprawdzono (187 testow zielonych + 2 `xfail` z E2; 29 jednostkowych i 8 regresji N2)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T-N2-01 zbior H v2 (549 obs., 226 sesji), 12 cm: RMSE 1,7486 / MAE 1,4039 / bias +0,2653 | 1,7488 / 1,4042 / +0,2649 | +0,0002 / +0,0003 / -0,0004 (tol. 0,001; to samo co replika zrodlowa) | OK |
| T-N2-02 flagi kalibracji: ok 294, bound_hi 244, gate 11, bound_lo 0 | 294 / 244 / 11 / 0 | 0 | OK |
| T-N2-03 po obserwacji vs `phys_single_masa` (`Z14c_candidates.parquet`) | 544/549 zgodne < 1e-6 C; 5 obs. po 23:00 rozni sie max 0,182 C (flaga `TAIL_EXTRAPOLATED` ustawiona dokladnie na tych 5); flaga i a_sw zgodne poza ogonem | <= 0,2 C wg opisu | OK |
| T-N2-04 fizyka bez kalibracji 2,0872 / 1,6974 / +0,9455; BELLS3 2,4065 / 1,8160 / -0,3432 | 2,0872 / 1,6974 / +0,9455; 2,4065 / 1,8160 / -0,3432 | BELLS3 po obserwacji identyczny ze zrodlem < 1e-9 | OK |
| T-N2-05 RMSE wg pory (n 49 / 226 / 237 / 37): 2,167 / 1,378 / 1,889 / 2,167 | 2,167 / 1,378 / 1,889 / 2,168 | <= 0,001 (tol. 0,005) | OK |
| SW_ma6 vs kolumna `sw_ma6` w `Z14c_candidates` | identyczne | < 1e-6 | OK |
| T-N2-10 (Z15, 200 par x 2 strony FWD/TSD): T12 po kalibracji, bez kalibracji, BELLS3, a_sw vs `Z15_temperatury_par.csv` | zgodne | < 1e-6 poza ogonem (<= 0,25 C) | OK |
| T-N2-06 solver: stan ustalony (profil liniowy, bilans energii powierzchni), round-trip kalibracji (a* = 0,55 -> a = 0,55) | zgodne | bilans < 1e-3 W/m2; a +- 2e-3 | OK |
| T-N2-07 czas/DST: godzina podwojna (jesien), luka wiosenna, offsety lato/zima | zgodne | dokladnie | OK |
| T-N2-08 klient: parametry zapytania, okno [start-1 d, end+1 d], retry 429 (5 prob), blad 500, tryb offline bez zapytan, cache | zgodne | dokladnie | OK |
| T-N2-09 hash parametrow | zgodny; zmiana parametru zmienia hash | dokladnie | OK |
| kontrola zywa: jedno zapytanie do Open-Meteo (okno 2021-09-10..14, komorka 50,20; 19,15) vs zapisany cache referencyjny, 6 zmiennych x 120 godzin | identyczne | 0 | OK |
Test T-N2-01 to powtarzalnosc na zbiorze eksploracyjnym H, nie deklaracja dokladnosci produktu (zbior niezalezny C: RMSE 2,73 [2,44; 2,98]); 44 % obserwacji H (244 z 549) trafia na gorna granice a_sw (`CALIB_BOUND_HI`), a 36 chwil jest oznaczonych `NIGHT`, gdy kalibracja do pirometru nie ma sygnalu slonecznego.

**Uwagi**
- Zrodla w `C:\WORK\DOKTORAT\temp_model` bez zmian (kontrola `find -newermt`). W `C:\projects\sql_tsd_fwd` sa pliki nowsze niz 2026-11-13 (`bak\e2bR9_lustro_*`, `logi\E2b\e2bR9_lustro_*`, `plik_wymiany_informacji.md`) — zmienione poza tym narzedziem (inne prace w tamtym projekcie); narzedzie nic tam nie zapisuje (odczyt: `tabele\z14lite_fwd_walidacja_v3.csv`).
- Wyniki w nocy: kalibracja do pirometru jest nieidentyfikowalna (bramka lub granica); flaga `NIGHT` mowi, ze `a_sw` nie ma tu znaczenia i wynik jest bliski fizyce bez kalibracji.
- Blad w README (sekwencje `\n`/`\f` w sciezce komendy `fwd_fit`) poprawiony przy okazji.

**Co zostaje:** E5 (instrukcje INSTRUKCJA_N1..N4.md), E2b (tryb `geometry` N4); do ustalenia: Q-N3-14, Q-N3-15, Q-N3-16, `UC_Schema.xsd`, Q-N4-3.

**STOP — decyzja:** brak decyzji blokujacych E5.

## 2026-11-14 — E5: instrukcje dla inzynierow + rozstrzygniecie Q-N4-3

**Co zrobiono**
- `docs\INSTRUKCJA_N1.md`, `INSTRUKCJA_N2.md`, `INSTRUKCJA_N3.md`, `INSTRUKCJA_N4.md`: do czego sluzy narzedzie, co trzeba miec, uruchomienie, najwazniejsze ustawienia, wyniki, flagi (z opisem "co robic"), ograniczenia. N1 zawiera opis `fwd_fit`; N2: uczciwa dokladnosc (H 1,75 C eksploracyjny vs C 2,73 C niezalezny), znaczenie `NIGHT`/`CALIB_BOUND_HI` (44 % w zbiorze odniesienia), u95 jako heurystyka, tryb offline i jedyne polaczenie sieciowe (archiwum Open-Meteo), teren zacieniony nieobslugiwany; N3: polozenie ugiec, status XML bez walidacji XSD, definicje robocze (`SCI_SUB`, `D_300`); N4: tylko `pairs`, zasada pary tylko geometrycznej, jak czytac kontrole zerowe.
- Q-N4-3 rozstrzygniete (Jacek, 2026-11-14; patrz PROJEKT 8.2): -4,8 m jest wliczone w `tsd_sref` (`e1_sref.py`, `corrected_xy`), wiec okna W5 ja zawieraja; konwencja lagu: pozycja = pikietaz - lag = pikietaz + 4,8 m. N3: `position_offset_m` domyslnie 0 (decyzja Jacka), opcja w konfiguracji.
- **Zmiana w kodzie N3 (znak):** `pos_m = pikietaz - position_offset_m` (wczesniej `+`), zeby wartosc -4,8 z projektu znaczyla to samo co w calym projekcie. Przy domyslnym 0 wyniki bez zmian. Dodany test `test_n3_position_offset_follows_lag_convention`.

**Co sprawdzono**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| kazda flaga z `Flag`, `TsdFlag`, `LayerFlag` opisana w odpowiedniej instrukcji | wszystkie wymienione | 0 brakujacych | OK |
| kazdy klucz konfiguracji cytowany w instrukcjach istnieje w dataclasses konfiguracji | 47 kluczy, wszystkie istnieja (3 "niezgodne" to nazwy plikow `layer_temp.csv`, `calibration.csv`, `conditions.csv`) | 0 | OK |
| opisane zachowania sprawdzone w kodzie (brak meteo -> wynik pusty z flagami, `fwd_fit` za malo danych -> wiersz z adnotacja, `mode: geometry` -> blad) | zgodne po poprawce dwoch opisow | 2 poprawione w trakcie | OK |
| N3: `pos_m - chainage_m` dla `position_offset_m` 0 i -4,8 | 0 i +4,8 | < 1e-9 | OK |

**Uwagi**
- Instrukcje opisuja wylacznie to, co jest zaimplementowane; nie dodaja nowych metod ani parametrow. Przyklady z liczbami (RMSE, beta, lambda) pochodza z raportu i dziennika.
- Walidacja XML wzgledem `UC_Schema.xsd` pozostaje otwarta (dostarczy Jacek za kilka dni; do tego czasu XML tylko wg zalacznika H p. 4.2 i kontroli struktury).

**Co zostaje:** E2b (tryb `geometry` N4: odcinki, regula anteny P043b, `s_ref`, pary zerowe); do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych E2b.

## 2026-11-14 — E2b: N4 tryb `geometry` (os pasa, polozenie plyty FWD, pary geometryczne i zerowe)

**Co zrobiono**
- `compare\geo.py` (EPSG:2180, lag polozenia, korytarze, rzut na korytarz, ciagi, os z przejazdow TSD), `comparewd_position.py` (K1-K4: rzut anteny, kierunek sesji z danych, regula anteny jako jawna tabela, ciagi i regresja dystansomierza, `sigma_long`), `compare\pairing.py` (kandydaci na pary, okna +-1/2,5/5 m, warstwy A/B/C/X, pary zerowe, wartosci okien), `compare\geometry_pipeline.py` (potok trybu), integracja z `run_n4` (`mode: geometry`), `configs
4_geometry_example.yaml`. Nowe wyjscia: `geometry_pairs.csv`, `fwd_plate_positions.csv`, `tsd_passes.csv`, `corridors.csv`, `geometry_null_pairs.csv`, `fwd_sessions.csv`, `fwd_session_runs.csv`.
- Wejscie trybu: wiersze TSD (np. `*_rows.csv` z N3: surowy `chainage_m`, `lat`, `lon`, `d0`, `gof`, `t12_c`) i stacje FWD (CSV: `station_id`, `session_id`, `station_m`, `latitude`, `longitude`, `device`, `date`, `D0`, `t_mid_c`; D0 i T z N1). Wynik wchodzi do tej samej analizy co tryb `pairs`.
- Q-N4-3 zastosowane: lag -4,8 m stosowany dokladnie raz (przy budowie polozenia TSD; konwencja `pozycja = pikietaz - lag`); N4 nie przyjmuje pikietazu po przesunieciu. Q-N4-2: regula anteny P043b jako domyslna tabela, nadpisywalna w konfiguracji (jedna regula zamiast dwoch rozbieznych w zrodle). Q-N4-4: tryb `geometry` zrobiony po zatwierdzeniu E2.
- Decyzje implementacyjne bez zmiany metod: (1) wartosci okien TSD liczone po `s_ref` (jedna definicja, S-N4-4, decyzja E0), a nie po zakresie `tsd_id` (patrz nizej); (2) kurs stacji FWD, gdy brak kolumny `heading_deg`, liczony z kolejnosci stacji w sesji jak `compute_headings` w bazie; (3) data przejazdu TSD z `geometry.tsd_runs_csv`, nazwy pliku (`T4RRRRMMDDnnnn`) albo `geometry.date_override` — brak daty to blad; przedzial kalibracji TSD z konfigurowalnej tabeli dat (domyslnie K2024-03-01, K2025-05-27, K2026-05-19); (4) filtr par jak w tabeli glownej raportu: warstwy A+B, ten sam rok, wazne d0 po obu stronach.

**Co sprawdzono (220 testow zielonych + 2 `xfail` z E2; nowe: 14 geo, 9 stacje/pary, 5 potok geometry, 4 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T-N4-12 testy syntetyczne zrodla (`test_e1.py` T1-T7, `test_e2b1.py` T1-T5, T11): poludnik srodkowy, symetria, skala, zbieznosc, lag, plyta, rzut i znak `lateral`, ciagi, korytarze, wygladzenie osi, regresja dystansomierza, pary zerowe | zgodne | wg zrodla | OK |
| T-N4-13 polozenie plyty FWD, 46826 stacji `odcinki` vs `fwd_plate_position_e2b` (K1-K4): `lane_match`, `era`, `pos_source`, `direction`, `corridor_id`, `run_id` | 100 % zgodne | 0 | OK |
| T-N4-13 `s_ant`, `lat_ant`, `s_plate_gps`, `s_dmi`, `s_fwd`, `residual_gps_m`, `sigma_a` | max roznica 2,9e-10 m | tol. 1e-6 | OK |
| T-N4-13 `sigma_long` | max roznica 2,0e-6 m (zaokraglenie sigma_era w tabeli) | tol. 1e-4 | OK |
| T-N4-14 kandydaci na pary, korytarze 0..29 (5632 pary = prefiks `pair_id`): ten sam zestaw i kolejnosc, `win1/2_5/5_n`, zakresy `tsd_id`, `layer`, `dt_days`, `same_year`, `calib_interval` | 100 % zgodne | 0 | OK |
| T-N4-14 `s_fwd`, `ds`, `dlat`, `win5_gof05_share`, `win5_lat_tsd_median`, `v_med`; `sigma_long_fwd` | max 8,7e-11; `sigma_long_fwd` 2,0e-6 | tol. 1e-6 / 1e-4 | OK |
| T-N4-14 pary zerowe (+-200 m, permutacja z seedem 20261017): 16659 wierszy | liczba, `center_s` (max 8,7e-11), `win5_n`, zakresy `tsd_id` zgodne | 0 | OK |
| T-N4-15 przypisanie wierszy TSD (3 pliki; 15 plikow sprawdzonych recznie) do referencyjnych korytarzy vs `tsd_sref` (`prepare_run` + `assign_run`): korytarz | 99,986-100 % wierszy w pasie | wiersze graniczne | OK |
| T-N4-15 `s_ref_gps` / `lateral_m` | max 0,010 m / 0,0011 m | wspolrzedne korytarzy w bazie zapisane z dokladnoscia ~mm | OK |
| T-N4-16 mediana d0 w oknie W5 vs `d0_tsd` Z15 (pary korytarzy 0..29: 335; 0..80: 2895) | 334/335 oraz 2888/2895 zgodnych < 1e-6; obecnosc wartosci zgodna we wszystkich | 7 par roznych (maks. 30,5 um), wyjasnione definicja okna (S-N4-4) | OK (wyjasnione) |

**Czego tryb `geometry` NIE robi (swiadomie, patrz `docs\INSTRUKCJA_N4.md`)**
- Nie wykrywa wspolnych odcinkow wg Tab. 3.2 (`detect_sections`, raport "linia do linii", flaga `in_stage1`) — pary nie zaleza od odcinkow (wynikaja z korytarzy i roku); odcinki to osobny krok kontrolny, jeszcze niezaimplementowany.
- `s_ref` = `s_ref_gps`: bez wyrownania profilem (wymaga kanalu `profile1`, ktorego nie ma eksport B_1510off), bez scalania duplikatow pasa i bez drogomierza zakotwiczonego w strefach zlego GPS. Os z przejazdow TSD nie jest identyczna z osia z calej bazy (zalezy od zestawu przejazdow); dla identycznosci mozna podac gotowa os (`geometry.corridors_csv`).
- Nie liczy lambdy (Q-N4-5) ani nie wybiera rekordu TSD wedlug wartosci.

**Uwagi**
- Zrodla w `C:\projects\sql_tsd_fwd` bez zmian (kontrola `find -newer`; zadnego `__pycache__`). W `C:\WORK\DOKTORAT\.git` zmienily sie pliki `FETCH_HEAD`/`refs/remotes/origin/HEAD` — nie przez to narzedzie (nie wykonuje zadnych komend git w tamtym katalogu).
- Roznice 7 z 2895 par (T-N4-16): zrodlowy `e2b2_values` bral wiersze z zakresu `tsd_id` min..max okna, w ktorym moga byc tez wiersze spoza okna odleglosciowego (np. przerwa w przejezdzie); tu okno to wiersze z |s_ref - s_fwd| <= 5 m.

**Co zostaje:** E2c (opcjonalnie): `detect_sections` + raport "linia do linii", wyrownanie profilem i scalanie duplikatow pasa (dla danych z kanalem `profile1`), estymator lambdy (Q-N4-5); do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych; do rozstrzygniecia zakres E2c (patrz wyzej).

## 2026-11-14 — E2c: N4 odcinki wspolne (Tab. 3.2) i raport przegladu „linia do linii”

**Co zrobiono**
- `compare\sections.py`: `detect_sections` (kryteria Tab. 3.2: ten sam rok i odstep <= 400 dni, >= 5 stacji w promieniu 8 m, pokrycie >= 30 % wzgledem stacji w obwiedni TSD, zakres pikietazu >= 500 m, |Spearman(station_m, pikietaz)| >= 0,80, kierunek wg kursow 30/150 st., klasa pasa 0,75/2,0 m) z wejsciem w DataFrame'ach i zapytaniami do drzewa KD wektorowo (te same wartosci co petla po stacjach). Licznik odrzuconych par wg przyczyny (rok, za malo stacji, pokrycie, krotki zakres, monotonicznosc, niejednoznaczny kierunek).
- `compare\section_report.py`: raport `section_review.html` (SVG, bez zaleznosci graficznych): slad GPS TSD i stacje FWD, wykres station_m - pikietaz z regresja, „linia do linii” (d0 TSD gesta linia i D0 FWD punkty na wspolnym pikietazu). Decyzje przegladu wracaja plikiem `geometry.sections.review_csv` (session_id, run_id, status).
- Integracja z trybem `geometry`: `sections.csv`, kolumny par `in_section`, `section_id`, `section_lane`, `section_direction`, `section_status`, opcjonalny filtr `geometry.sections.require_section` (pary z odcinka, bez odrzuconych). Domyslnie odcinki NIE filtruja par (zgodnie ze zrodlem: pary wynikaja z korytarza i roku, odcinki sa kontrola/przegladem).
- Decyzja bez zmiany metody: brak `matplotlib` w srodowisku — raport rysowany wlasnym SVG zamiast instalowania pakietow; brak kursu TSD/stacji uzupelniany z kolejnosci punktow (jak `compute_headings` w bazie). Kryteria przegladu recznego nie dostaly zadnych nowych progow (raport pokazuje, nie ocenia).

**Co sprawdzono (przebieg pelny: patrz wynik testow; nowe: 9 jednostkowych, 1 integracyjny, 1 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T-N4-11 `detect_sections` na calej bazie v4 (251 sesji FWD x 239 plikow TSD z GPS) vs `tsd_fwd_sections`: liczba sekcji | 445 = 445, te same pary (sesja, plik) | 0 | OK |
| T-N4-11 kierunek, klasa pasa, `fwd_matched`, `fwd_total`, `fwd_in_overlap` | 100 % zgodne | 0 | OK |
| T-N4-11 Spearman, pokrycie (oba), zakresy `station_m` i pikietazu, mediana odleglosci poprzecznej, srednia roznica kursow | max roznica < 1e-9 (w skrypcie kontrolnym dokladnie 0) | tol. 1e-9 | OK |
| T-N4-11 przeglad reczny: 167 `confirmed` vs sekcje kierunku same i pasa same/adjacent | 167 = 167 (87 same/same + 80 same/adjacent), recall 167/167, precyzja 167/167 | 0 | OK |
| odrzucone pary w v4 wg przyczyny | rok 3776, za malo stacji 60, pokrycie 27, krotki zakres 13, monotonicznosc 0 | — | informacyjnie |
| testy syntetyczne: kierunek przeciwny, klasy pasa 0,5/1,2/5 m, odrzucenia wg przyczyny, pokrycie w obwiedni, raport SVG, integracja (filtr, review, wylaczenie) | zgodne | wg zalozen | OK |

**Uwagi**
- Odcinki liczone sa na surowym GPS (antena FWD, GPS wiersza TSD bez lagu), jak w zrodle; plaskie przyblizenie 111320 m/stopien tez jak w zrodle.
- 278 z 445 sekcji ma pas `far` albo kierunek przeciwny — w przegladzie recznym nie byly rozpatrywane (zrodlo: `lane-filter same,adjacent`), tu sa w `sections.csv` z kolumna `lane_class`/`direction`.

**Co zostaje:** wyrownanie profilem i scalanie duplikatow pasa (dla danych z kanalem `profile1`), estymator lambdy (Q-N4-5); do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych.

## 2026-11-14 — E2d: N4 estymator lambdy (Q-N4-5)

**Co zrobiono**
- `compare\lambda_est.py`: sigma_TSD z par przejazdow w tych samych binach 10 m po `s_ref` (pokrycie >= 5 wierszy, |dt| <= 1 d, poza betonem; 1,4826 MAD(ln d_i − ln d_j) / sqrt(2)), sigma_FWD z powtorzen stacji FWD miedzy sesjami tego samego aparatu w oknach 10 m (od 2024 r., |dT powierzchni| < 3 C, poza betonem; `sigma_within` = 1,4826 MAD(D − mu_ij) / sqrt(2)), lambda = sigma_FWD² / sigma_TSD². Port z `e2b2_values` (lambda TSD), `e1_sref` (biny i pary przejsc), `e12_noise` (powtarzalnosc FWD, `sigma_decomp`).
- Integracja z trybem `geometry`: `geometry.lambda_est` (`enabled`, `apply`, progi jak w zrodle), plik `lambda_estimate.csv`, pola `lambda_d0_used` i `lambda_source` w `meta.json`. Domyslnie lambda zostaje z `measures.lambda_d0` (0,11787): oszacowanie jest tylko raportowane, a `apply: true` uzywa go w analizie. Nowe opcjonalne kolumny wejscia: `t_surface` w stacjach FWD (wymagana przy estymatorze), `time` i `concrete` w wierszach TSD.
- Decyzje bez zmiany metody: (1) czas przejazdu bez kolumny `time` to poludnie daty — wtedy warunek |dt| <= 1 dzien oznacza ta sama lub sasiednia date (na bazie referencyjnej daje to 2047 par zamiast 2015 i sigma_TSD 0,29836 zamiast 0,29641 — dlatego estymator przyjmuje czas wiersza); (2) tryb `pairs` nie ma estymatora (brak danych powtorzen) — lambda z konfiguracji; (3) brak progu minimalnej liczby powtorzen: n par jest raportowane, a przy braku powtorzen wynik jest NaN (przy `apply` blad z komunikatem).

**Co sprawdzono (241 testow zielonych + 2 `xfail`; nowe: 9 jednostkowych, 1 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T-N4-09 sigma_FWD (`e12_lambda`, ge2024, 10 m) i liczba par | 0,101763 / 128 par (13 par sesji) | < 1e-6 | OK |
| T-N4-09 sigma_TSD (`e2b2_lambda`, d0) i liczba par | 0,296408 / 2015 par (czas biny z `tsd_bin_stats`, pliki B_1510off ok) | < 1e-6 | OK |
| T-N4-09 mediana roznicy log (TSD) | -0,075508 | < 1e-6 | OK |
| T-N4-09 lambda d0 | 0,11786960020790811 | 0 (dokladnie wartosc stala w `config_n4.LAMBDA_D0`) | OK |
| liczba wierszy w binie (`n`) vs `tsd_bin_stats` (690582 biny z `tsd_sref`) | 99,88 % zgodnych, brak binow tylko po jednej stronie | 0,12 % binow o `n` innym o kilka wierszy (nie wplywa na pary) | OK |
| syntetyczne: sigma_TSD 0,3, sigma_FWD 0,1 -> lambda 0,111; odrzucenia (dzien, beton, pokrycie, rok FWD, temperatura, aparat, jedna sesja) | zgodne | wg zalozen | OK |
| integracja: oszacowanie zapisane, nie uzyte bez `apply`; `apply` zmienia lambde w analizie; brak `t_surface` i `apply` bez `enabled` = blad | zgodne | — | OK |

**Uwagi**
- Estymator na danych uzytkownika wymaga powtorzen (kilka przejazdow TSD tego samego dnia i kilka sesji FWD tego samego aparatu na wspolnej drodze); z jednego przejazdu i jednej sesji lambdy nie da sie wyznaczyc.
- FWD: w referencji `s_ref` stacji pochodzi z `fwd_sref` (regula anteny R2); w narzedziu z `s_fwd` (P043b), wiec okna 10 m moga sie minimalnie roznic — test referencyjny uzywa `fwd_sref`, aby sprawdzic sam estymator.

**Co zostaje:** wyrownanie profilem i scalanie duplikatow pasa (dla danych z kanalem `profile1`); do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych.

## 2026-11-14 — E2e: N4 wyrownanie przejazdow profilem podluznym

**Co zrobiono**
- `compare\align.py`: wyrownanie przejsc korytarza profilem (profil minus mediana biegnaca 101 m; odniesienie = najdluzszy przejazd; bloki ~1 km, przesuniecie z korelacji Pearsona przez FFT w zakresie +-15 m z parabola i wariantem polprobkowym, prog r >= 0,8, odrzut blokow > 3 m od mediany, szablon dla przejsc bez wspolnych blokow, centrowanie na mediane GPS przejsc). Port z `e1_sref` (`align_*`, `delta_fn`, `loo_residuals`, `align_corridor`, krok 2 przebiegu), `e0b_t20_defl` (`block_curve`, `curve_peak`, `running_median_nan`, `resample`), `e0_t20_lag` (`parabola_peak`), `qc_gyro_gps` (`xcorr_pearson`).
- Integracja z trybem `geometry`: opcjonalna kolumna profilu w wierszach TSD (`geometry.tsd_columns.profile`), `geometry.align: auto | true | false` (domyslnie `auto` = gdy jest profil). `s_ref = s_ref_gps + delta(s)`; okna par, pary zerowe, sekcje i lambda korzystaja z wyrownanego `s_ref` (rama GPS stacji FWD zachowana). Nowe wyjscia: kolumny `align_ref`, `align_note`, `n_blocks*`, `delta_*`, `centering_m`, `loo_*` w `tsd_passes.csv` i `tsd_align_blocks.csv`.
- Poprawka znaleziona w trakcie: analiza konczyla sie `ZeroDivisionError` przy mniej niz 3 sesjach FWD (przedzialy klastrowe CR2/dzikiego bootstrapu); teraz sa pomijane, gdy sesji jest < 3 (pozostale miary licza sie).

**Co sprawdzono (255 testow zielonych + 2 `xfail`; nowe: 6 syntetycznych, 1 integracyjny, 7 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T8 zrodla (`test_e1.py`): odtworzenie przesuniecia 2,3 m i dryftu 0,8 m/km; 20 realizacji (1,3 m, szum 0,1); `align_corridor` na dwoch przejsciach | blad RMS < 0,07 m, maks. wewnatrz < 0,15 m, obciazenie < 0,05 m; delta < 0,12 m | wg zrodla | OK |
| T-N4-17 korytarze 0, 1, 2, 3, 4, 7, 8 (100 przejsc): zrodlo wyrownania (`reference` / `profile_ref` / `profile_template` / `gps`), liczba blokow i blokow uzytych, notatka `align_note` | 100 % zgodne, 0 niezgodnych przejsc | 0 | OK |
| T-N4-17 centrowanie korytarza vs `tsd_passes.centering_m` | max roznica 2,1e-5 m | tol. 1e-4 | OK |
| T-N4-17 `s_ref` vs `tsd_sref` (wiersze bez drogomierza zakotwiczonego) | max roznica 0,0011 m | tol. 0,005 (wspolrzedne korytarzy w bazie ~mm) | OK |
| test integracyjny: profil drugiego przejazdu przesuniety o 3 m -> roznica delta miedzy przejazdami; tryb auto bez profilu; `align: true` bez profilu = blad | 3,0 +- 0,25 m; zgodne | wg zalozen | OK |

**Uwagi**
- Wyrownanie dziala na **zbiorze przejazdow podanym na wejsciu**: odniesieniem jest najdluzszy przejazd korytarza w tym zbiorze, wiec `s_ref` jest wzgledny w obrebie zbioru (rama GPS mediany przejsc). Dodanie nowych przejazdow moze zmienic odniesienie i przesunac `s_ref` o ulamki metra; dla powtarzalnosci wynikow miedzy uruchomieniami nalezy podawac stale zbiory przejazdow.
- Nadal poza zakresem: scalanie duplikatow pasa i drogomierz zakotwiczony w strefach zlego GPS (oba z `e1_sref`).

**Co zostaje:** scalanie duplikatow pasa (`find_merges`/`apply_merges`) i drogomierz w strefach zlego GPS; do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych.

## 2026-11-14 — E2f: N4 scalanie duplikatow pasa i odtworzenie calej osi referencyjnej

**Co zrobiono**
- `compare\geo.py`: `parallel_close`, `find_merges`, `apply_merges` (korytarz krotszy niz 2 km, ktory na >= 50 % dlugosci lezy <= 2,5 m od dluzszego, nierozwiazanego korytarza tego samego kierunku, zostaje rozwiazany do tego o najwiekszym udziale; punkty -> cel jako `wide` <= 4,25 m i kurs <= 30 st., dalsze `merged_far`). Port z `e1_sref` (wpis 37, decyzja p. 2). Progi w `AxisParams` (`merge_max_len_m`, `merge_min_share`, `parallel_close_m`); `build_axis(..., merge=True)`.
- Integracja z trybem `geometry`: `geometry.merge_lanes` (domyslnie true, tylko dla osi z przejazdow). Pary i okna wartosci korzystaja wylacznie z wierszy pasa wlasnego (`lane_fit = lane`), jak w zrodle; punkty `wide` zostaja w przejsciach (wyrownanie, `wide_share`, lambda). Nowe wyjscie: `corridor_merges.csv`, kolumna `wide_share` w `tsd_passes.csv`.

**Co sprawdzono (262 testy zielone + 2 `xfail`; nowe: 5 + 1 syntetycznych, 1 regresji)**
| Wartosc referencyjna | Uzyskana | Roznica | Status |
|---|---|---|---|
| T-N4-18 os zbudowana od zera z 239 plikow TSD (bez pliku 55 `qc_gps_shifted`): liczba i numery korytarzy | 165 = 165, te same numery | 0 | OK |
| T-N4-18 dlugosci korytarzy vs `ref_corridors` | max roznica 0 | tol. 1e-3 | OK |
| T-N4-18 scalenia duplikatow pasa vs `ref_corridor_merges`: zestaw, cel, punkty `wide` i `merged_far` | 43 = 43, 100 % zgodne | 0 | OK |
| T-N4-18 wiersze vs `tsd_sref`: korytarz | 6 956 291 z 6 956 291 zgodnych | 0 | OK |
| T-N4-18 `s_ref_gps` | max roznica 0,0005 m (zapis w bazie z dokladnoscia 1 mm) | tol. 1e-3 | OK |
| T-N4-18 punkty `wide` (`lane_fit = wide`) | 25 219 = 25 219, wszystkie te same | 0 | OK |
| syntetyczne: duplikat 2,2 m obok jest scalany; 4 m, > 2 km i przeciwny kierunek nie sa; `parallel_close`; potok: pary tylko z pasa wlasnego, bez scalania dwa korytarze | zgodne | wg zalozen | OK |

**Uwagi**
- Cala os referencyjna (165 korytarzy, 7 mln wierszy) jest odtwarzana od zera w ok. 40 s; razem z E2b i E2e potwierdza to, ze potok osi, przypisania, wyrownania i scalania zgadza sie ze zrodlem na calym zbiorze, nie tylko na probkach.
- Baza referencyjna nie ma stref zlego GPS (`tsd_gps_bad_segments` puste), wiec brak drogomierza zakotwiczonego nie rozni wynikow na tym zbiorze; dla danych z blednym GPS wiersze trzeba usunac z wejscia albo pominac.
- Scalanie zalezy od zbioru przejazdow (korytarze budowane zachlannie od najdluzszych ciagow): ten sam zbior daje te same korytarze, inny zbior moze dac inne numery i scalenia.

**Co zostaje:** drogomierz zakotwiczony w strefach zlego GPS (`apply_odometer_anchor`; wymaga tabeli stref zlego GPS); do ustalenia: `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16, potwierdzenie `SCI_SUB`.

**STOP — decyzja:** brak decyzji blokujacych.

## 2026-11-14 — SCI_SUB pomijane (decyzja Jacka)

- `SCI_SUB` nie jest liczone: w XML DSN zostaje pustym elementem `<SCI_SUB></SCI_SUB>` (element jest w ukladzie zalacznika H p. 4.2, wiec go nie usuwam; puste wartosci sa dozwolone jak `IRI_1`, `PROFIL_1`). Kolumna `a090` (calka 0-0,90 m) zostaje w CSV bez zmian. Pytanie Q-N3-12 (definicja SCI_SUB) jest zamkniete; na liscie otwartych punktow zostaja `UC_Schema.xsd`, Q-N3-14, Q-N3-15, Q-N3-16.
- Test `test_cli_n3_analytic_values_and_xml`: asercja SCI_SUB zmieniona na "pusty element".

