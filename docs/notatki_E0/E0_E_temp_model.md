# E0_E - audyt C:\WORK\DOKTORAT\temp_model pod narzedzie N2 `layer_temp`

Zakres: odczyt (nic nie zapisano/przeniesiono/skasowano w C:\WORK\DOKTORAT). Python uruchamiany tylko do odczytu
(`-B -I`, brak zapisu bytecode; pliki robocze wylacznie w katalogu scratchpad). Data audytu 2026-11-13.
Notacja: [K] = potwierdzone w kodzie/pliku, [P] = policzone przeze mnie odczytem, [W] = wniosek/hipoteza (niezweryfikowana).

---------------------------------------------------------------------------------------------------

## 0. Najwazniejsze (skrot)

1. **Sciezka kodu "fizyka z kalibracja jednorazowa do pirometru"** = `z14c_candidates.process_unit` (mode `single`, target `masa`) ->
   `z14b_single_shot.calibrate` (brentq po `a_sw`) -> `z14lite_validate.predict_block` -> `depth_thickness_study.sim_eb_all_depths`
   -> `energy_balance_bc.simulate_eb`. Kolumna wynikowa: `phys_single_masa` (parquet `Z14c_candidates.parquet`). Dotyczy WYLACZNIE klasy terenu TN
   ("otwarta"). XGBoost/hybryda nie bierze udzialu w wartosci (jest dopasowywana "przy okazji" w `class_fit`, ale nie jest uzyta).
2. **Plik z RMSE 1,75**: `C:\WORK\DOKTORAT\temp_model\output\z14lite\z14d\E3-T46_z14d_H_v2.csv`, wiersz
   `"fizyka TN, kalibracja jednorazowa (IR_masa)"`: n=549, rmse=1.7486468918, mae=1.4038706, bias=+0.2652546, R2=0.8731, rmse_lo/hi=1.6193/1.8689
   (bootstrap po sesjach, 2000 powt., seed 42). Sesji 226 ([K] w kolumnie `zbior`).
3. **Niezaleznie odtworzylem** wartosc ze zrodel: (a) z `Z14c_candidates.parquet` + `z14lite_fwd_walidacja_v3.csv`: 1.7486 / 1.4039 / +0.2653 (n=549, 226 sesji);
   (b) wlasna, ~100-liniowa replika fizyki (bez importow z projektu, tylko numpy/pandas/scipy + zamrozone stale) na cache `openmeteo_cache_utc`:
   **RMSE 1.7488, MAE 1.4042, bias +0.2649**, flagi 294 ok / 244 bound_hi / 11 gate (identyczne co referencja); 544/549 obs zgodnych do 1e-12 C,
   5 obs (pomiar po 23:00 w ostatniej dobie okna cache) roznia sie do 0.18 C - patrz pulapka P4. Replika zgodna tez z 240 losowymi wierszami Z15 (1e-12).
4. **Rdzen produktu N2 jest maly**: potrzebne tylko EB-1D (solve_banded), 5 zmiennych Open-Meteo, 4 zamrozone zestawy stalych (alpha, parametry EB, beta50[5], beta_ir[5]).
   Cala reszta repo (hybryda B, XGBoost, foldy, bootstrap, E2-kalibracje) NIE jest potrzebna.
5. **Uwaga merytoryczna**: referencja 1,75 to zbior H, na ktorym metode *zaprojektowano* (Z14b - eksploracyjnie, PO Z14-lite). Na zbiorze potwierdzajacym C (wizyty na stanowiskach)
   ta sama metoda dala RMSE 2,73 [2,44; 2,98], bias -1,45 ("POPRAWA NIEPOTWIERDZONA"; po korekcie celu C v2: 3,08 [2,78; 3,36]). Do testu regresji wolno uzywac H v2
   (to test powtarzalnosci), ale nie jako deklaracji dokladnosci produktu.

---------------------------------------------------------------------------------------------------

## 1. Identyfikacja sciezki "fizyka + kalibracja jednorazowa" i pliku referencyjnego

### 1.1 Lancuch wywolan (jedna obserwacja = jedna chwila t, IR, T_air, lat/lon)
```
wejscie: ts (lokalny naiwny, Europe/Warsaw z DST), lat, lon, t_surface (IR aparatu FWD), t_air (aparat)
 |
 +- komorka OM: q_lat = round(lat/0.05)*0.05, q_lon analogicznie  [z14lite_validate.GRID_DEG]
 +- om = zv.load_cell_meteo(cache_utc, q_lat, q_lon, lo=day-35d, hi)            # godzinowe OM, czas lokalny
 +- frame = zs.build_frame(om, t_min, t_max)                                   # siatka 10 min od day-35d do ceil(t,10min)
 |     = zv.network_frame -> eb.meteo_to_10min (interp. liniowa; swr przesuniete o -30 min) + kalendarz + MA1d/7d/30d
 +- t50 = ob.ols_predict(frame, T50_FEATURES, beta50)                           # dolny BC: 4 cechy OLS
 +- dhat = ob.ir_corr_predict(frame, beta_ir); ir_masa = IR - dhat(t)           # korekta IR->"masa" (w istocie ~t_2cm)
 +- zs.calibrate(frame, t50, fit, t_start=day-3d, t_end=ceil(t)+10min, t, ir_masa)
 |     Ts(a) = sim_eb_all_depths(...).t_0cm w chwili t, przy a_sw = a
 |     ts_lo=Ts(a=0.03), ts_hi=Ts(a=1.0)
 |     |ts_hi-ts_lo| < GATE_C=1.0 C  -> flaga "gate", a = a_default (1.0)         [pora nocna / brak slonca]
 |     f_lo*f_hi > 0                 -> brzeg bliższy celowi: "bound_lo"/"bound_hi"
 |     inaczej brentq(Ts(a)-ir_masa, 0.03, 1.0, xtol=1e-3) -> "ok"
 +- a_use = a_default gdy flaga in {gate, nosim}, inaczej a
 +- zv.predict_block(..., fit z eb_p['a_sw']=a_use) -> kolumna phys_120mm = T na 12 cm z symulacji EB (NIE hybryda)
```
`phys_single_masa` w `z14c_candidates.process_unit` = `pred_at(om, t, ir, air, fit, a_use)[0]`. Ta sama funkcja w `z15_temperatures.predict_side` (`t12_cal`).

### 1.2 Wartosc referencyjna - plik i kolumny
- **Plik zrodlowy metryk**: `C:\WORK\DOKTORAT\temp_model\output\z14lite\z14d\E3-T46_z14d_H_v2.csv`
  (kolumny: `zbior, model, n, rmse, mae, bias, R2, rmse_lo, rmse_hi, d_rmse_vs_main, d_lo, d_hi, istotna`).
  Wiersz `fizyka TN, kalibracja jednorazowa (IR_masa)`:
  n=549 | rmse=1.7486468918319669 | mae=1.403870123763068 | bias=+0.26525456359165744 | R2=0.873109635587412 | CI RMSE [1.6193; 1.8689].
  Zbior: `H v2 (549 obs. bez 16322; IV-X; 12 cm; n = 549, sesji = 226)`.
- **Dane wierszowe** (z nich liczy sie wszystko): `...\output\z14lite\z14c\Z14c_candidates.parquet` (1700 wierszy = 850 obs x 2 klasy; 48 kolumn),
  kolumny: `phys_single_masa` (predykcja), `t_layer` (pomiar w otworze), `klasa=="otwarta (TN)"`, `flag_single_masa`, `a_single_masa`, `hour`, `ts_obs`, `unit_id`.
  Filtr H (z14d_report.main / z15b_tab42_robust): `asphalt_temp_trusted==1 & asphalt_status in {entry_first, entry_change} & month in 4..10` + skonczone wszystkie 4 modele
  (dolaczenie metadanych z `z14lite_fwd_walidacja_v3.csv` po `obs_group_id`). Stacja 16322 wylaczona juz w `z14c_candidates.build_tasks` ([K], decyzja 2026-11-03).
- **[P] Przeliczenie z parquet (odczytem)**: n=549, sesji=226; `phys_single_masa`: RMSE 1.7486, MAE 1.4039, bias +0.2653.
  Pozostale kolumny: `phys_uncal` (fizyka TN bez kalibracji) 2.0872 / 1.6974 / +0.9455; `hybrid_uncal` 2.1180 / 1.7066 / +1.0271; `bells3` 2.4065 / 1.8160 / -0.3432
  (= E3-T46, E3-T47/Z15b_T42).
- Znak bledu: **predykcja - pomiar** (bias +0.27 = model nieco za cieply). [K] `z14lite_report.metrics`.
- Rozklad (E3-T47, Z15b_T42_robust.csv): mediana |e| = 1.2155 [1.105; 1.342], P90 |e| = 2.817 [2.590; 2.987];
  RMSE wg pory (godz. lokalna aparatu): 0-6 h: 2.167 (n=49, bias -0.04) | 6-12: 1.378 (n=226, +0.15) | 12-18: 1.889 (n=237, +0.25) | 18-24: 2.167 (n=37, +1.48).
  RMSE wg lat: 2020 1.72 (118) / 2021 1.89 (114) / 2022 1.74 (141) / 2023 2.33 (30) / 2024 1.70 (63) / 2025 1.44 (43) / 2026 1.22 (40) [E3-T47 / raport_Z14d.md].
  77% (73% dla tego modelu) wariancji bledu jest MIEDZY sesjami (stala "wina miejsca"), nie wewnatrz sesji.
