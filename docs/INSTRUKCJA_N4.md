# Instrukcja N4 — `tsd_fwd_compare` (porownanie TSD z FWD)

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Metoda: raport PW.S-1063 (Etap II), p. 6.2-6.3 i 7.3.

## 1. Do czego sluzy
Ocenia zgodnosc D0 z TSD i z FWD na **gotowych parach** punktow, po sprowadzeniu obu stron do 20 C, i podaje: miary zgodnosci,
przedzialy niepewnosci, wplyw warunkow (aparat, kalibracja, odstep czasu, GoF), kontrole zerowe oraz funkcje przeliczajaca
(mnoznik TSD → FWD) z ocena poza proba.

Dwa tryby wejscia: `pairs` (gotowe pary, p. 3) i `geometry` (N4 sam buduje pary z geometrii, p. 3a). Dalsza analiza jest taka sama.

## 2. Zasady, ktorych narzedzie pilnuje
- Pary sa tylko **geometryczne**. Zadnego wyboru rekordu TSD wedlug wartosci FWD (to dawaloby sztucznie dobra zgodnosc).
  Jesli w pliku par jest wybor po wartosciach, wyniki sa tylko diagnostyczne i nie sluza do wnioskow.
- D0 TSD pochodzi z eksportu **B_1510off** (przeliczone bez czujnika 1,51 m). Eksport nominalny jest wejsciem kontrolnym, nie zrodlem.
- Obie strony sa korygowane temperaturowo (`beta` D0 = 1,60415 %/C, do 20 C) **przed** liczeniem miar. Zbiory bez korekty
  (`none`) sa tylko porownaniem.
- Nachylen TSD nie koryguje sie wspolczynnikami FWD.

## 3. Co trzeba miec
Plik CSV par (`input.pairs_csv`), jeden wiersz = jedna para, z kolumnami (nazwy mozna zmienic w `input.columns`):
`pair_id`, `fwd_session_id` (klaster = sesja FWD), `fwd_d0` [um, 50 kN], `d0_tsd` [um, mediana okna +-5 m], `fwd_t12_cal`, `tsd_t12_cal`
(temperatura warstwy 12 cm po stronie FWD i TSD — z N2). Pozostale kolumny sa opcjonalne i wlaczaja dodatkowe analizy:
`device`, `calib_interval`, `dt_days`, `win5_gof05_share`, `corridor_id`, `fwd_station_id`, `tsd_year`, `era`, `fwd_measured_at_local`.
Temperatury i dodatkowe kolumny mozna dolaczyc z osobnych plikow po `pair_id`: `input.t12_csv`, `input.meta_csv`.
Opcjonalnie: `input.null_pairs_csv` — wartosci TSD dla par zerowych (`pair_id`, `null_type`, `d0_w5`, `d0_valid_w5`).

## 3a. Tryb `geometry` — pary z geometrii
```bash
C:\ENV
arzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_fwd_compare --config configs
4_geometry_example.yaml
```
**Wejscie**
- Wiersze TSD (`geometry.tsd_rows`): CSV z kolumnami `chainage_m` (SUROWY pikietaz pliku, niemalejacy), `lat`, `lon`, `d0` (B_1510off, um),
  `gof`, `t12_c` (temperatura warstwy z N2), opcjonalnie `speed_kmh`. Wygodnie: `*_rows.csv` z N3 (`output.rows_csv: true`). Nie podawaj
  `pos_m` ani pikietazu po przesunieciu — lag polozenia ugiec (-4,8 m) N4 stosuje sam, dokladnie raz.
- Data przejazdu TSD: z `geometry.tsd_runs_csv` (`run_id`, `date`), z nazwy pliku (`T4RRRRMMDDnnnn`) albo z `geometry.date_override`.
  Brak daty to blad. Przedzial kalibracji TSD (`calib_interval`) wynika z daty i tabeli `geometry.calib_intervals`.
