# narzedzia_tsd_fwd

Pakiet `tsdfwd_tools` — narzedzia TSD/FWD dla Zakladu Diagnostyki Nawierzchni IBDiM (N1-N4), odtwarzajace metody
raportu PW.S-1063 (Etap II). Projekt: `docs\PROJEKT.md`, inwentarz zrodel: `docs\INWENTARZ.md`, dziennik: `docs\DZIENNIK.md`.

Stan: E2 — N1 `fwd_tempcorr` (korekta temperaturowa ugiec FWD, z opcjonalnym `fwd_fit`) i N4 `tsd_fwd_compare` (tryb `pairs`). N2, N3 i tryb `geometry` N4 w kolejnych etapach.

## Srodowisko
```bash
conda create -p C:\ENV\narzedzia_tsd_fwd python=3.11
C:\ENV\narzedzia_tsd_fwd\python.exe -m pip install -e .[dev,mdb]
```

## Uruchomienie N1
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_tempcorr --config configs\n1_example.yaml
```
Opcje: `--dry-run` (bez zapisu), `--out-dir`, `--log-level`, `--strict` (kod 2 przy braku/niewaznej temperaturze).

## Uruchomienie N4 (porownanie TSD-FWD, tryb pairs)
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_fwd_compare --config configs\n4_pairs_example.yaml
```
Wejscie: pary TSD-FWD z temperaturami warstwy po obu stronach (CSV), opcjonalnie dodatkowe kolumny par i pary zerowe.
Wyniki: `agreement*.csv`, `conditions.csv`, `calibration.csv`, `null_checks.csv`, `conversion.csv`, `meta.json`, `report.html`.

## Dopasowanie wspolczynnikow z wlasnych wizyt (opcjonalnie)
```bash
C:\ENV
arzedzia_tsd_fwd\python.exe -m tsdfwd_tools fwd_fit --config configswd_fit_example.yaml
```
Wynik (`*_coefficients.csv`, format jak `e2a3_final_k_profile.csv`) mozna uzyc w N1: `coefficient_set: file`.

## Testy
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m pytest tests            # jednostkowe i regresji (@reference pomijane bez tests\local_paths.yaml)
```
Testy `@reference` czytaja dane projektow zrodlowych tylko do odczytu — sciezki w `tests\local_paths.yaml` (wzor: `tests\local_paths.example.yaml`).