- [P] RMSE wg flagi kalibracji (H, TN, single/masa): ok n=294 1.691 (bias +0.28) | bound_hi n=244 1.813 (+0.18) | gate n=11 1.804 (+1.75).
  [P] wg SW (sw_ma6 = srednia 6 h): <=5 W/m2 (noc) n=36 RMSE 2.163 | 5-100 n=102 1.430 | 100-300 n=173 1.534 | >300 n=238 1.939.

### 1.3 UWAGA: numeracja "Tab. 4.3"
W kodzie `z15b_tab42_robust.py` wynik H v2 (549/226) jest podpisany jako **"Tab. 4.2 raportu PW.S-1063"**, a "Tab. 4.3" w `z15b_tab41_tab43_robust.py` to zbior C v2
(LAMB/Podkowa/TN; RMSE 2.48 / 3.65 / 2.69 / 2.88 dla modelu finalnego), a nie H. Tab. 4.1 = hybryda A/B na stanowiskach (E3-T07). Jesli raport PW.S-1063 ma inna numeracje
niz kod - do potwierdzenia z autorem (pytanie Q1). Liczby 1,75 / 1,40 / +0,27 / 549 / 226 pasuja WYLACZNIE do zbioru H v2 = E3-T46.

---------------------------------------------------------------------------------------------------

## 2. Parametry zamrozone potrzebne przez sciezke (wyciagniete odczytem; do wpisania w `params.json` pakietu)

Zrodla w repo: `output\E2-T01_calibration_summary_top-t_2cm.csv` (alpha), `output\E2-T05_eb_surface_bc_params.csv` (EB), oraz OLS liczony w `class_fit`
(`zv.fit_station_models` -> `ob.fit_ols`; `ob.fit_ir_corr`) na `output\E2-T07_features_TN.parquet`, wiersze 2025-08-20..2026-08-19 z `snow_period==False` (43 302 wiersze po dropna).
- **alpha (TN, global)** = 1.1180916449068726e-06 m2/s (RMSE kalibracji 0.359 C).
- **Parametry EB (TN)**: a_sw = 1.0 (gorna granica; w pliku 0.99999999999995), h0 = 13.703653335884345 W/m2K, h1 = 0.8635956775154445 W s/m3K,
  c_vol = 2491672.4664717293 J/m3K, svf = 1.0. (=> k = alpha*c_vol = 2.786 W/mK). Granice PARAM_SPEC: a_sw [0.03; 1.0], h0 [1; 30], h1 [0; 15], c_vol [1.2e6; 3.2e6], svf [0.2; 1.0].
- **beta50** (dolny BC, [wyraz wolny, sin_doy, cos_doy, MA7, MA30]) [P]: `[4.345912232478229, -0.5238792264652146, -3.479711280281572, 0.5972550045675352, 0.2659045471826211]`
  gdzie sin_doy = sin(2*pi*doy/365.25), MA7/MA30 = srednia krocząca po siatce 10 min z `temperature_2m` OM (okna 7*144/30*144 krokow; min_periods 6*144/25*144).
  Interpretacja: t_50cm ~ T_powietrza_wygladzona + cykl roczny (dopasowane do JEDNEGO roku, JEDNEJ stacji, Warszawa).
- **beta_ir** (korekta IR->masa; delta = IR - t_2cm; cechy [1, swr_kW, swr_kW*wiatr, clear_night, clear_night*wiatr]) [P]:
  `[-2.786519348653504, 5.08355350162691, -0.33793970242554944, -2.3739849783973197, 0.34833124664883247]`;
  swr_kW = swr/1000; clear_night = (1 - cloud/100)*[swr<5 W/m2]. Uwaga: to NIE sa wspolczynniki E2-T03 (tamte: fit godzinowy, inna probka) - ob.fit_ir_corr liczy na siatce 10 min.
- Stale solvera: DZ=0.01 m, NZ=51 wezlow (0-50 cm), DT=600 s, SPINUP_OP=288 krokow (48 h, wyniki NaN), LEAD=3 doby przed dniem pomiaru, HIST_DAYS=35, GRID_DEG=0.05,
  GATE_C=1.0, XTOL=1e-3, EPS_SURF=0.95, sigma=5.67e-8, Brunt eps_clear=0.605+0.048*sqrt(e_hPa), e=6.112*exp(17.62*Td/(243.12+Td)).
