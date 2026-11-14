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
