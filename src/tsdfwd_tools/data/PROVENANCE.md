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

## params_TN.json
- zrodlo: projekt `C:\WORK\DOKTORAT\temp_model` (tylko odczyt), stan 2026-11-13: `output\E2-T01_calibration_summary_top-t_2cm.csv`
  (alpha, wariant global, stacja TN), `output\E2-T05_eb_surface_bc_params.csv` (parametry bilansu energii TN), dolny BC t50 i korekta IR
  = OLS na `output\E2-T07_features_TN.parquet` (2025-08-20..2026-08-19, bez okresow ze sniegiem, 43 302 wiersze).
- Zawartosc: alpha [m2/s], parametry EB (a_sw, h0, h1, c_vol, svf), wspolczynniki dolnego BC (beta50) i korekty IR (beta_ir), granice a_sw.
  Wersja sprzed poprawki czasu Open-Meteo (pre-omfix; roznica po poprawce <= 0,02 C). Teren otwarty; teren zacieniony nie jest obslugiwany.
- Kontrola: hash SHA-256 sekcji `parameters` w `layer_temp\params.py` (`EXPECTED_BUILTIN_HASH`) i test dryfu; odtworzenie zbioru H v2
  (RMSE 1,7488) w `tests\regression\test_n2_reference.py`.