- Sprawdzenie [P]: z tymi stalymi replika (scratchpad `e0_standalone.py`) daje 1.7488 / 1.4042 / +0.2649 na H (patrz sekcja 0 pkt 3).
  Stale beta50/beta_ir dla produktu NALEZY zamrozic w pliku z hashem (inaczej ich zmiana przy kazdym uczeniu zmieni wyniki); zrodlo - E2-T07 z `output\` (Sept 2026, OM z etykietami UTC+2),
  a nie `_omfix_check` (po poprawce czasu OM; roznice TN <=0.4% w EB, patrz Z14d). Regresja referencji 1,749 zachodzi dla stalych z `output\`.

---------------------------------------------------------------------------------------------------

## 3. Opis skryptow (src\)

Konwencja projektu (CLAUDE.md): komentarze po polsku bez diakrytykow, nazwy po angielsku; wyniki z prefiksem ID `E2-/E3-...`; pliki zrodlowe nigdy nie nadpisywane.
Kazdy skrypt ma `main()` pod `__main__` i pisze do `output\...` (czyli NIE uruchamiac - zapisuje).

### 3.1 `fourier_1d.py` (E2, pkt 2) - solver przewodnictwa Dirichlet/Dirichlet
- Publiczne: `simulate(surface_series, bottom_series, init_profile_depths, init_profile_temps, alpha=1.0e-6, depth=0.50, nz=51, dt_s=600.0) -> (z, T[nt,nz])`;
  `run_window(df, start, days, alpha) -> (rmse_dict, rmse_mean)`; CLI `--start --days --alpha --calibrate`.
- Liczy: dT/dt = d/dz(alpha dT/dz), backward Euler, tridiagonalny `solve_banded` (macierz stala w czasie), alpha skalarne lub wektor (srednia harmoniczna na interfejsach).
  BC: gora = zadana (t_0cm lub t_2cm), dol = zadana t_50cm. Siatka: 1 cm (nz=51), dt=600 s. Start: interpolacja liniowa pomiarow. Zero fizyki powierzchni.
- Wejscia: DataFrame stacji (`load_station_data`), kolumny t_0cm..t_50cm. Wyjscie: pole T(z,t), RMSE na czujnikach 2-28 cm.
- Zaleznosci: numpy, pandas, scipy, `load_station_data`. Stale: zakres alpha 3e-7..2e-6 (siatka 25 geom.), depth 0.5 m.
- Uzywany dalej jako `simulate` w `operational_bc.sim_irc_tmid` i `baselines_e3` (stacjonarny profil z korekta IR) - **NIE potrzebny w N2** (wariant "stationary", wymaga ciaglej serii IR).
- Pulapka: wezly brzegowe sa zadane wartoscia - dla pirometru (t_0cm) daje bias ~-0.9..-2.3 C (wniosek E2: pirometr nie nadaje sie na Dirichleta).

### 3.2 `energy_balance_bc.py` (E2 pkt 5) - **serce modelu N2**
- Publiczne: `load_alphas(out_dir)`; `longwave_down(met)`; `meteo_to_10min(om, index)`; `simulate_eb(seg, met, alpha, p) -> DataFrame (kolumny czujnikow, t_0cm = Ts)`;
  `prepare_station(csv_path, om)`; `eb_residuals(prepared, alpha, p, cols)`; `objective(prepared, alpha, p, cols)`;
  `calibrate_eb(prepared, alpha, param_names, maxiter)`; `dirichlet_residuals(prepared, alpha, top_col, attrs)`; `rmse_by_depth(res_long, model, station)`; `plot_*`; `main`.
- Rownanie (wezel powierzchniowy, polowa komorki): `C*dz/2 * dTs/dt = a_sw*SW + eps*(Ld_eff - sigma*Ts^4) + (h0 + h1*U)*(Ta - Ts) + k*(T1 - Ts)/dz`.
  Ld_eff = svf*Ld_sky + (1-svf)*sigma*Ta^4; Ld_sky = eps_sky*sigma*Ta^4, eps_sky = cc + (1-cc)*eps_clear (Crawford-Duchon + Brunt); czlon sigma*Ts^4 zlinearyzowany
  wokol Ts z poprzedniego kroku (lw_lin = 4*eps*sigma*Ts^3; rhs: 3*eps*sigma*Ts^4). Wnetrze: alpha*d2T/dz2, dol: Dirichlet t_50cm (K). k = alpha*c_vol. dt=600 s, dz=1 cm, 51 wezlow.
  Init: profil z pomiaru (E2) / liniowy Ta->t50 (E3, `sim_eb_all_depths`). Rozbieg 6 h (E2, `ca.SPINUP_STEPS=36`) lub 48 h (E3, `SPINUP_OP=288`).
- Kalibracja (E2): Nelder-Mead (adaptive, maxiter 1200) po a_sw, h0, h1, c_vol (+svf tylko Podkowa), funkcja celu = sredni RMSE po czujnikach 2-28 cm, maska sniegu (snow_depth > 5 mm wylaczone).
- Wejscia OM: `temperature_2m` [C], `dew_point_2m` [C], `wind_speed_10m` [m/s], `cloud_cover` [%], `shortwave_radiation` [W/m2, srednia poprzedzajacej godziny], `snow_depth` [m]
  (w `meteo_to_10min` kolumna `snow_depth` jest WYMAGANA, wiec musi byc w cache). Wyjscie: Ts i temperatury na glebokosciach czujnikow (**funkcja zwraca tylko glebokosci czujnikow**, nie cala siatke).
- Zaleznosci: numpy, pandas, scipy (solve_banded, minimize), matplotlib, `calibrate_alpha` (stan globalny `ca.configure` - konfiguracja modulu mutowana przy kazdym wywolaniu!), `load_station_data`.
- Stale na sztywno: EPS_SURF=0.95, SIGMA=5.67e-8, SNOW_MAX_M=0.005, KELVIN=273.15, PARAM_SPEC (granice i starty), formuly Brunta; interpolacja swr: etykieta -30 min.
- Pulapki: (a) a_sw=0.03..1.0, TN siedzi na gornej granicy 1.0 (reanaliza zaniza SW o 6-7% w dni bezchmurne [E3-T13]) - w produkcie "kalibracja" moze tylko ZMNIEJSZAC a_sw;
  (b) Podkowa: c_vol na dolnej granicy 1.2e6, svf=0.316 - parametry sprzezone, nieseparowalne (T24: wariant "tylko a_sw/svf z B" daje 6.13 C na TN);
  (c) `ca.configure` zmienia globalne SUB_COLS/NZ - kolejnosc wywolan ma znaczenie; (d) `main` zapisuje E2-T05/T06, F10-F12 do `output\` (nadpisze referencje!).

### 3.3 `operational_bc.py` (E3 pkt 3/3a) - dolny BC + korekta IR + profile operacyjne
- Publiczne: `load_full_features(out_dir)`; `fit_ols(df, feature_cols, y) -> beta`; `ols_predict(df, feature_cols, beta) -> Series`; `ir_corr_features(df)`;
  `fit_ir_corr(train_df) -> beta[5]`; `ir_corr_predict(df, beta)`; `fit_ir_corr_seasonal(train_df, min_rows=500)`; `ir_corr_predict_seasonal(df, betas)`;
  `contiguous_runs(index, valid)`; `build_common_support(features, with_lag=True)`; `sim_irc_tmid(df, window, top, bottom, station, alpha)`;
  `sim_eb_tmid_ts(df, window, bottom, station, alpha, p) -> (t_mid, Ts)`; `sim_eb_tmid(df, window, bottom, station, alpha, p)`;
  `class OperationalModels(features, out_dir)` (`predict_t50`, `predict_op_irc`, `predict_op_eb`, `predict_xgb`, `eb_for(fold)`, `predict_fn(key)`...);
  `export_fold_predictions(models, out_dir)`; `bells3_o_bar(out_dir, profile="survey", split="monthly")`; `pooled`, `plot_profiles`, `main`.
- Liczy: t50_hat = OLS(sin_doy, cos_doy, MA7, MA30 temperatury powietrza OM); delta_IR = OLS(swr_kW, swr*wiatr, clear_night, clear_night*wiatr); symulacje przewodnictwa (profil "stationary", Dirichlet = IR-delta)
  i EB (profil "survey", dol = t50_hat) na ciaglych oknach; wspolne wsparcie czasowe dla porownan modeli; `main` liczy E3-T03/T04/F02.
- **Z tego pliku N2 bierze**: `fit_ols`, `ols_predict`, `fit_ir_corr`, `ir_corr_features`, `ir_corr_predict`, `contiguous_runs`, `T50_FEATURES`, `SPINUP_OP`. Reszta = framework walidacyjny (badawczy).
- Stale: T50_FEATURES, IRC_TARGET=(op_t_surf_ir, target_t_2cm), SPINUP_OP=288, DT_S=600, DZ=0.01, CS_LAG_STEPS=18, SEASONS.
- Pulapki: kolumny `op_om_ta_ma7d/30d` zaleza od dlugosci historii (wymagane >=25 dni, dlatego HIST_DAYS=35); beta_ir uczone na pirometrze **Qulon-RTS stacji**, a stosowane do pirometru aparatu FWD (zastrzezenie autora: roznia sie);
  delta = IR - t_2cm, a kalibracja dopasowuje Ts wezla z=0 do "IR_masa" (~t_2cm) - niescisle fizycznie (pytanie Q4).

### 3.4 `surface_calib.py` (E3 Z9b) - BADAWCZY, pominac
- Publiczne: `station_context(features, out_dir, A, B)`; `params_from(ctx, a_sw, svf)`; `sim_window_ts(ctx, win, p)`; `calibrate(ctx, win, target, maxiter=300)`; `eval_tmid(ctx, p, exclude=None)`;
  `window_of(start, days)`; `run_case(ctx, start, days, target, maxiter=300)`; `reference_bars(ctx)`; `hybrid_on_calibrated(features, out_dir, ctx, p_cal, exclude)`; `summary`, `plot`, `main`.
- Co: kalibracja a_SW i svf (Nelder-Mead) do N dob ciaglego odczytu pirometru stacji B (okna 1/3/7/14 dob, 3 polozenia), parametry h0,h1,c_vol,alpha,t50,korekta IR ze stacji A; ocena T_mid IV-X.
  Wynik: 1.60/2.12 C (7 dob). To koncepcyjny poprzednik "kalibracji jednorazowej" (tu na wielu dobach); N2 uzywa wersji jednorazowej z jednej chwili (`z14b_single_shot.calibrate`, brentq).
- Zaleznosci: scipy.minimize, `coldstart_test` (xgboost), `hybrid_e3`, `validation_protocol`. Nie importowac do N2.

### 3.5 `ir_mass_relation.py` (E2 pkt 5) - badawczy (benchmark korekty pirometru)
- Publiczne: `build_hourly(station_csv, meteo_parquet)`; `fit_ols(d)`; `fit_ols_seasonal(d, min_rows=500)`; `evaluate(d, delta_hat)`; `plot_delta_diurnal`, `plot_delta_drivers`, `main`.
- Co: OLS delta=t_0cm-t_2cm ~ 1 + swr_kW + swr_kW*wiatr + clear_night + clear_night*wiatr (godzinowo, wyklucza snieg), wariant globalny i sezonowy; zapisuje E2-T03/T04 (wspolczynniki).
  RMSE odtworzenia t_2cm: TN 3.04->1.61, Podkowa 1.74->0.92 C. Wejscie: CSV stacji + `openmeteo_ibdim_hourly.parquet`.
- Pulapka: **to nie sa wspolczynniki uzywane w sciezce N2** - tam `ob.fit_ir_corr` (10 min, rok, bez sniegu); E2-T03 sluzy tylko do kolumny `phys_delta_ir` w tabelach cech.
  Prog nocy `NIGHT_SWR=5 W/m2` jest wspolny (clear_night). Czas OM: godzinowe etykiety "right".

### 3.6 `fetch_openmeteo.py` - pobieranie (jedyne polaczenie sieciowe) [szczegoly: sekcja 5]
- Publiczne: `fetch(start, end, lat=IBDIM_LAT, lon=IBDIM_LON) -> (DataFrame, meta)`; `om_utc_to_local(df)`; `check_time_alignment(df_meteo, station_csv)`;
  CLI `--start --end --out --check-station`. Stale: IBDIM_LAT=52.2676, IBDIM_LON=21.0246, API_URL, HOURLY_VARS (15), DEFAULT_START=2025-07-01, DEFAULT_END=2026-08-19.
- Wejscie: daty LOKALNE zakresu. Wyjscie: parquet godzinowy z indeksem czasu lokalnego Europe/Warsaw (naiwnym) + `_meta.json`.

### 3.7 `z14lite_fetch_openmeteo.py` - Z14-lite krok 1 (pobieranie dla sieci)
- Publiczne: `load_points(csv_path=SRC_CSV)`; `load_micro_windows(csv_path=MICRO_OM_CSV)`; `plan_queries(d)`; `plan_micro_queries(d)`; `haversine_km(lat1, lon1, lat2, lon2)`;
  `cache_name(lat, lon, start, end)`; `fetch_one(lat, lon, start, end, cache_dir) -> (status, meta)` (status: cache|fetched|limit|error); `main`. CLI `--plan --cache-name --micro --out`.
- Co: wspolrzedne -> siatka 0.05 st.; okno [dzien-35 d, dzien] scalane gdy przerwa < 10 d; 1 zapytanie/komorka/okno; cache per zapytanie (parquet+json); 429 -> 60 s i do 5 prob; zerwane polaczenia -> 5*n s;
  limit dzienny -> zapis stanu i koniec (bez uzupelniania brakow). Raport JSON (`Z14lite_openmeteo_report_utc.json`: 332 zapytania, 96 komorek, max odleglosc 3.16 km, mediana 1.83 km, 0 brakow).
- Stale: GRID_DEG=0.05, HIST_DAYS=35, MERGE_GAP_DAYS=10, SLEEP_S=2.0, MAX_RETRY=5, RETRY_WAIT_S=60. Domyslny cache od 2026-11-04: `openmeteo_cache_utc` (stary `openmeteo_cache` ma bledne etykiety czasu latem).

### 3.8 `z14lite_validate.py` - Z14-lite kroki 2-3 (potok sieciowy) - **zrodlo `predict_block`**
- Publiczne: `design_cols()`; `add_calendar(df)`; `network_frame(om, index)`; `fit_station_models(features, out_dir, station)`; `bells3_from_parts(ir, t1d, times, coef, depth_mm)`;
  `bells3_bt_from_parts(ir, air, t1d, times)`; `check_bells_replicas(features)`; `load_cell_meteo(cache_dir, q_lat, q_lon, lo, hi) -> (om, (grid_lat, grid_lon))`;
  `predict_block(om, times, ir, air, depth_requests, fitted, station_geom, two_layer=None) -> DataFrame`; `code_path_test(features, out_dir, fitted, n_sample=500, seed=42)`;
  `thickness_check(obs, fitted, cache, n=100, seed=7)`; `main`. Stale modulu: `SRC_CSV`, `CLASS_STATION`, `MAIN_CLASS="otwarta (TN)"`, `DEPTH_COLS=[t_4cm,t_8cm,t_12cm]`, `HIST_DAYS=35`, `SIM_LEAD_DAYS=3`, `GRID_DEG=0.05`.
- `predict_block`: dla chwil `times` (jedna komorka, jedna doba): `frame` od (dzien-35 d); t50 z OLS; symulacja EB od (dzien-3 d) z modelowanym dolem; interpolacja liniowa Ts i T(z) do chwili t;
  cechy (OP_INSTANT, MA, t50_hat, anchor_eb = IR - Ts, ir_minus_t50hat) -> hybryda B (XGBoost na rezyduum phys) dla t_4/8/12 cm; **interpolacja po glebokosci tylko miedzy 4/8/12 cm (np.interp, poza zakresem = stala, czyli 2 cm albo 15 cm bylyby BLEDNE)**;
  BELLS3/BELLS3_O/BELLS3_BT z T(1-day) z reanalizy. Zwraca kolumny `phys_{mm}mm`, `hybrid_{mm}mm`, `xgb_op_{mm}mm`, `bells3_{mm}mm`, `ts_sim`, `t50_hat`, `anchor_eb`, `t1d`... lub `None` gdy brak OM/symulacji.
- Wejscia: OM godzinowe; `times` lokalne (naiwne); `ir`, `air` [C]. Wyjscie: [C]. Zaleznosci: xgboost (hybryda), `baselines_e3`, `depth_thickness_study`, `energy_balance_bc`, `hybrid_e3`, `operational_bc`, `validation_protocol`, `load_station_data`.
- `fit_station_models`: uczy t50 OLS + hybryde + xgb_op na PELNYM roku stanowiska (bez foldow); alpha z E2-T01, EB z E2-T05; `code_path_test` (500 losowych chwil Podkowy; siec vs E3 = 0.0015 C, prog 0.15) i `thickness_check` (grubosc 150/250/300 mm: 0.0000 C - grubosc nie wchodzi do obliczen w konfiguracji z alpha globalna).
- Pulapki: `network_frame` interpoluje OM i wypelnia ogon stala ("interpolate" bez limit_direction) - patrz P4; `load_cell_meteo` wybiera pliki cache po nazwie wzorcem `om_{lat}_{lon}_*.parquet` (dokladne 2 miejsca po przecinku, `+`->`p`, `-`->`m`) i po metadanych `start/end`.

### 3.9 `z14lite_report.py` - metryki, propagacja, diagnostyka (badawczy; funkcje pomocnicze potrzebne)
- Publiczne: `build_table(z14_dir)`; `metrics(err)`; `r2(pred, obs)`; `bootstrap_sessions(df, models, main, reps, seed=42)`; `common_support(df, models)`;
  `deflection_error(err_temp, t_meas) -> (lin, expo)`; `figures(...)`; `main`. Stale: K_LIN=0.02, BETA_EXP=0.016, BAND_FWD=1.37 %, BAND_TOL=3.0 %, BT_DOMAIN.
- `bootstrap_sessions`: resampling SESJI (`session_id`) z powtorzeniami, 2000 powt., percentyle 2.5/97.5, roznice sparowane. `deflection_error`: lin = 100*0.02*err/(1+0.02*(20-T)); expo = 100*(exp(0.016*err)-1).
- Zbior H (w main): `dataset=="odcinki" & trusted==1 & status in {entry_first, entry_change} & month 4..10`. Wynik Z14-lite (przed korekta czasu OM): hybryda B TN 2.734, BELLS3 2.543, n=550 (E3-T30/F20-F22; **przestarzale** - liczone na cache z bledem czasu).
- Dla N2 przydatne: `metrics`, `bootstrap_sessions`, `deflection_error` (propagacja do bledu znormalizowanego ugiecia).

### 3.10 `z14b_single_shot.py` / `z14c_candidates.py` / `z14c_omfix.py` (poza lista, ale WAZNE - to wlasciwa sciezka)
- `z14b_single_shot`: `at(series, times)`; `build_frame(om, t_min, t_max)`; `class_fit(features, out_dir, cls)` (modele klasy + `beta_ir`, `a_default`); `ts_at_a(frame, t50, fit, a, t_start, t_end, t_bar)`;
  `calibrate(frame, t50, fit, t_start, t_end, t_bar, target) -> (a, flag, ts_lo, ts_hi, ts_cal)`; `summarize`; `process_unit(om, fits, unit, depth_m, variants)`; `run_tasks`; `h_tasks(grid_deg)`; `micro_tasks(grid_deg)`;
  `test_replication`; `test_station_path`; `main` (`--test-only`, `--nproc`). Stale: A_LO/A_HI z `eb.PARAM_SPEC['a_sw']` (0.03/1.0), GATE_C=1.0, XTOL=1e-3, LEAD=3 d.
- `z14c_candidates`: `ts_series`, `session_calibrate` (K1, odrzucone), `pred_at(om, t, ir, air, fit, a)`, `process_unit(om, fits, unit)` (4 tryby: single/session x masa/raw), `build_tasks()`, `main`. EXCLUDED_STATIONS={16322}.
- `z14c_omfix`: `labels_to_local(om, offset_h=1)`, `load_cell_meteo_fixed`, `apply()` (podmienia `zv.load_cell_meteo`; dla starego cache); nowy cache `*_utc` nie wymaga poprawki.

### 3.11 `z14d_report.py`, `z14d_units.py`, `z14d_c_v2.py`, `z14d_b_compare.py` - raporty Z14d (badawcze)
- `z14d_report`: `rmse(e)`, `load_D(z14c)`, `decomp(df, names)` (wariancja miedzy/wewnatrz sesji, wg pory dnia i roku), `deflection_table(df, names)`, `main(--out, --reps)`. Liczy E3-T46..T51 (H v2, rozbicie, propagacja, wrazliwosc, 1 km, mikroodcinki)
  i zatrzymuje sie (STOP), jesli nie odtworzy 1.749/2.118/2.406 (tol. 0.0015). Plik wejsciowy: `Z14c_candidates.parquet`.
- `z14d_units`: `_init`, `_run_spot`, `km_tasks()`, `_km_unit`, `_run_km`, `main(--mode spot|km|micro, --nproc, --cache, --suffix)`. Przelicza modele na NOWYM cache UTC; kontrola `spot`: 83 jednostki, max |roznica| fizyki 1.2e-13 C wobec Z14c-z-poprawka.
- `z14d_c_v2`: `sensor_at(feats, st, col, times)`, `build(pred, cls, depth_k, target)`, `boot(df, day, reps)`, `main`. C v2 = zbior potwierdzajacy po korekcie celu (Podkowa: sonda 12 cm != 12 cm, cel = czujnik).
- `z14d_b_compare`: `cmp(old, new, keys, cols, label)`, `main`. Porownanie lancucha E2/E3 po poprawce czasu OM (`_omfix_check`), prog 0.02 C -> **liczby publikacji_1 nie stoja** (6/28 liczb > 0.02, max +0.066). Badawcze.

### 3.12 `z15_pairs_fetch_openmeteo.py`, `z15_temperatures.py` - Z15 (zastosowanie produkcyjne na sieci - najblizszy prototyp N2)
- `z15_pairs_fetch_openmeteo`: `load_side(df, lat_col, lon_col, time_col, side)`, `plan_queries(d)`, `main(--plan, --cache-name)`. Dla 5511 par TSD-FWD (2024-2026): 137 zapytan, 34 komorki, 0 brakow.
- `z15_temperatures`: `predict_side(om, fit, t, ir, air, depth_m=0.12) -> dict(t12_uncal, t12_cal, t12_bells3, a_cal, flag, flag_pl, ir_masa)`; `stop_check(out_dir, n=100, seed=7, cache_name)`;
  `load_pairs`, `build_jobs(df, grid_deg)`, `build_tasks(jobs, chunk=30)`, `run_all(df, out_dir, nproc, cache_name)`, `to_wide`, `robust_errors`, `diagnostics`, `main(--test-only, --nproc, --n-stop)`.
  Wejscie `tabele\z15_pary_wejscia.csv`: `fwd_time/lat/lon/ir/air`, `tsd_time/lat/lon/ir/air`. Wyjscie `output\z15\Z15_temperatury_par.csv` (kolumny `{fwd,tsd}_t12_cal`, `_t12_uncal`, `_t12_bells3`, `_a_cal`, `_calib_flag`, `_calib_flag_detail`).
- **`predict_side` jest dokladnie interfejsem N2** (jedna chwila -> T12 + a_cal + flaga). Flagi polskie: ok / granica (bound_*) / bramka (gate, "noc") / brak_symulacji. Kontrola STOP: 0.00e+00 C wzgledem `z14c_candidates.process_unit`.
- Wyniki: 5511/5511 par ma T12; flagi FWD ok 36.9% / bramka 19.9% / granica 43.2%; TSD ok 54.5% / granica 45.5% / bramka 0% (tylko dzien); FWD vs wpis operatora (entry, wiek 0, n=33): RMSE 1.35.
  Pary TSD-FWD NIE sa rownoczesne (mediana odstepu 75 dni) - roznica T12_TSD-T12_FWD (+8.86 C) to sezon/godzina, nie blad.
- Zastrzezenie [K]: pirometr TSD (`temp_road`) nie walidowany na sieci; korekta IR->masa i kalibracja zastosowane identycznie jak do FWD.

### 3.13 `validation_protocol.py` (E3 pkt 1) - badawczy
- Publiczne: `build_folds()`, `load_features(out_dir=None)`, `get_fold_data(fold, features, config)`, `evaluate_predictions(test_df, y_pred, config)`, `set_common_support(support)`,
  `attach_common_support(out_dir, features=None)`, `evaluate_model(predict_fn, config, profile, features=None, folds=FOLDS)`, `export_folds(out_dir, features=None)`, `sanity_check(features=None)`;
  `Fold(split, fold, train_station, test_station, test_ranges, gap_days)`, `EvalConfig(snow, target="target_t_mid")` (snow wymagany: "exclude"|"include").
- Co: zamrozony protokol v3: 24 foldy monthly + 8 seasonal + 2 transfer (32+), gap 2 doby, pory doby 0-6/6-12/12-18/18-24, okno diagnostyczne IV-X (`DIAG_MONTHS=(4,10)`), DATA_START=2025-08-20, DATA_END=2026-08-19.
- Dla N2: tylko stala "sezon diagnostyczny IV-X" (jedyne miejsce, gdzie IV-X jest zdefiniowane w kodzie poza filtrem H). Nie importowac.

### 3.14 Pozostale pliki wskazane w zakresie
- `requirements.txt` (przypiete 2026-09-22): numpy 2.5.1, pandas 3.0.3, scipy 1.18.0, pyarrow 25.0.0, matplotlib 3.11.0, openpyxl 3.1.5, requests 2.34.2, scikit-fem 12.0.2, xgboost 3.3.0, scikit-learn 1.9.0, arch 8.0.0, statsmodels 0.15.0.
  Python 3.12.16 (`C:\ENV\doktorat`). **Rdzen N2 wymaga tylko: numpy, pandas, scipy, pyarrow, requests.** (pandas 3.x: patrz P7).
- `CLAUDE.md` (571 linii): kontekst, plan E2/E3, Z14-lite/Z14b/Z14c/Z14d/Z15/Z16, erratum czasu OM, migracja PC. Kluczowa regula repo: zrodla nie sa nadpisywane; wyniki z ID `E3-Txx`.
- Rodzina `z15b_*` (miary odporne Tab. 4.1-4.3), `z16_*` (lato/noc, bootstrap stacjonarny, DM) - badawcze, jedynie czytaja zapisane predykcje; pominac.

---------------------------------------------------------------------------------------------------

## 4. Pliki w output\ (zakres)

| Plik / katalog | Zawartosc | Uwaga |
|---|---|---|
| `output\z14lite\E3-T30..T34`, F20..F22, `Z14lite_*` | Z14-lite: hybryda B TN 2.734 [2.412; 3.096] bias +1.74, BELLS3 2.543, n=550/226 sesji, werdykt "WYNIK CZESCIOWY" | **przestarzale** (cache z bledem czasu OM latem, erratum 2026-11-04); stare wersje z BELLS3_O/BT: `_v1_z_BELLS3_O_BT\` |
| `output\z14lite\z14b\` (E3-T35..T38, F23..F25) | Z14b: kalibracja jednorazowa, mikroodcinki, zegar | liczby IV-X dotkniete bledem czasu; mikroodcinki: kalibracja bez efektu (noc) |
| `output\z14lite\z14c\` (E3-T39..T45, F26..F28, `Z14c_candidates.parquet`) | Z14c: D (549) i C; zbior C (n=647): finalny 2.728, hybryda 1.798, BELLS3 2.823; `Z14c_candidates.parquet` = zrodlo referencji | dane D po korekcie czasu przez `z14c_omfix` |
| `output\z14lite\z14d\E3-T46_z14d_H_v2.csv` | **referencja RMSE 1.749 / MAE 1.404 / bias +0.265, n=549/226** | patrz sekcja 1.2 |
| `...\z14d\E3-T47` | rozbicie wg godziny, lat, wariancja miedzy sesjami | |
| `...\z14d\E3-T48/T49/T50..T52` | propagacja na ugiecie; wrazliwosc (H+entry_possible n=790: 1.779 [1.644; 1.913]); 1 km (n=9: fizyka+kal 2.25, BELLS3 1.46); mikroodcinki (n=120: 2.61 vs BELLS3 2.01) | |
| `...\z14d\E3-T53..T56`, F29..F31 | C v2; T56 = roznice E3-T06 po poprawce czasu | |
| `...\z14d\Z15b_T41/T42/T43_robust.csv` | miary odporne: T41 = hybryda A/B na stanowiskach; **T42 = H v2 z mediana i P90 + CI**; T43 = C v2 (4 podzbiory) | T42/T43 numeracja - sekcja 1.3 |
| `output\z14lite\openmeteo_cache_utc\` | 938 plikow = 469 okien (parquet + json), 21 MB; UTC->lokalny po stronie klienta | **cache do uzycia** (offline) |
| `output\z14lite\openmeteo_cache\` | 347 okien, 15 MB | etykiety latem o -1 h; tylko przez `z14c_omfix` |
| `output\z15\` | `Z15_temperatury_par.csv` (5511 par), diagnostyka, raport_Z15.md | E3-T57 |
| `output\E2-T01, E2-T03, E2-T05, E2-T07/T08` | alpha, wspolczynniki korekty IR (godzinowe), parametry EB, tabele cech stacji | zrodla stalych |

---------------------------------------------------------------------------------------------------

## 5. Open-Meteo - jak dziala pobieranie (jedyne dopuszczalne polaczenie sieciowe)

- **Endpoint**: `https://archive-api.open-meteo.com/v1/archive` (HTTP GET, `requests.get(..., timeout=120)`; `fetch_openmeteo.API_URL`). Bez klucza API.
- **Parametry**: `latitude`, `longitude` (zaokraglone do 0.05 st. w sieci; IBDiM 52.2676/21.0246 dla stanowisk), `start_date` = poczatek-1 dzien, `end_date` = koniec+1 dzien (bufor na konwersje UTC->lokalny),
  `hourly` = 15 zmiennych, **`timezone=UTC`** (OBOWIAZKOWO - patrz erratum), `wind_speed_unit=ms`. Produkt: domyslny `best_match` (ERA5 / ERA5-Land / IFS HRES wg dokumentacji Open-Meteo; skrypt go nie przypina).
