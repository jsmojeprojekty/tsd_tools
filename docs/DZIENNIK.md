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