- Stacje FWD (`geometry.fwd_stations_csv`): jeden wiersz = jedna stacja; `station_id`, `session_id`, `station_m` (dystansomierz; km albo m —
  jednostka wykrywana z danych), `latitude`, `longitude`, `device` (aparat, np. 8002-367), `date`, `D0` (um, 50 kN, bez korekty temperaturowej,
  z N1), `t_mid_c` (temperatura warstwy po stronie FWD). Opcjonalnie `heading_deg` (brak: kurs z kolejnosci stacji w sesji), `time`.
  Nazwy kolumn mozna zmienic w `geometry.fwd_columns` / `geometry.tsd_columns`.

**Co N4 robi**
1. Buduje os pasa (korytarz) z przejazdow TSD (albo bierze gotowa z `geometry.corridors_csv`) i przypisuje wiersze TSD: `s_ref` (pozycja
   wzdluz osi) i `lateral_m` (odleglosc poprzeczna, + = w lewo od kierunku jazdy).
2. Rzutuje antene FWD na os, wyznacza kierunek sesji **z danych** (nie z pola kursu), przesuwa antene przed plyte wg tabeli regul aparatu
   (`geometry.antenna`; domyslnie 8002-367: 5,5 m do 2025-10-09, potem 0; 8082-119: 1,0 m; 8002-369: 1,0 m, niepotwierdzone) i wygladza polozenie
   regresja dystansomierza. Wynik: `s_fwd` i niepewnosc polozenia `sigma_long`.
3. Dla kazdej stacji i kazdego przejazdu TSD na tym samym korytarzu (ten sam rok) tworzy pare; okno wartosci to wiersze z |s_ref − s_fwd| <= 5 m
   (co najmniej 3 z waznym d0), wartosc = mediana d0. Warstwa jakosci polozenia: A (|dlat| <= 1,0 m i sigma_long <= 1,0 m), B (1,75 m / 2,5 m),
   C (sigma_long <= 5 m), X (reszta). Do porownania wchodza warstwy z `geometry.layers` (domyslnie A i B).
4. Tworzy pary zerowe (to samo FWD, wiersze TSD z tego samego przejazdu ±200 m dalej i losowe >= 300 m dalej; seed 20261017) do kontroli zerowej.

5. Wykrywa odcinki wspolne TSD-FWD wg kryteriow Tab. 3.2 (`geometry.sections`): para (sesja FWD, przejazd TSD) jest odcinkiem, gdy ten sam rok
   (odstep <= 400 dni), >= 5 stacji FWD w promieniu 8 m od najblizszego punktu TSD, pokrycie >= 30 % (wzgledem stacji lezacych w obwiedni TSD),
   zakres pikietazu >= 500 m, |Spearman(station_m, pikietaz)| >= 0,80 (**monotonicznosc polozenia stacji, nie korelacja ugiec**), kierunek wg kursow
   (roznica <= 30 st. = ten sam, >= 150 st. = przeciwny, reszta odrzucona) oraz klasa pasa wg mediany odleglosci poprzecznej (<= 0,75 m ten sam,
   <= 2,0 m sasiedni, wiecej: inny). Pary dostaja kolumny `in_section`, `section_id`, `section_lane`, `section_direction`, `section_status`.
   Domyslnie odcinki nie filtruja par; `geometry.sections.require_section: true` zostawia tylko pary z odcinka (bez odrzuconych w przegladzie).
6. Raport przegladu `section_review.html` (reczna kontrola „linia do linii”): dla kazdego odcinka slad GPS (TSD i stacje FWD), wykres
   station_m - pikietaz z regresja oraz d0 TSD (gesta linia) i D0 FWD (punkty) na wspolnym pikietazie. Decyzje zapisz w pliku CSV
   (`session_id`, `run_id`, `status`: confirmed / rejected) i podaj w `geometry.sections.review_csv`. Raport pokazuje do 300 odcinkow
   (`report_max_sections`); pelna tabela: `sections.csv`.