- **Zmienne `hourly`** (HOURLY_VARS): `temperature_2m` [C], `relative_humidity_2m` [%], `dew_point_2m` [C], `surface_pressure` [hPa], `cloud_cover` [%], `wind_speed_10m` [m/s],
  `shortwave_radiation`, `direct_radiation`, `diffuse_radiation` [W/m2], `precipitation` [mm], `snowfall` [cm], `snow_depth` [m], `soil_temperature_7_to_28cm`, `_28_to_100cm`, `_100_to_255cm` [C].
  **Uzywane przez sciezke N2**: `temperature_2m`, `dew_point_2m`, `wind_speed_10m`, `cloud_cover`, `shortwave_radiation` + `snow_depth` (wymagane technicznie przez `meteo_to_10min`, w fizyce nieuzywane).
  Pozostale 9 (RH, cisnienie, direct/diffuse, opad, snieg, 3 poziomy gruntowe) to balast badawczy (Z6) - w N2 wywalic z zapytania.
- **Rozdzielczosc**: czasowa godzinowa; przestrzenna - najblizsza komorka siatki reanalizy (zwracane `grid_lat/grid_lon` zapisywane w meta; np. zapytanie 49.85/20.25 -> siatka 49.8770/20.1913,
  IBDiM 52.2676/21.0246 -> 52.26713/20.961182; zapytanie rozni sie od komorki o rzedu 0.03-0.06 st.) [W: natywnie ~0.1 st. (ERA5-Land)/0.25 st. (ERA5), nieweryfikowane w kodzie].
  Zaokraglenie do 0.05 st. = do 3.2 km (max), mediana 1.8 km [K, raport]. Wysokosc komorki `elevation_m` zapisywana, ale model z niej nie korzysta.
