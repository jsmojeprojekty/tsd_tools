# Demonstracja narzedzi

```bash
C:\ENV\narzedzia_tsd_fwd\python.exe demo\uruchom_demo.py
```
Skrypt uruchamia N1-N4 na danych przykladowych (XLSX z `tests\data`, 30 pomiarow z `demo\dane`, przejazd B_1510off, pary z raportu i dane
syntetyczne), zapisuje wyniki w `demo\wyniki` (poza git) i buduje strone `demo\wyniki\PODSUMOWANIE.html` (wykresy, tabele, pliki wynikowe).
Dane zrodlowe projektow `sql_tsd_fwd` i `DOKTORAT` sa tylko czytane (sciezki z `tests\local_paths.yaml`).

Pochodzenie `dane\pomiary_pirometr_demo.csv`: wycinek 30 pomiarow (czas, polozenie, pirometr, powietrze, temperatura warstwy z sondy) ze zbioru
walidacyjnego modelu temperatury (projekt DOKTORAT, `temp_model`, zbior H v2); sluzy tylko do pokazu.
