# Instrukcja N1 — `fwd_tempcorr` (korekta temperaturowa ugiec FWD)

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Metoda: raport PW.S-1063 (Etap II), p. 7.1.

## 1. Do czego sluzy
Sprowadza ugiecia FWD z kazdego czujnika do temperatury odniesienia 20 C (i sily 50 kN), a dopiero z ugiec skorygowanych liczy
wskazniki krzywizny SCI300, BDI i BCI. Kolejnosc jest obowiazkowa: **najpierw korekta temperaturowa na kazdym czujniku, potem
wskazniki**. Narzedzie nie ma wlasnych wspolczynnikow wskaznikow.

## 2. Co trzeba miec
- Plik z pomiarem FWD: `Drops*.xlsx` + `stations*.xlsx` (format IBDiM), baza MDB Dynatest (wymaga sterownika ODBC; odczyt tylko do odczytu)
  albo CSV (jeden wiersz = jeden zrzut; kolumny `station_id`, `force_kn`, `d1`..`d9`, opcjonalnie `session_id`, `time`, `latitude`, `longitude`,
  `asphalt_temp`, `air_temp`).
- **Temperature warstwy asfaltowej T_mid** (z glebokosci ok. 12 cm, ze srodka pakietu), w jednej z postaci:
  kolumna w pliku stacji (`temperature.source: column`), jedna stala (`constant`) albo CSV z wynikiem N2 (`csv_join`).
  Narzedzie **niczego nie interpoluje ani nie zgaduje** — brak temperatury oznacza flage `T_MISSING` i puste wartosci skorygowane.