- **Okna czasowe**: dla kazdej obserwacji [dzien-35 d, dzien] (35 d = MA30 z min_periods 25 d + rozbieg 3 d); okna tej samej komorki scalane, gdy przerwa < 10 dni; 1 zapytanie = jedno okno (~864 godz. = 36 dni).
  Po konwersji zakres przyciety do dat lokalnych `[start 00:00, end 23:59]`, wiec ostatni wiersz = godz. 23:00 dnia `end` (P4).
- **Konwersja czasu**: `om_utc_to_local`: indeks UTC -> `tz_convert("Europe/Warsaw")` -> naiwny; duplikat jesienny: zostaje PIERWSZE wystapienie; brak godziny wiosennej: brak wiersza (interpolacja po czasie przy skladaniu cech).
  Czas pomiaru FWD to `local_Europe_Warsaw_DST_no_shift` (lokalny z DST, naiwny) -> laczone bez dodatkowych przesuniec. Etykiety radiacji = srednia z godziny POPRZEDZAJACEJ -> w `meteo_to_10min` indeks przesuniety o -30 min, potem interpolacja liniowa i clip >= 0.
- **Cache**: `output\z14lite\openmeteo_cache_utc\om_{lat}_{lon}_{start}_{end}.parquet` + `.json` (meta: query_lat/lon, grid_lat/lon, elevation_m, start/end, fetched_at, units, n_rows, n_missing, time_basis);
  nazwa: `f"om_{lat:+.2f}_{lon:+.2f}_{start}_{end}"` z `+`->`p`, `-`->`m`, daty z `-`->`m` (np. `om_p49.85_p20.25_2021m08m05_2021m09m09`). Wznawialny (istnienie obu plikow = pomijanie); brak TTL/wersjonowania/walidacji
  swiezosci [W: archiwum reanalizy bywa korygowane - tego cache nie wykryje]. Odczyt: `zv.load_cell_meteo(cache_dir, q_lat, q_lon, lo, hi)` skleja pliki, ktorych [start,end] zachodzi na [lo,hi], usuwa duplikaty indeksu i przycina do [lo-1 d, hi+1 d].
