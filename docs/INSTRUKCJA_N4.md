# Instrukcja N4 — `tsd_fwd_compare` (porownanie TSD z FWD, tryb `pairs`)

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Metoda: raport PW.S-1063 (Etap II), p. 6.2-6.3 i 7.3.

## 1. Do czego sluzy
Ocenia zgodnosc D0 z TSD i z FWD na **gotowych parach** punktow, po sprowadzeniu obu stron do 20 C, i podaje: miary zgodnosci,
przedzialy niepewnosci, wplyw warunkow (aparat, kalibracja, odstep czasu, GoF), kontrole zerowe oraz funkcje przeliczajaca
(mnoznik TSD → FWD) z ocena poza proba.

Tryb `pairs` zaklada, ze pary zostaly zbudowane wczesniej. **Budowania par z geometrii (odcinki, antena FWD, rzut na os drogi)
w tym wydaniu nie ma** (tryb `geometry`, etap E2b). Konfiguracja z `mode: geometry` konczy sie bledem.

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
- Tylko tryb `pairs`; pary z geometrii (E2b) w kolejnym etapie. Przy budowie par geometrycznych polozenie TSD jest przesuniete
  o −4,8 m (lag, +- 1,5 m): korekta jest wliczona raz, przy wyznaczaniu `s_ref` TSD; nie wolno jej dokladac drugi raz do okien.
- Korelacja wewnatrz sesji par zerowych dla wariantu **bez korekty** nie jest w pelni odtwarzalna (inna definicja okna w skrypcie zrodlowym);
  test zostal oznaczony jako oczekiwane niepowodzenie (`xfail`) w testach pakietu — nie wplywa to na wyniki par skorygowanych.
- Lambda (0,11787) jest przyjeta z raportu. Dla innych danych/aparatow powinna byc wyznaczona na nowo; narzedzie tego nie robi.
- Mnoznik przeliczenia opisuje zgodnosc na ocenianych odcinkach i aparatach; poza nimi (inna wersja rejestratora, inny przedzial
  kalibracji) trzeba go zweryfikowac.