7. Opcjonalnie szacuje **lambde** (`geometry.lambda_est.enabled: true`): lambda = sigma_FWD² / sigma_TSD² na skali log, uzywana w regresji Deminga.
   sigma_TSD to rozrzut roznic ln d0 miedzy przejazdami TSD z jednego dnia (|dt| <= 1 dzien) w tych samych binach 10 m korytarza (poza betonem;
   bin pokryty, gdy >= 5 wierszy); sigma_FWD to rozrzut powtorzen D0 FWD miedzy sesjami tego samego aparatu w oknach 10 m (od 2024 r., |dT powierzchni|
   < 3 C, poza betonem, poziom sesji usuniety). Estymator wymaga powtorzen: kilku przejazdow TSD tego samego dnia i kilku sesji FWD tego samego aparatu
   na wspolnej drodze oraz kolumny `t_surface` (temperatura powierzchni z pirometru aparatu FWD). Bez czasu wiersza (`time` w wierszach TSD) czas przejazdu
   to poludnie daty, wiec „|dt| <= 1 dzien” oznacza te sama lub sasiednia date. Wynik w `lambda_estimate.csv`; do analizy trafia dopiero po
   `geometry.lambda_est.apply: true` (domyslnie analiza uzywa `measures.lambda_d0`, 0,11787 z raportu). Przy malej liczbie powtorzen oszacowanie jest
   niepewne — sprawdz `n_pairs_tsd` i `n_pairs_fwd` w pliku wynikowym.

**Dodatkowe wyniki**: `lambda_estimate.csv` (gdy wlaczony estymator), `sections.csv` (odcinki z miarami i statusem przegladu), `section_review.html`, `geometry_pairs.csv` (wszyscy kandydaci z warstwami i oknami), `fwd_plate_positions.csv` (polozenie plyty i `sigma_long` dla stacji),
`tsd_passes.csv`, `corridors.csv`, `geometry_null_pairs.csv`, `fwd_sessions.csv` (kierunek i jednostka dystansomierza na sesje),
`fwd_session_runs.csv` (ciagi stacji i dopasowanie dystansomierza). W `meta.json` sekcja `geometry` zawiera uzyte reguly anteny i `sigma_era`.

**Czego ten tryb nie robi (jeszcze)**
- Pary wynikaja z wspolnego korytarza i roku, nie z odcinkow; odcinki sa kontrola (kolumny `in_section`, opcjonalny filtr) i podstawa przegladu recznego.
  Odcinki liczone sa na surowym GPS (antena FWD i GPS wiersza TSD, bez przesuniecia plyty ani lagu), jak w zrodle.
- `s_ref` pochodzi z GPS (bez wyrownania profilem, bez scalania duplikatow pasa). Os z przejazdow TSD zalezy od zestawu przejazdow — ta sama droga
  z innym zestawem plikow moze dac troche inne `s_ref`; dla powtarzalnosci podaj gotowa os w `geometry.corridors_csv`.
- Przejazdy z wieloma pasami jednej jezdni wymagaja czytelnych przejazdow w obu pasach (korytarze rozdzielane sa przy rozstawie > 1,75 m
  i kursie > 30 stopni).