- **Limity/zachowanie**: tempo <= 1 zapytanie / 2 s (`SLEEP_S`), HTTP 429 -> 60 s i do 5 prob, zerwane polaczenie -> 5*n s, "limit dzienny" -> zapis stanu i koniec bez uzupelniania; zadnych imputacji.
  Pobranie H: 332 zapytania (320 pobranych, 0 bledow). Pobranie Z15: 137 zapytan. [W: archiwum ma opoznienie rzedu kilku dni wzgledem "dzis" - w N2 pomiar sprzed <~5 dni nie bedzie mial pelnych danych; tego repo nie obsluguje (brak API prognoz)].
- **ERRATUM CZASU (2026-11-04)**: `timezone=Europe/Warsaw` oznacza WSZYSTKIE godziny stalym przesunieciem z dnia POBRANIA (cache z 2026-10-31: UTC+1 caly rok -> latem etykiety o 1 h za wczesne);
  stary plik E2/E3 (2026-09-20) UTC+2 caly rok -> zima o 1 h za pozne. Stad `timezone=UTC` + konwersja po stronie klienta. Wplyw: Z14 H: 1.934 -> 1.749 (fizyka z kalibracja), hybryda 2.596 -> 2.118.

---------------------------------------------------------------------------------------------------

## 6. Dane archiwalne potrzebne do powtorzenia testu i ich lokalizacja

