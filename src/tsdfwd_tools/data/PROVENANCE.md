# Pochodzenie plikow danych pakietu

## e2a3_final_k_profile.csv
- zrodlo: `C:\projects\sql_tsd_fwd\tabele\e2a3_final_k_profile.csv`, stan 2026-10-15 12:45, MD5 `ac5f657401c75b81d67b74ace4fbb7b0`
  (kopia bajt w bajt; repozytorium zrodlowe `c67f7fe`).
- Zawartosc: wspolczynniki korekty temperaturowej k (`k_guide`, postac liniowa) i beta (`beta_pct` [%/C], postac wykladnicza)
  dla 12 wskaznikow (D0..D1800, SCI300, BDI, BCI) w trzech zbiorach (`TN`, `PODKOWA`, `lacznie`); pochodzenie: P040 (E3F),
  wizyty z T_mid z czujnikow stacji 5 <= T < 30 C, bez stycznia, efekt staly punkt x miesiac, log-link (quasi-Poisson),
  500 replik bootstrapu po dniach (CI). Uzywany jest zbior `lacznie` (n = 414 wizyt).
- Uwaga: wspolczynniki wyznaczone na pakietach 24-25 cm (stanowiska TN i Podkowa), jeden rok danych; wskazniki SCI300/BDI/BCI
  z tego pliku NIE sa uzywane do korekty (wskazniki liczone wylacznie z ugiec skorygowanych).

## tab71.csv
- zrodlo: raport PW.S-1063 v1.12, Tab. 7.1 (wartosci zaokraglone; D450 0,0096->0,010, D900 0,00329->0,003, D300 0,01234->0,012).
