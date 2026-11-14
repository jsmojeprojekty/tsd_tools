# Instrukcja N2 — `layer_temp` (temperatura warstwy asfaltowej)

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Metoda: raport PW.S-1063 (Etap II), model fizyczny TN.

## 1. Do czego sluzy
Szacuje temperature warstwy asfaltowej na zadanej glebokosci (domyslnie 12 cm) w chwili pomiaru FWD/TSD. Wynik jest wejsciem
temperatury dla N1 (`csv_join`), N3 (kolumna `t12_c`) i N4.
Metoda: jednowymiarowy model przewodzenia ciepla z bilansem energii na powierzchni, zasilany godzinowymi danymi pogodowymi,
z **jednorazowa kalibracja pochlaniania promieniowania do odczytu pirometru** z pomiaru.

## 2. Co trzeba miec
1. CSV z pomiarami: czas **lokalny** (Europe/Warsaw, z czasem letnim/zimowym, naiwny, np. `2025-07-14 11:35:00`), polozenie WGS84
   (`latitude`, `longitude`) i odczyt pirometru `t_surface` [C]. Opcjonalnie `t_air` (kopiowana do wyniku, nie wchodzi do modelu).
2. Polaczenie z internetem **przy pierwszym uruchomieniu** (dane pogodowe z archiwum Open-Meteo) albo gotowy cache.
   To jedyne polaczenie sieciowe w calym pakiecie; wysylane sa tylko wspolrzedne siatki 0,05 stopnia i daty (nie wasze pliki).
3. Katalog cache (`meteo.cache_dir`): kolejne uruchomienia na tych samych dniach i komorkach nie pobieraja danych ponownie;
   `meteo.offline: true` wymusza prace wylacznie z cache.

