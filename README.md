# narzedzia_tsd_fwd

Pakiet `tsdfwd_tools` — narzedzia TSD/FWD dla Zakladu Diagnostyki Nawierzchni IBDiM (N1-N4), odtwarzajace metody
raportu PW.S-1063 (Etap II). Projekt: `docs\PROJEKT.md`, inwentarz zrodel: `docs\INWENTARZ.md`, dziennik: `docs\DZIENNIK.md`.

Stan: E1 — N1 `fwd_tempcorr` (korekta temperaturowa ugiec FWD). N2-N4 w kolejnych etapach.

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

## Testy
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m pytest tests            # jednostkowe i regresji (@reference pomijane bez tests\local_paths.yaml)
```
Testy `@reference` czytaja dane projektow zrodlowych tylko do odczytu — sciezki w `tests\local_paths.yaml` (wzor: `tests\local_paths.example.yaml`).
