# Instrukcja N3 — `tsd_network` (TSD na sieci + XML DSN)

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Metoda: raport PW.S-1063 (Etap II), p. 6.1-6.2 i 7.3; format XML: zalacznik H, p. 4.2.

## 1. Do czego sluzy
Z eksportu przejazdu TSD (B_1510off) liczy ugiecie D0 skorygowane do 20 C, calki nachylen (P0) oraz ich pochodne, usrednia je
w oknach +-5 m co 10 m (i w odcinkach 50 / 100 m) i zapisuje wyniki jako CSV oraz plik XML DSN `UC` (zalacznik H p. 4.2).

## 2. Co trzeba miec
- Eksport TSD **B_1510off**: `*.raw.sup.txt` (D0 przeliczone z 9 czujnikow nachylen, **bez czujnika 1,51 m**). Eksport nominalny
  (z czujnikiem 1,51 m) nie jest tu uzywany jako zrodlo D0.
- **Temperatura warstwy 12 cm** na przejezdzie: CSV z kolumnami `chainage_m` i `t12_c` (i opcjonalnie `file`) — najlepiej wynik N2
  z `input.passthrough: [chainage_m, file]`. Temperatura pirometru TSD (`Temp Road`) **nie jest** temperatura warstwy; bez temperatury
  warstwy trzeba swiadomie ustawic `layer_temp.source: none` + `allow_uncorrected: true` (D0 bez korekty, flaga `T_MISSING`).
- Dla XML: kod oddzialu, rok, droga, jezdnia, pas i kilometr poczatku odcinka (`km_start`) — **bez wartosci domyslnych**, podaje je uzytkownik.