## 4. Uruchomienie
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_fwd_compare --config configs\n4_pairs_example.yaml
```
Opcje: `--dry-run`, `--out-dir`, `--log-level`, `--strict`. Obliczenia z `replicates: 9999` trwaja dluzej; do prob mozna zmniejszyc liczbe replik.

## 5. Najwazniejsze ustawienia
| Klucz | Domyslnie | Znaczenie |
|---|---|---|
| `correction.treatments` | `[none, main_after]` | warianty do porownania: `none` (bez korekty), `main_after` (korekta obu stron), `k02` (dotychczasowy wzor, porownawczo) |
| `correction.main_treatment` | `main_after` | wariant glowny: dla niego liczone sa przedzialy niepewnosci, warunki i kalibracja |
| `measures.lambda_d0` | 0,11787 | stosunek wariancji bledu FWD do TSD na skali log (z raportu, p. 6.2); z konfiguracji, **nie** estymowany |
| `uncertainty.methods` | `session_bootstrap`, `wild_cluster_webb`, `cr2` | trzy metody przedzialow dla malej liczby klastrow |
| `uncertainty.h0_multiplier` | 1,6 | wartosc mnoznika sprawdzana w przedziale 95 % |
| `conditions.group_by` | `[device, calib_interval]` | podzial na warunki (aparat, przedzial kalibracji); ujemne `dt_days` raportowane osobno |
| `calibration.models` | `[multiplier]` | `affine` dodatkowo na zyczenie |
| `output.overwrite` | false | nadpisywanie wynikow |

## 6. Wyniki (w `output.dir`)
| Plik | Zawartosc |
|---|---|
| `agreement.csv` | miary zgodnosci dla kazdego wariantu korekty: liczba par i sesji, mediana ilorazu TSD/FWD z przedzialem, odchylenie log-ilorazu, r Pearsona, rho Spearmana, CCC, nachylenie Deminga (log-log), korelacja wewnatrz sesji |
| `agreement_groups.csv` | to samo w grupach (aparat x rok) |
| `agreement_ci.csv` | przedzialy mnoznika trzema metodami (bootstrap po sesjach, wild cluster Webb, CR2) |
| `conditions.csv` | zgodnosc wg warunkow (aparat, kalibracja, odstep czasu, GoF, zmiennosc) |
| `calibration.csv` | mnoznik/funkcja przeliczajaca oceniana poza proba (leave-session-out) |
| `conversion.csv` | funkcja przeliczajaca TSD → FWD |
| `null_checks.csv`, `null_delta.csv` | kontrola zerowa: pary przesuniete o −200 m / +200 m i permutacje; roznica wzgledem par prawdziwych |
| `pairs_corrected.csv` | pary z wartosciami skorygowanymi |
| `meta.json` | wersje, hash konfiguracji, uzyta beta, liczniki par (w tym par bez T12 lub poza 5-30 C), uwaga metodyczna |
| `report.html` | skrot do czytania w przegladarce |

## 7. Jak czytac wyniki
- Zgodnosc oceniaj **razem z kontrola zerowa**. Para zerowa (ten sam przejazd przesuniety o 200 m albo permutacja) pokazuje, jak duza
  zgodnosc daje sama struktura danych (np. wspolna zmiennosc wzdluz drogi). Prawdziwa zgodnosc ma sens, gdy wyraznie ja przewyzsza.
- Liczba **klastrow** (sesji FWD) jest mala (rzedu kilkudziesieciu): przedzialy z `agreement_ci.csv` sa wazniejsze niz pojedynczy mnoznik;
  gdy trzy metody sie rozchodza, to jest informacja o niepewnosci, nie blad narzedzia.
- Pary z T12 poza 5-30 C albo bez T12 sa oznaczone i policzone w `meta.json`; nie sa cicho wykluczane z calosci wnioskow.

## 8. Ograniczenia i punkty otwarte
- Przy budowie par geometrycznych (tryb `geometry`) polozenie TSD jest przesuniete
  o −4,8 m (lag, +- 1,5 m): korekta jest wliczona raz, przy wyznaczaniu `s_ref` TSD; nie wolno jej dokladac drugi raz do okien.
- Korelacja wewnatrz sesji par zerowych dla wariantu **bez korekty** nie jest w pelni odtwarzalna (inna definicja okna w skrypcie zrodlowym);
  test zostal oznaczony jako oczekiwane niepowodzenie (`xfail`) w testach pakietu — nie wplywa to na wyniki par skorygowanych.
- Lambda (0,11787) jest domyslnie przyjeta z raportu. Dla innych danych/aparatow mozna ja oszacowac (`geometry.lambda_est`, tylko tryb `geometry`);
  w trybie `pairs` lambda pochodzi z konfiguracji.
- Mnoznik przeliczenia opisuje zgodnosc na ocenianych odcinkach i aparatach; poza nimi (inna wersja rejestratora, inny przedzial
  kalibracji) trzeba go zweryfikowac.
