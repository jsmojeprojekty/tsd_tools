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