## 3. Uruchomienie
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools layer_temp --config configs\n2_example.yaml
```
Okolo 550 obserwacji liczy sie w ok. 16 s (z cache). Opcje: `--dry-run`, `--out-dir`, `--log-level`, `--strict`.

## 4. Najwazniejsze ustawienia
| Klucz | Domyslnie | Znaczenie |
|---|---|---|
| `input.survey_csv`, `*_column` | — | plik i nazwy kolumn czasu, polozenia i pirometru |
| `input.passthrough` | `[]` | kolumny kopiowane do wyniku, np. `[chainage_m, file]` — wtedy wynik jest od razu wejsciem N3 |
| `model.depth_cm` | 12 | glebokosc 0-50 cm; zwalidowane tylko 10 i 12 cm |
| `model.thickness_cm` | null | gdy podane: glebokosc = grubosc/2 |
| `model.calibration` | `single_shot_ir_mass` | `none` = sama fizyka, bez kalibracji do pirometru |
| `meteo.offline` | false | tylko cache |
| `qc.season_months` | IV-X | poza sezonem: flaga `OUT_OF_SEASON` |
| `comparators.bells3` | false | dodatkowa kolumna `bells3_c` (klasyczny BELLS3, tylko do porownania) |
| `output.overwrite` | false | nadpisywanie istniejacych wynikow |

## 5. Wyniki
`layer_temp.csv`: `id, measured_at_local, latitude, longitude, t_surface, [t_air], depth_cm, t_layer, u95, a_sw, ts_sim, calib_flag,
grid_lat, grid_lon, sw_ma6, qc_flags, flags_text, t_layer_uncal, ir_masa, [bells3_c], [t12_c], [kolumny passthrough]`.
- `t_layer` — wynik [C] po kalibracji; `t_layer_uncal` — sama fizyka;
- `u95` — **orientacyjna** polowa przedzialu [C] (p. 7); `t12_c` — ta sama wartosc pod nazwa oczekiwana przez N3 (tylko gdy `depth_cm = 12`);
- `calib_flag` — wynik kalibracji: `ok`, `gate`, `bound_lo`, `bound_hi`, `nosim`.

`layer_temp_meta.json`: wersja i hash parametrow, licznik flag, uzyta konfiguracja, produkt i tryb Open-Meteo oraz informacja o dokladnosci.

## 6. Flagi (kolumna `flags_text`)
| Flaga | Znaczenie / co robic |
|---|---|
| `NIGHT` | brak sygnalu slonecznego (SW_ma6 < 5 W/m2): kalibracja do pirometru nie dziala, wynik bliski czystej fizyce |
| `CALIB_BOUND_HI` | pochlanianie na gornej granicy (1,0): pirometr cieplejszy niz model; **wynik czesto zanizony**, wystepuje u ok. 44 % pomiarow w zbiorze odniesienia |
| `CALIB_BOUND_LO` | pochlanianie na dolnej granicy (0,03) |
| `CALIB_GATE` | kalibracja nieidentyfikowalna (pochlanianie prawie nie wplywa na temperature powierzchni): uzyte wartosc domyslna |
| `CALIB_NOSIM`, `METEO_GAP` | brak/luka w danych pogodowych: wynik pusty lub niepewny |
| `TAIL_EXTRAPOLATED` | pomiar po ostatniej pobranej godzinie danych (pomiary po ok. 23:00): ostatnie dane utrzymane jako stale, bledy do ok. 0,2 C |
| `IR_MISSING` | brak odczytu pirometru: wartosc z fizyki bez kalibracji |
| `CALIB_OFF` | kalibracja wylaczona w konfiguracji |
| `SNOW`, `OUT_OF_SEASON` | snieg wg reanalizy / miesiac poza sezonem walidacji IV-X |
| `DEPTH_NOT_VALIDATED`, `DEPTH_OUT_OF_RANGE` | glebokosc inna niz 10 i 12 cm / poza 0-50 cm (wynik pusty) |
| `POSITION_OUT_OF_POLAND` | polozenie poza Polska (model kalibrowany dla klimatu Polski) |
| `SHADED_SITE_SUSPECTED` | zarezerwowana, **nigdy nie ustawiana** — narzedzie nie wykrywa zacienienia (p. 7) |

## 7. Dokladnosc i ograniczenia — przeczytac przed uzyciem wynikow
- **Dokladnosc.** RMSE 1,75 C dotyczy zbioru eksploracyjnego (549 pomiarow, 226 sesji), na ktorym model byl dopracowywany.
  Na **niezaleznym** zbiorze RMSE wynosi **2,73 C** [przedzial 2,44; 2,98]. Realnych bledow nalezy spodziewac sie bliskich drugiej liczby.
- `u95` to heurystyka: max(2 x RMSE dla pory doby, 2,2 C). Nie jest przedzialem ufnosci wyznaczonym statystycznie.
- **Teren otwarty.** Parametry sa z jednej stacji na odkrytym terenie. W miejscach zacienionych (drzewa, zabudowa, tunel, estakada)
  model zawyza temperature o 3-5 C; narzedzie tego nie wykrywa. Takich punktow nie podawac bez recznej oceny.
- **Pomiary nocne i wieczorne** (`NIGHT`) nie maja kalibracji do pirometru.
- Pomiar pirometrem musi byc wykonany na powierzchni nawierzchni, nie na znaku, pasie ani plamie wilgoci.
- Dane pogodowe sa reanaliza o siatce ok. 5 km (komorki 0,05 stopnia); lokalne zjawiska (mgla, mikroklimat) nie sa odwzorowane.
- Parametry modelu sa zamrozone (hash w pliku meta); zmiana parametrow wymaga nowej wersji pakietu.
- Brak polaczenia z internetem i brak cache (albo `offline: true` bez pokrycia): dla danej doby i komorki wynik jest **pusty**
  (flagi `METEO_GAP`/`CALIB_NOSIM`, ostrzezenie w logu); narzedzie nie zgaduje wartosci. Po uruchomieniu sprawdzic w pliku meta
  licznik tych flag, zanim wyniki trafia do N1/N3/N4.