1. **Pomiary FWD (pirometr + temperatura w otworze 12 cm)**:
   `C:\projects\sql_tsd_fwd\tabele\z14lite_fwd_walidacja_v3.csv` (1394 wiersze, 39 kolumn; `paths.TABELE`; 851 `odcinki` + 543 `odcinki_1km`; kodowanie utf-8-sig).
   Kolumny uzywane: `dataset, session_id, station_id, year, measured_at_local` (lokalny, DST, naiwny; `time_basis=local_Europe_Warsaw_DST_no_shift`), `latitude, longitude, gps_source, gps_status`,
   **`t_surface`** (IR aparatu [C]), **`t_air`** [C], **`t_layer`** (temperatura w otworze, [C]; cel), `t_layer_depth_cm` (12 dla 1054 wierszy, 10 dla 258), `t_layer_source` (operator_entry / measured_series),
   `asphalt_status` (entry_first 248 / entry_change 331 / entry_possible 272), `asphalt_temp_trusted`, `t_layer_age_min`, `obs_group_id`, `road_id`, `force_kn`, `d1..d9` (ugiecia; dla propagacji).
   Zbior H = `dataset=="odcinki" & t_surface,t_air notna & t_layer_depth_cm==12 & asphalt_temp_trusted==1 & status in {entry_first,entry_change} & month IV-X & station_id!=16322` -> **549 obs., 226 sesji** [P].
   Pochodzenie (SQL): eksport P058b/P059/P060 w `C:\projects\sql_tsd_fwd\prompty\` (bazy: `bazy\baza_odcinki_v4.db`, surowe: `raw\`, `baza_TSD_FWD_odcinki\FWD`) - nie otwieralem (zbiory 18-740 GB); dla testu wystarczy CSV.
2. **Odczyty IR stacji (sesyjne)**: `...\tabele\z14lite_v3_ir_stacje.csv` (47 370 wierszy) - tylko dla trybu `session`/K1 (odrzuconego); do single-shot NIEPOTRZEBNE.
3. **Open-Meteo cache** (offline, 21 MB): `C:\WORK\DOKTORAT\temp_model\output\z14lite\openmeteo_cache_utc\` (okna H = 332 zapytania). Zrodlowo wymaga sieci (sekcja 5).
4. **Dane do (re)fitu stalych** (NIE potrzebne w runtime, tylko do audytu stalych): `C:\WORK\DOKTORAT\stacje pogodowe\raport_stacja1.csv` (TN), `raport_stacja2.csv` (Podkowa);
   `output\E2-T07_features_TN.parquet` / `E2-T08_...`; `output\E2-T01_calibration_summary_top-t_2cm.csv`; `output\E2-T05_eb_surface_bc_params.csv`; `output\openmeteo_ibdim_hourly.parquet` (punkt IBDiM, 2025-07-01..2026-08-19).
5. **Dla Z15 (regresja drugiego rzedu)**: `...\tabele\z15_pary_wejscia.csv` (5511 par; 2.4 MB) + `output\z15\Z15_temperatury_par.csv` (wynik referencyjny).
6. Pirometr TSD/FWD != pirometr stacji (Qulon-RTS) - zastrzezenie autora [K]; sonda w otworze = pomiar kontrolny operatora, jego blad (Podkowa 12 cm: +4.1 C, TN 12 cm: RMSE 1.12 C wzgledem czujnika wbudowanego) wyznacza dolna granice bledu.

---------------------------------------------------------------------------------------------------

## 7. Pulapki (wazne dla N2)

- **P1 Sezon IV-X**: w kodzie sezon jest wymuszony TYLKO filtrem zbioru (miesiace 4..10) i regula raportowania `DIAG_MONTHS=(4,10)`; sam potok (`predict_block`/`predict_side`) nie sprawdza miesiaca ani sniegu
  (`snow_depth` jest interpolowane, lecz nieuzywane w fizyce - brak modelu pokrywy snieznej/mrozu). Parametry (alpha, EB, beta50, beta_ir) pochodza z calego roku stanowiska, w tym zimy. N2 musi samo dodac guard/flage "poza sezonem" (XI-III) i "snieg" (snow_depth > 0.005 m).
- **P2 Noc / kalibracja nie dziala**: bramka `|Ts(a=1)-Ts(a=0.03)| < 1.0 C` -> a_sw = domyslne 1.0 (flaga `gate`; w H tylko 11 obs.), ale dodatkowo 244/549 (44%) = `bound_hi` (cel IR_masa wymaga a>1; kalibracja bez efektu).
  Poza H: FWD na sieci -> bramka 19.9% (noc), TSD 0%. Wg pory (H): 0-6 h RMSE 2.17 (n=49), 18-24 h 2.17 (bias +1.48) vs 6-12 h 1.38. Proponowana flaga N2: `night` = (SW_ma6 < 5 W/m2) lub flaga `gate`; kalibracja nocna "nieidentyfikowalna" [K Z14b].
- **P3 Wspolrzedne**: zaokraglenie do siatki 0.05 st. (do 3.2 km); komorka reanalizy ~0.1 st. -> pomiar w poblizu granicy komorek moze trafic do innego pliku; brak korekcji wysokosci/zacienienia.
  Klasa terenu domyslnie "otwarta (TN)" - na terenie zacienionym (Podkowa) model TN ma bias +3..+5 C (Z14c: 12 cm Podkowa 3.65, bias +2.96), co przesuwa ryzyko na zacienienie (nieobslugiwane).
- **P4 Koniec okna cache**: cache `_utc` konczy sie na godz. 23:00 dnia `end` (przyciecie do dat lokalnych). Pomiar po 23:00 dostaje ogon meteo wypelniony stala (pandas `interpolate` bez limit_direction).
  Referencyjne Z14c (stary cache + `omfix`) mialo tam jeszcze godz. 00:00 nastepnej doby -> 5 z 549 obs. (pomiar 23:14-23:45: `odcinki_8_77`, `odcinki_9_88`, `odcinki_114_17452`, `odcinki_128_19961`, `odcinki_230_41754`)
  roznia sie 1e-5 .. 0.18 C; agregat: RMSE 1.7486 (ref) vs 1.7488 (nowy cache). Pobierac `end_date` = dzien+1 (wszystkie wiersze doby).
- **P5 Jednostki**: wiatr m/s (`wind_speed_unit=ms`), SW W/m2 (srednia z godziny poprzedzajacej), chmury %, temperatury C (w EB przeliczane na K), `snow_depth` m, h0/h1 w W/m2K i W s/m3K, c_vol J/m3K, alpha m2/s.
- **P6 Czas**: UTC vs lokalny - wszystko w naiwnym czasie lokalnym Europe/Warsaw z DST; godzina podwojna jesienia: pierwsze wystapienie OM, pomiar FWD z tej godziny jest niejednoznaczny (nieobslugiwany); wiosenna luka: interpolacja.
  Zegar aparatu FWD "niepotwierdzony" (Z14b: min. wariancji przy -90 min), po erracie ~60 min z tego to blad etykiet OM; reszta bezwladnosc czujnikow - czasu nie przesuwano.
- **P7 Pandas 3.0 / jednostki czasu**: kod uzywa `astype("int64")` na DatetimeIndex w `np.interp` (zalezne od rozdzielczosci ns/us; w repo komentarz o round-tripie przez parquet w `contiguous_runs`).
  W repliece wymusilem `as_unit("ns")` + `.asi8`. W pakiecie uzywac jawnie tej samej jednostki.
- **P8 Interpolacja po glebokosci**: `predict_block` interpoluje tylko 4/8/12 cm i obcina stala poza zakresem; N2 ("temperatura na zadanej glebokosci") musi odczytywac wezel/siatke 1 cm z `T[:, k]` (solver ma siatke 0-50 cm, `simulate_eb` zwraca jedynie glebokosci czujnikow - trzeba rozszerzyc zwracanie pelnej siatki).
- **P9 Stan globalny**: `ca.configure(...)` mutuje globale (SUB_COLS, NZ, TOP_COL) przy kazdym wywolaniu symulacji; `z14c_omfix.apply()` podmienia `zv.load_cell_meteo`; `thickness_check` tymczasowo modyfikuje `STATION_META`. Nie powielac.
- **P10 Cache**: patrz sekcja 5 (brak TTL, brak wersjonowania produktu OM, nazwa zalezna od zaokraglenia wspolrzednych, plik JSON konieczny obok parquet). Stary katalog `openmeteo_cache` ma bledne etykiety czasu.
- **P11 Dolny BC**: beta50 dopasowana do jednego roku jednej stacji (Warszawa); dla innych lat/regionow ekstrapolacja (Z6: grunt z reanalizy nie poprawia przenosnosci). Wplyw dolu na T w 12 cm: wspolczynnik transmisji ~0.40 [Z12].
- **P12 Granice a_sw**: gorna granica 1.0 = wartosc domyslna klasy TN; kalibracja moze tylko zmniejszac absorpcje. Podkowa: a_sw=0.166 i svf=0.316 (nieseparowalne).
- **P13 Moc statystyczna**: 77% wariancji bledu miedzy sesjami; N=2 stanowiska; H jest eksploracyjny wzgledem Z14b; wynik na C (niezalezny) gorszy (2.73 / v2 3.08).
- **P14 `main()` zapisuja do output\**: uruchomienie czegokolwiek z src\ bez `--out` nadpisze referencje (np. `energy_balance_bc.main` -> E2-T05, `operational_bc.main` -> E3-T03/T04). N2 nie powinno ich wolac.

---------------------------------------------------------------------------------------------------

## Wnioski dla projektu

### A. Podzial na moduly pakietu `tsdfwd_tools` (propozycja dla N2 `layer_temp`)
```
tsdfwd_tools/layer_temp/
  constants.py     # stale fizyczne i solvera (DZ=0.01, NZ=51, DT=600, SPINUP=288 (48 h), LEAD=3 d, HIST=35 d, GRID=0.05, GATE=1.0, EPS=0.95, A_LO/A_HI, XTOL) + wersja protokolu
  params.py        # wczytanie zamrozonych parametrow klasy TN z params_TN.json (alpha, EB, beta50, beta_ir, hash zrodla); (opcjonalnie klasa shaded jako TODO, nie domyslnie)
  meteo.py         # OpenMeteoClient (archive-api, timezone=UTC, 6 zmiennych, retry/429/sleep), cache wg schematu z repo, om_utc_to_local, load_cell_meteo (end_date = dzien+1)
  frame.py         # meteo_to_10min (swr -30 min, clip), longwave_down (Brunt+Crawford-Duchon), cechy kalendarza i MA7/MA30, jawna jednostka czasu ns
  solver.py        # simulate_eb: zwraca PELNA siatke T[nt,51] (z=0..50 cm), ta sama numeryka co energy_balance_bc.simulate_eb (linearyzacja LW, polowa komorki, dol Dirichlet)
  calibrate.py     # corr IR->masa (beta_ir), t50 (beta50), calibrate_single_shot (brentq po a_sw, bramka, flagi ok/bound_lo/bound_hi/gate/nosim)
  predict.py       # layer_temperature(ts, lat, lon, ir, air, depth_m=0.12, meteo=None) -> {value, u95, flag_time, flag_calib, a_sw, ts_sim, qc[]}; wersja wsadowa dla survey (grupowanie komorka x doba jak z15 build_tasks)
  bells3.py        # opcjonalny komparator: BELLS3 (sin18, T(1-day) = (min+max)/2 z OM dnia poprzedniego; wspolczynniki b0..b5)
  uncertainty.py   # tabela niepewnosci z H v2 wg pory/flagi (patrz C) + bootstrap sesyjny (opcjonalnie)
  qc.py            # guardy: sezon IV-X, snieg, NaN OM, noc, wsp. poza Polska/gridem, depth poza [0,50] cm, IR/T_air poza dziedzina
  cli.py           # wejscie CSV survey -> wyjscie CSV (+ meta JSON: wersja, hash params, grid_lat/lon, flagi)
