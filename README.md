# narzedzia_tsd_fwd

Pakiet `tsdfwd_tools` — narzedzia TSD/FWD dla Zakladu Diagnostyki Nawierzchni IBDiM (N1-N4), odtwarzajace metody
raportu PW.S-1063 (Etap II). Projekt: `docs\PROJEKT.md`, inwentarz zrodel: `docs\INWENTARZ.md`, dziennik: `docs\DZIENNIK.md`.

Stan: E2f — N1 `fwd_tempcorr` (z opcjonalnym `fwd_fit`), N2 `layer_temp`, N3 `tsd_network` i N4 `tsd_fwd_compare` (tryby `pairs` i `geometry`) oraz instrukcje dla inzynierow. Tryb `geometry` wykrywa tez odcinki wspolne (Tab. 3.2) i zapisuje raport przegladu `section_review.html`. Opcjonalny estymator lambdy z powtorzen (`geometry.lambda_est`). Gdy wiersze TSD maja profil podluzny, przejazdy sa wyrownywane profilem (`geometry.align`). Os z przejazdow TSD ze scalaniem duplikatow pasa (`geometry.merge_lanes`). Nie ma drogomierza zakotwiczonego w strefach zlego GPS.

## Instrukcje dla inzynierow
`docs\INSTRUKCJA_N1.md` (korekta temperaturowa FWD), `docs\INSTRUKCJA_N2.md` (temperatura warstwy), `docs\INSTRUKCJA_N3.md` (TSD na sieci + XML DSN),
`docs\INSTRUKCJA_N4.md` (porownanie TSD-FWD). Kazda opisuje dane wejsciowe, uruchomienie, wyniki, flagi i ograniczenia.

## Odtwarzalnosc wzgledem raportu
`docs\ODTWARZALNOSC.md` — zalacznik generowany z przebiegu testow: dla kazdego numeru testu (T-N1-01 ... T-N4-18) wartosc referencyjna z raportu
lub bazy zrodlowej, tolerancja i wynik; rozbieznosci i ograniczenia. Odswiezenie: `python docs\odtwarzalnosc\zbuduj_odtwarzalnosc.py`
(rejestr powiazan numer testu - punkt raportu - testy: `docs\odtwarzalnosc\rejestr.yaml`).

## Srodowisko
```bash
conda create -p C:\ENV\narzedzia_tsd_fwd python=3.11
C:\ENV\narzedzia_tsd_fwd\python.exe -m pip install -e .[dev,mdb,parquet]
```
Dodatek `parquet` (pyarrow) jest potrzebny tylko do odczytu cache Open-Meteo zapisanego w formacie parquet (cache referencyjny); cache zapisywany przez N2 jest w CSV.

## Uruchomienie N1
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_tempcorr --config configs\n1_example.yaml
```
Opcje: `--dry-run` (bez zapisu), `--out-dir`, `--log-level`, `--strict` (kod 2 przy braku/niewaznej temperaturze).

## Uruchomienie N2 (temperatura warstwy asfaltowej)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools layer_temp --config configs\n2_example.yaml
```
Wejscie: CSV z kolumnami czasu (lokalny z DST), pozycji WGS84 i odczytu pirometru. Model: fizyka 1-D z jednorazowa kalibracja do pirometru
(teren otwarty), meteo z archiwum Open-Meteo (jedyne polaczenie sieciowe; `meteo.offline: true` = tylko cache). Wyniki: `layer_temp.csv`
(T warstwy, u95, flagi) i `layer_temp_meta.json`. Dokladnosc: RMSE 1,75 C na zbiorze eksploracyjnym, 2,73 C na niezaleznym.

## Uruchomienie N3 (TSD na sieci + XML DSN)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_network --config configs\n3_example.yaml
```
Wejscie: eksport TSD B_1510off (`*.raw.sup.txt`) + temperatura warstwy 12 cm (CSV z N2: `chainage_m`, `t12_c`). Wyniki: okna +-5 m co 10 m
(`*_windows_10m.csv`), agregacje 50/100 m (`*_agg_*m.csv`), opcjonalnie wiersze 1 m, plik meta i XML DSN `UC` (zal. H p. 4.2).

## Uruchomienie N4 (porownanie TSD-FWD, tryb pairs)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_fwd_compare --config configs\n4_pairs_example.yaml
```
Wejscie: pary TSD-FWD z temperaturami warstwy po obu stronach (CSV), opcjonalnie dodatkowe kolumny par i pary zerowe.
Wyniki: `agreement*.csv`, `conditions.csv`, `calibration.csv`, `null_checks.csv`, `conversion.csv`, `meta.json`, `report.html`.

## Uruchomienie N4 (tryb geometry: pary z geometrii)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_fwd_compare --config configs\n4_geometry_example.yaml
```
Wejscie: wiersze TSD (np. `*_rows.csv` z N3, surowy pikietaz) i stacje FWD (CSV z aparatem, data, D0 i temperatura z N1). N4 buduje wspolna os pasa,
wykrywa odcinki wspolne (Tab. 3.2), ustala polozenie plyty FWD, tworzy pary geometryczne (okna +-5 m) i pary zerowe, po czym liczy te same miary co w trybie `pairs`.

## Dopasowanie wspolczynnikow z wlasnych wizyt (opcjonalnie)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_fit --config configs\fwd_fit_example.yaml
```
Wynik (`*_coefficients.csv`, format jak `e2a3_final_k_profile.csv`) mozna uzyc w N1: `coefficient_set: file`.

## Testy
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m pytest tests            # jednostkowe i regresji (@reference pomijane bez tests\local_paths.yaml)
```
Testy `@reference` czytaja dane projektow zrodlowych tylko do odczytu — sciezki w `tests\local_paths.yaml` (wzor: `tests\local_paths.example.yaml`).