## 3. Uruchomienie
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_network --config configs\n3_example.yaml
```
Opcje: `--dry-run`, `--out-dir`, `--log-level`, `--strict`. W konfiguracji mozna podac wiele plikow `input.tsd_files`; kazdy daje osobny zestaw wynikow.

## 4. Co jest liczone (kolejnosc)
1. Odczyt wierszy co 1 m; kontrola kroku pikietazu i naglowka pliku (problemy sa **flagowane, nie odrzucane**).
2. Temperatura warstwy 12 cm interpolowana na pikietaz wiersza.
3. D0 skorygowane do 20 C: wykladniczo, beta = 1,60415 %/C (zakres 5-30 C; poza nim flagi), jak w N1 dla czujnika D0.
4. Filtr Hampela na D0 po korekcie: okno +-10 m, prog 3 x 1,4826 x MAD okna; odrzucenie oznacza odrzucenie calej czaszy wiersza.
5. Calki nachylen P0 z 9 czujnikow (interpolacja PCHIP, krok 1 mm): odcinki 0-0,31, 0,31-0,61, 0,61-0,91 m i P0(x). **Bez korekty
   temperaturowej** (flaga `P0_UNCORRECTED` — tak wymaga raport 6.1).
6. Mediana w oknie +-5 m (przedzial domkniety, co najmniej `min_rows_in_window` = 3 wazne wiersze); mediana liczona z wartosci wierszy
   (nie calka z mediany).
7. Agregacja do przedzialow 50 i 100 m (`floor(pozycja / krok)`).

## 5. Ustawienia, o ktorych trzeba wiedziec
| Klucz | Domyslnie | Uwagi |
|---|---|---|
| `layer_temp.source` | `csv` | `csv` (wynik N2), `constant` (jedna wartosc), `none` (bez korekty, z `allow_uncorrected: true`) |
| `processing.window_m` | 5 | polowka okna; dopuszczalnie 10 |
| `processing.hampel` | wlaczony, 10 m, k = 3 | |
| `processing.aggregate_m` | `[50, 100]` | |
| `processing.position_offset_m` | **0** | patrz p. 6 |
| `processing.to_fwd_scale_enabled` | false | dodatkowa kolumna w skali FWD (mnoznik 1,62); **opcjonalna**, dla D_200 i D_300 niezweryfikowana (flaga `SCALE_FWD_UNVERIFIED`) |
| `qc.gps_gyro` | true | test zgodnosci kursu z zyroskopu i GPS (tylko diagnostyka, nie koryguje polozenia) |
| `xml_uc.enabled` | false | `kod_oddz`, `rok`, `droga`, `jezdnia`, `pas`, `km_start` wymagane |
| `xml_uc.km_direction` | `increasing` | `decreasing`, gdy kilometraz maleje wzdluz przejazdu |
| `output.rows_csv` | false | wlacza zapis wierszy 1 m (duze pliki) |

## 6. Polozenie ugiec (`position_offset_m`)
Punkt pomiaru ugiecia lezy wzdluz toru okolo **4,8 m** (+- 1,5 m) dalej niz polozenie GPS zapisane w tym samym wierszu. W projekcie
wartosc te zapisuje sie jako lag **−4,8**, a pozycja wiersza to `pikietaz − lag = pikietaz + 4,8 m`. W N3 domyslnie jest **0**
(bez przesuniecia, decyzja Jacka); zeby przesunac, wpisz `processing.position_offset_m: -4.8`. Przesuniecie dotyczy okien, agregacji i XML
(`DYSTANS`, `KM` odnosza sie wtedy do punktu pomiaru). Wartosc jest taka sama dla wszystkich plikow (jedna stala globalna, nie per plik).
Uwaga: to nie jest korekta znanego przesuniecia pikietazu 20-50 m na poczatku niektorych plikow z 2026 — to wymaga osobnej oceny.

## 7. Wyniki
W `output.dir`, dla pliku `<nazwa>.raw.sup.txt` (nazwa = czesc przed pierwsza kropka):
- `<nazwa>_windows_10m.csv` — okna co `xml_uc.step_m` (10 m): mediany `d0_20`, `t12_c`, `speed_kmh`, calek, `n_rows`, `n_valid_d0`,
  `gof_share_ge05`, `gof_median`, `window_ok`;
- `<nazwa>_agg_50m.csv`, `<nazwa>_agg_100m.csv` — odcinki 50 i 100 m (`bin_id, s_from_m, s_to_m`, te same mediany);
- `<nazwa>_rows.csv` — wiersze co 1 m (tylko gdy `rows_csv: true`), z flagami `flags_text`;
- `UC_<nazwa>.xml` — gdy `xml_uc.enabled`;
- `<nazwa>_n3_meta.json` — parametry, zrodlo temperatury, skala, wyniki testu zyroskop-GPS, liczba rekordow XML;
- `summary.csv` — jeden wiersz na przejazd (data, liczba wazna D0, udzialy flag).

### Plik XML (profil `dsn_h42`, 21 pol)
Kolejnosc pol jak w zalaczniku H p. 4.2: `KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1, PREDKOSC, STRAIN_GAUGE,
T_DROGI, T_POW, SCI_200, SCI_300, SCI_SUB, D_0, D_200, D_300`. Znaczenie: `D_0` = mediana D0 po korekcie do 20 C; `D_x = D_0 − P0(x)`;
`SCI_200 = D_0 − D_200`, `SCI_300 = D_0 − D_300`; `T_DROGI`, `T_POW` = odczyty temperatur z eksportu TSD (nie temperatura warstwy).
`IRI_1` i `PROFIL_1` sa puste (eksport B_1510off nie zawiera tych kanalow). Brak wartosci to pusty element, nigdy `nan`.
Plik: UTF-8 bez BOM, konce linii LF. Struktura jest sprawdzana wewnetrznie; **walidacja wzgledem `UC_Schema.xsd` zostanie dodana po
dostarczeniu schematu** — do tego czasu plik trzeba traktowac jako zgodny z opisem z zalacznika H, ale niezweryfikowany schematem.

## 8. Flagi (kolumna `flags_text`)
`T_MISSING`, `T_BELOW_5C`, `T_ABOVE_RANGE` (temperatura: brak / < 5 C / > 30 C), `D0_INVALID`, `D0_HAMPEL_REJECTED`, `SLOPE_MISSING`,
`P0_UNCORRECTED` (stala adnotacja calek), `INTEGRAL_NONPOSITIVE`, `WINDOW_FEW_ROWS`, `LOW_GOF_SHARE` (udzial czasz GoF >= 0,5 w oknie < 50 %;
GoF jest atrybutem, nie filtrem), `GPS_INVALID`, `FILE_NOT_RECALIBRATED` (pusty `Re-calibrationfile`: to nie jest eksport B_1510off),
`FILE_MISSING_CHANNEL`, `FILE_SCALE_SUSPECT` (krok pikietazu odbiega od 1 m), `FILE_YEAR_OUT_OF_RANGE` (rok przed 2024), `GYRO_GPS_NOT_OK`,
`SCALE_FWD_UNVERIFIED`.

## 9. Ograniczenia i punkty do potwierdzenia
- Poziom D0 TSD zalezy od wersji rejestratora i przedzialu kalibracji aparatu; **porownywac przejazdy w obrebie tej samej wersji**.
  Mieszanie wersji bez korekty zmienia D0 o rzad wielkosci i wyklucza analize temperaturowa.
- Wyniki sa w **skali TSD**. Przeliczenie na skale FWD (mnoznik 1,62) jest opcjonalne, wazne dla wartosci odcinkowych (>= 100 m)
  i nie zastepuje porownania w N4.
- `D_300` jest liczone dla 0,30 m (nie 0,31 m, polozenia czujnika). `SCI_SUB = D_0 − D_900` to definicja robocza,
  do potwierdzenia po dostarczeniu `UC_Schema.xsd` (Q-N3-12a).
- KM: eksport nie zawiera znacznikow kilometrazu; `KM = km_start + znak x pikietaz/1000` z konfiguracji. Data pochodzi z nazwy pliku,
  godzina z `GPS time` — sprawdzic na pierwszym pliku (Q-N3-15).
- Temperatura warstwy 12 cm pochodzi z modelu N2 (RMSE 1,75 C na zbiorze eksploracyjnym, 2,73 C na niezaleznym) — blad temperatury
  przenosi sie na skorygowane D0 (ok. 1,6 % na stopien).
- Przy `T12 < 5 C` korekta nie ma zastosowania i `d0_20` jest puste; przejazdy w mrozie nie tworza D_0 w XML.