## 3. Uruchomienie
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_tempcorr --config configs\n1_example.yaml
```
Opcje: `--dry-run` (nic nie zapisuje), `--out-dir`, `--log-level`, `--strict` (kod wyjscia 2, gdy jakakolwiek stacja nie ma waznej temperatury).
Przyklad konfiguracji: `configs\n1_example.yaml`; nieznany klucz w konfiguracji konczy sie bledem (literowka nie przejdzie niezauwazona).

## 4. Najwazniejsze ustawienia
| Klucz | Wartosci | Znaczenie |
|---|---|---|
| `input.drop_rule` | `mean_nonseating` (domyslnie), `second_drop`, `last_nonseating` | ktore zrzuty tworza wartosc stacji; domyslnie srednia zrzutow nieosadczych |
| `correction.variant` | `B` (domyslnie), `A`, `legacy` | B: wykladniczy, wazny 5-30 C; A: liniowy, wazny 5-25 C; legacy: dotychczasowy wzor krajowy, tylko porownawczo |
| `correction.road_type` | `public`, `highway` | tylko dla `legacy`: k = 0,02 (drogi publiczne) albo k = 0,01 (autostrady) |
| `correction.coefficient_set` | `e2a3_full` (domyslnie), `tab71`, `file` | `e2a3_full` = pelna precyzja z raportu; `tab71` = wartosci zaokraglone z tab. 7.1; `file` = wlasne wspolczynniki (patrz p. 7) |
| `temperature.max_age_min` | domyslnie 60 | starszy wpis temperatury: flaga `T_STALE` |
| `output.formats` | `[csv]`, `[csv, xlsx]` | |

Wariant legacy jest **porownaniem**, nie zalecana metoda; wynik ma flage `LEGACY_RULE`. Dla k = 0,01 zrodlem jest kod TSDLayerIQ
(brzmienie przepisu nie zostalo zweryfikowane — odnotowano w pliku meta).

## 5. Wyniki
W katalogu `output.dir`, dla kazdego pliku wejsciowego:
- `<plik>_tempcorr.csv` — jeden wiersz na stacje: `session_id, station_id, measured_at, latitude, longitude, force_kn, t_mid_c, t_source,
  t_status, variant, coef_set`, ugiecia znormalizowane do 50 kN (`D0`..`D1800`), skorygowane do 20 C (`D0_20`..`D1800_20`),
  `SCI300_20, BDI_20, BCI_20`, `flags`, `flags_text`;
- `<plik>_tempcorr_meta.json` — wersja pakietu, wejscia z sumami MD5, uzyty wariant i wspolczynniki;
- `summary.csv` — na plik: liczba stacji, T min/mediana/max, udzialy flag, mediana korekty D0.

## 6. Flagi (kolumna `flags_text`; rekord nigdy nie jest usuwany)
| Flaga | Znaczenie / co robic |
|---|---|
| `T_MISSING` | brak temperatury; wartosci skorygowane puste — uzupelnic temperature |
| `T_BELOW_5C` | T < 5 C: korekta nie ma zastosowania (stan podloza); wartosci skorygowane puste |
| `T_ABOVE_RANGE` | T powyzej zakresu wariantu (A: 25 C, B: 30 C); korekta wykonana, wynik **uzywac ostroznie** |
| `INDEX_ABOVE_RANGE` | SCI300/BDI/BCI przy T > 25 C: wskazniki policzone, ale poza zakresem, dla ktorego zbadano ich korekte |
| `INDEX_NONPOSITIVE` | wskaznik po korekcie <= 0 |
| `T_CARRIED`, `T_ENTRY_POSSIBLE`, `T_STALE` | temperatura przeniesiona z wczesniejszej stacji / niepewny wpis / zbyt stary wpis |
| `T_PLACEHOLDER` | wartosc zastepcza aparatu (np. 20,4 C) — **to nie jest pomiar**, wynik traktowac jako bez temperatury |
| `T_SENTINEL` | wypelniacz eksportu (np. -3,4e38) potraktowany jako brak |
| `FORCE_OFF_NOMINAL` | sila zrzutu poza +-10 % od 50 kN (normalizacja liniowa mimo to wykonana) |
| `NO_NONSEATING_DROP` | brak zrzutu nieosadczego w stacji |
| `THICKNESS_OUT_OF_RANGE` | grubosc pakietu spoza 15-30 cm (zakres wazny dla wspolczynnikow) |
| `GEOPHONE_MISSING` | brak czujnika w ukladzie sesji |
| `LEGACY_RULE` | wynik dotychczasowego wzoru (tryb porownawczy) |

## 7. Dopasowanie wlasnych wspolczynnikow (opcjonalne, `fwd_fit`)
Gdy macie wlasne wizyty powtarzane w roznych temperaturach (jedna wizyta = jeden wiersz CSV/XLSX), narzedzie dopasuje wspolczynniki
i zapisze je w formacie uzywanym przez N1:
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_fit --config configs\fwd_fit_example.yaml
```
Wynik `<plik>_coefficients.csv` podaje sie w N1: `correction: {coefficient_set: file, coefficients_file: ..., coefficients_scope: lacznie}`.
Dla kazdego wskaznika potrzeba co najmniej `fit.min_n` = 30 wizyt w zakresie 5-30 C; przy mniejszej liczbie wiersz wspolczynnika
jest pusty z adnotacja `za malo danych` (nie ma wartosci domyslnej). Przedzialy 95 % pochodza z bootstrapu blokowego po dniach.

## 8. Ograniczenia
- Wspolczynniki z raportu pochodza z wizyt na ocenianej sieci; dla innych konstrukcji i grubosci (poza 15-30 cm) wynik jest orientacyjny.
- Narzedzie koryguje temperature, nie sile ani sezonowa zmiennosc podloza; ponizej 5 C wyniku nie podaje.
- Wskazniki krzywizny licza sie wylacznie ze skorygowanych ugiec. Powyzej 25 C sa oznaczone (nie zablokowane).
- Temperatura wejsciowa musi byc temperatura **warstwy** (nie powierzchni, nie powietrza). Zla wielkosc na wejsciu daje
  poprawnie wygladajacy, ale bledny wynik — narzedzie tego nie wykryje.
