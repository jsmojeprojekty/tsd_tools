# Instrukcja `tsd_dsn` — przejazdy TSD z sieci -> XML DSN w skali FWD

Dla inzynierow Zakladu Diagnostyki Nawierzchni. Narzedzie jest nakladka na N2 (temperatura warstwy) i N3 (przetwarzanie TSD i XML); nie wprowadza nowych metod obliczen.

## 1. Do czego sluzy
Bierze **katalog przejazdow TSD** w eksporcie B_1510off i dla kazdego przejazdu: (1) wybiera z pliku probki pirometru i powietrza, (2) liczy temperature
warstwy 12 cm (N2, dane pogodowe z Open-Meteo lub z cache), (3) przetwarza przejazd w N3 (korekta do 20 C, calki, okna 10 m) i (4) zapisuje plik
`UC_<nazwa>.xml` w formacie DSN, z wartosciami w **skali FWD**.

## 2. Co trzeba miec
1. **Przejazdy B_1510off** w jednym katalogu: `*.raw.sup.txt`, `*.raw.sup.xls` lub `*.raw.sup.xlsx`. Eksport **nominalny** (puste pole `Re-calibrationfile`,
   z czujnikiem 1,51 m) jest odrzucany z komunikatem; trzeba go przeliczyc do B_1510off programem producenta.
2. **Tabela przejazdow** (CSV): `plik, kod_oddz, rok, droga, jezdnia, pas, km_start` (wymagane, bez wartosci domyslnych) oraz opcjonalnie `km_direction`
   (`increasing`/`decreasing`), `chainage_start_m`, `date_override`. `plik` = nazwa pliku z rozszerzeniem lub bez. Wzor: `configs\przejazdy_przyklad.csv`
   (**wartosci `TEST` sa fikcyjne**).
3. **Przelicznik TSD -> FWD** dla okresu kalibracji: liczba (`fwd_scale.to_fwd_multiplier`) albo `conversion.csv` z N4 (`fwd_scale.to_fwd_conversion_csv`).
   Zmienia sie po kazdej kalibracji, dlatego nie ma wartosci domyslnej.
4. **Dane pogodowe**: katalog cache Open-Meteo (`temperature.meteo_cache_dir`); przy pierwszym uruchomieniu na nowych dniach potrzebny internet
   (jedyne polaczenie sieciowe; wysylane sa tylko wspolrzedne siatki i daty), `meteo_offline: true` wymusza prace z cache.

## 3. Uruchomienie
```bash
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_dsn --config configs\tsd_dsn_example.yaml --dry-run
C:\ENV\narzedzia_tsd_fwd\python.exe -m tsdfwd_tools tsd_dsn --config configs\tsd_dsn_example.yaml
```
`--dry-run` sprawdza pliki, tabele przejazdow, eksport nominalny i probki temperatury, bez N2/N3 i bez zapisu. Kod wyjscia: 0 = wszystkie przejazdy
poprawne, 1 = co najmniej jeden przejazd z bledem (pozostale sa przetworzone), 2 (`--strict`) = brak temperatury w czesci probek.

## 4. Jak liczona jest temperatura warstwy (zalozenia do potwierdzenia)
- Probki co `temperature.sample_m` (100 m) wzdluz pikietazu, z poczatkiem i koncem przejazdu. W kazdej: mediana pirometru (`Temp Road`) i powietrza w oknie
  +-`window_m` (5 m), polozenie GPS i czas.
- Czas z kolumny `GPS time` jest traktowany jako **UTC** i zamieniany na czas lokalny Europe/Warsaw (z czasem letnim); N2 pracuje na czasie lokalnym.
  Gdy w danych jest czas lokalny: `temperature.gps_time_basis: local`. (Pole `GODZ` w XML podaje czas z pliku bez zamiany.)
- N2 liczy temperature warstwy dla probek (z kalibracja do pirometru), a N3 interpoluje ja liniowo po pikietazie. Zastrzezenia N2 (dokladnosc 2,73 C na
  zbiorze niezaleznym, teren zacieniony, pomiary nocne) obowiazuja bez zmian — patrz `INSTRUKCJA_N2.md`.

## 5. Wyniki
W `output.dir`:
- `batch_summary.csv` — jeden wiersz na przejazd: `status` (`ok`/`error`), `message`, data, liczba wierszy i waznych D0, probki temperatury (`n2_samples`,
  `n2_valid_t12`, `n2_flags`), liczba rekordow XML, przelicznik i jego zrodlo, sciezka XML;
- `batch_meta.json` — wersja, ustawienia temperatury i skali, liczniki;
- `<przejazd>/n2/` — probki (`<przejazd>_survey.csv`), `layer_temp.csv` i meta N2;
- `<przejazd>/n3/` — wyniki N3: okna 10 m, odcinki 50/100 m, `UC_<przejazd>.xml`, `*_n3_meta.json` (przelicznik, zrodlo, pola z niezweryfikowanym przelicznikiem).

## 6. Ograniczenia
- XML jest zgodny z opisem z zalacznika H p. 4.2, ale niezweryfikowany wzgledem `UC_Schema.xsd` (schemat ma dostarczyc Jacek).
- Przelicznik jest zweryfikowany dla D0; dla `D_200`, `D_300` i SCI nie (patrz `INSTRUKCJA_N3.md`).
- Narzedzie nie przelicza eksportu nominalnego do B_1510off.
- Narzedzie jest sprawdzone na danych syntetycznych; prawdziwy przejazd B_1510off z sieci jeszcze nie byl przetwarzany.