tests/ regression/ (patrz D)
```
Zasada: zero importow z `DOKTORAT\temp_model\src`; parametry jako plik JSON z hashem zrodla (E2-T01/T05/T07).

### B. Co jest badawcze i trzeba pominac w N2
- Hybryda B / A / C, XGBoost (`xgb_op`, `xgb_op_lag`), `hybrid_e3`, `hybrid_swap_test`, `coldstart_test`, `importance_stability`, `residual_transfer_diag` - nie wchodza do wartosci referencyjnej (wystarczy fizyka; hybryda B pogarsza H: 2.12 vs 1.75).
- BELLS3_O i BELLS3_BT (zakaz projektu); `bells3_bt_diag`; `calibrate_alpha`, `fem_verification`, `fourier_1d` (Dirichlet), `ir_mass_relation` (E2-T03), `export_features`, `load_station_data` (parser stacji) - potrzebne tylko do wygenerowania zamrozonych stalych.
- Protokol walidacji E3 (`validation_protocol`, `eb_fold_calib`, `baselines_e3`, `bootstrap_ci`, `synthesis_e3`), `surface_calib` (Z9b), `soil_bc`, `depth_thickness_study`, `transferability_test`, `env_sensitivity`, `deep_level_shading`, `depth_correlations`, `eb_convergence_check`, `k1_impact`, `sample_vs_full`, `v2_v3_report`, `fig_presentation`.
- Z14*/Z15b/Z16 skrypty raportowe i K1-K5 (`z14c_k4`, `z14c_report`, `z14c_confirm*`, tryb `session`), kalibracja sesyjna (K1) i surowy IR (K2) - odrzucone w Z14c.
- Mikroodcinki, 1 km, zbiory C - jako testy rozszerzone, nie jako zaleznosc.
- Z kodu produkcyjnego tylko: EB solver, siatka/CZAS, OLS t50 i korekta IR (jako zamrozone wspolczynniki), kalibracja brentq, klient OM, BELLS3 (opcja).

### C. Niepewnosc i flagi dla N2 (propozycja na bazie H v2; [P] = policzone)
- Globalnie: RMSE 1.75 [1.62; 1.87] (bootstrap po sesjach), MAE 1.40, bias +0.27, P90 |e| 2.82 [2.59; 2.99]. Proponowany u95 = +-2*RMSE_pora ~ +-2.8..4.3 C (heurystyka; do uzgodnienia z autorem), co najmniej dolna granica metody pomiaru (~1.1 C, E3-T45).
- Pory (H, wg godziny lokalnej aparatu): 0-6 h 2.17; 6-12 h 1.38; 12-18 h 1.89; 18-24 h 2.17 -> flaga `night` (0-6, 18-24 lub SW < 5 W/m2) = "kalibracja nie dziala"; w tych porach podac wiekszy u95.
- Flagi kalibracji: ok (RMSE 1.69), bound_hi (1.81; kalibracja nasyca sie na a_sw=1), bound_lo, gate (1.80, bias +1.75), nosim. Dodatkowe: `out_of_season` (XI-III), `snow`, `meteo_gap`, `tail_extrapolated` (P4), `shaded_site_suspected` (brak danych o zacienieniu - ryzyko biasu +3..+5 C).
- Raportowac `a_sw`, `ts_sim` (Ts modelu vs IR_masa) i residuum kalibracji `ts_cal_bar - target` jako diagnostyke.

### D. Plan testu regresji na wartosciach referencyjnych
Dane testowe: `z14lite_fwd_walidacja_v3.csv` + kopia 332 okien `openmeteo_cache_utc` dla H (offline; ok. kilkanascie MB) jako fixture; zamrozone `params_TN.json` z sekcji 2. Test nie moze miec sieci (mock klienta OM).
1. **T1 (glowny)**: H v2 (549 obs., 226 sesji): `RMSE = 1.7486 +- 0.001`, `MAE = 1.4039 +- 0.001`, `bias = +0.2653 +- 0.001`. (Replika na nowym cache: 1.7488 / 1.4042 / +0.2649 - miesci sie; tolerancja 0.001 swiadomie szersza niz 1e-4 z powodu P4.)
2. **T2 (liczebnosci i flagi)**: n=549, sesji=226, flagi `ok=294, bound_hi=244, gate=11, bound_lo=0`; bez `nosim`.
3. **T3 (po obserwacji)**: |N2 - `phys_single_masa` z `Z14c_candidates.parquet`| < 1e-6 C dla 544/549; 5 wskazanych `obs_group_id` (P4) - tolerancja 0.2 C albo pobrac `end_date`+1; ten sam test dla `phys_uncal` (bez kalibracji) i `a_single_masa` (< 5e-2 w 5 wyjatkach, reszta < 1e-9).
4. **T4 (komparator)**: fizyka bez kalibracji 2.0872 / 1.6974 / +0.9455; BELLS3 2.4065 / 1.8160 / -0.3432 (`BELLS3_COEF`, T(1-day) z OM, `sin18`).
5. **T5 (rozklad)**: RMSE wg pory: 2.167 (n49) / 1.378 (n226) / 1.889 (n237) / 2.167 (n37); (opcja) bootstrap sesyjny seed 42, 2000 powt.: CI RMSE [1.619; 1.869] +-0.01 (`bootstrap_sessions`).
6. **T6 (Z15, 2. poziom)**: losowe 200 par z `Z15_temperatury_par.csv`: `{fwd,tsd}_t12_cal` i `_t12_uncal` zgodne < 1e-6 (replika: 1e-12 na 240 wierszach); flagi identyczne; agregat flag FWD 2033/2380/1098, TSD 3004/2507/0.
7. **T7 (kontrola solvera)**: porownanie z `z14b/Z14b_predictions_meta.json`/Z14d_spot (83 jednostki, 1e-13) lub z moim `e0_standalone.py`; test jednostkowy: stan stacjonarny (stale forcing -> profil), bilans energii, kalibracja do znanego a_sw (round-trip: Ts(a*)=target -> a ~ a*).
8. **T8 (czas/DST/UTC)**: test `om_utc_to_local` (godzina podwojna, luka wiosenna), pomiar o 23:30 w ostatniej dobie okna; guardy P1/P2/P8 (glebokosc 5/10/20 cm -> bez obcinania).
9. **T9 (tryb sieciowy)**: mock `requests.get` z zapisanym JSON (parametry `timezone=UTC`, `wind_speed_unit=ms`, 6 zmiennych); test retry 429; test, ze N2 nie robi zadnych innych polaczen.
10. **T10 (dryf)**: hash `params_TN.json` + `Z14c_candidates.parquet` w tescie; zmiana stalych -> test czerwony.
Uwaga: nie podawac 1.75 jako dokladnosci produktu - test odtwarza H (eksploracyjny); niezalezny zbior C: 2.73 (v2: 3.08).

### E. Pytania do autora
- **Q1** Numeracja: w kodzie H v2 (549/226, RMSE 1.749) = "Tab. 4.2", a "Tab. 4.3" = C v2 (4 podzbiory). Ktora tabela raportu PW.S-1063 jest wartoscia referencyjna - H v2 (jak zakladam)?
- **Q2** Czy referencja ma byc zbiorem H (eksploracyjnym, do ktorego dobrano metode w Z14b) - czy test regresji ma zawierac tez C v2 (2.73 / v2 3.08) jako "uczciwy" prog? Jaka deklaracja dokladnosci w dokumentacji N2?
- **Q3** Parametry zamrozone: czy produkt ma uzywac stalych sprzed poprawki czasu OM (E2-T05 z `output\`, tak odtwarzana referencja), czy po poprawce (`_omfix_check`, TN h0 13.64, c_vol 2.4805e6, RMSE kalibracji 1.592)? Zmieni to wynik o <~0.01-0.02 C - ktora wersja jest "wiazaca"?
- **Q4** `IR_masa = IR - delta_hat`, gdzie delta ~ IR - t_2cm; kalibracja porownuje je z Ts wezla z=0. Czy to zamierzone (Ts ~ temperatura "masy" 2 cm) - czy docelowo powinno byc porownanie z temperatura na 2 cm modelu?
- **Q5** Kalibracja moze tylko zmniejszac a_sw (a<=1.0); 44% H = bound_hi. Czy w N2 dopuscic a_sw > 1 (k_SW ~1.07 wg Z4 diagnostyki SW), czy zostawic `bound_hi` jako flage "kalibracja nasycona"?
- **Q6** Definicja flagi pory: czy "noc" ma byc liczona z godziny aparatu (0-6/18-24), z SW reanalizy (< 5 W/m2), czy z flagi `gate` (11 obs. w H, 19.9% FWD na sieci)? Czas aparatu jest "niepotwierdzony" (P6).
- **Q7** Czy N2 ma obslugiwac klase zacieniona (Podkowa: a_sw 0.166, svf 0.316, alpha 8.72e-7) jako opcje, skoro model TN daje tam bias +3..+5 C; i skad brac informacje o zacienieniu przy pomiarze (brak w CSV)?
- **Q8** Pirometr TSD (`temp_road`) i pirometr aparatu FWD != Qulon-RTS stacji (zrodlo beta_ir). Czy N2 ma stosowac te same wspolczynniki dla TSD i FWD (jak Z15) i jak oznaczac niepewnosc?
- **Q9** Dane OM dla pomiarow "z dnia dzisiejszego": archiwum ma opoznienie; czy dopuszczalna jest wylacznie obrobka pomiarow archiwalnych (jak dotad), czy potrzebny jest tryb forecast/historical-forecast (to inne API - poza "jedynym dopuszczalnym polaczeniem")?
- **Q10** Cache OM: czy produkt ma wersjonowac produkt/model OM (best_match zmienia sklad w czasie; archiwum bywa korygowane) i zapisywac `grid_lat/grid_lon`+`fetched_at` w wyniku? Czy dopuszczalny jest pakiet z cache testowym (21 MB) w repo?
- **Q11** Glebokosc: N2 ma liczyc na dowolnej glebokosci (1 cm siatka, zakres 0-50 cm) - czy walidacja jest tylko dla 12 cm (i 10 cm w 258 wierszach `odcinki_1km`)? Czy "polowa pakietu" = grubosc/2 (tu 12 cm z definicji standardu) i czy grubosc pakietu ma jakiekolwiek znaczenie (model jej nie uzywa: Z5/Z14b 0.0000 C)?
- **Q12** Znaczenie: Z14-lite/Z14b liczby IV-X sa dotkniete erratum - czy "do przeliczenia pod nowymi ID" (nadal nie zrobione)? Czy `E3-T30..T38` mozna ignorowac w dokumentacji N2?
- **Q13** Stacja 16322 wylaczona (pomylka operatora) - czy wylaczenie zostaje w teście referencyjnym (549), a do dokumentacji N2 wystarczy lista obs.?
