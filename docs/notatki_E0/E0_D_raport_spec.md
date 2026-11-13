# E0_D — specyfikacja funkcjonalna narzędzi N1–N4 wyciągnięta z raportu PW.S-1063 (v1.12, 2026-11-13)

Źródło: `C:\WORK\DOKTORAT\publikacje_monografia\raport_PWS-1063\raport_PWS-1063_tekst.md` (1320 linii, tylko odczyt).
Konwencje: „L###” = numer linii w pliku; „R x.y” = rozdział raportu; „Tab. x.y” = tabela raportu; „[C##]” = numer komentarza HTML z rejestru w sekcji 1 (pełny tekst wszystkich komentarzy w Aneksie A na końcu pliku). Wartości z komentarzy HTML (nie z tekstu głównego) oznaczono „(kom.)”. Obliczenia własne (nie z raportu) oznaczono „(obl. własne)”.
Raport jest szkicem v1.12 z otwartymi decyzjami autora; liczby z komentarzy bywają bardziej szczegółowe niż tekst.

---------------------------------------------------------------------
## 1. REJESTR KOMENTARZY HTML (`<!-- -->`) — 95 sztuk

Liczba: **95** komentarzy (grep `<!--` = 95; 4 są wieloliniowe: L6 [C01], L415 [C35], L611 [C43], L687 [C48]).
Większość to „źródło: …” wskazujące tabele CSV / skrypty / wpisy dziennika SQL_TSD_FWD (P0xx, wpis N, commit) i DOKTORAT (Z14d, Z15b, Z16, E3-T..). Poniżej: numer, linia, rozdział/tabela, treść skrócona. Pełny tekst: Aneks A.

Legenda skrótów w komentarzach: SQL = repozytorium SQL_TSD_FWD (projekt bazy), DOKTORAT = C:\WORK\DOKTORAT (temp_model), P0xx = zlecenie wykonawcze, W### = rejestr wniosków, „wpis N” = dziennik prac, PUB-E = monografie/PUB-E_normalizacja_FWD_stacje.md (publikacja_2).

### 1.1 Komentarze wskazujące tabele źródłowe i skrypty bezpośrednio istotne dla N1–N4

| ID | L | Rozdz./Tab. | Źródło wskazane w komentarzu (tabele CSV / skrypty / commity) |
|---|---|---|---|
| C23 | 304 | R3.6, **Tab. 3.2** | raport_metodyka_baza_TSD_FWD.md rozdz. 4.2, tabela 2 |
| C24 | 307 | R3.6 (akapit o progach 5 stacji / 500 m) | raport_metodyka rozdz. 4.3 |
| C25 | 320 | R3.7 | raport_metodyka rozdz. 6.1, 6.2 |
| C26 | 336 | R3.8 (kontrola na całej sieci) | SQL P071 (wpis 254, commit ffd2e85): `tabele/e2bR9_lustro_warianty.csv` (5511 par, 36 sesji, main_after; r_within_session: W5 0,403 — zerowe 0,155/0,135/0,096; W10 0,511 — 0,150/0,153/0,087; X_b1510 0,508 — 0,149/0,163/0,076; C_raw 0,615 — 0,565/0,557/0,559; X_nom 0,405; median_ratio X_nom 0,523, C_raw 1,063, W5 1,615; pearson_r łącznie X_nom 0,257, X_b1510 0,750); `e2bR9_lustro_kalibracja.csv` (W5 mnożnik k02: MAE w próbie 27,68 µm, poza próbą 27,74 µm; C_X afiniczna 22,89/23,71 µm); `e2bR9_lustro_warunki.csv` (r Pearsona logarytmów, wszystkie pary warstwy łącznie, bez przedziałów). Sesje 225–227 = fwd_sessions baza_odcinki_v4 (2026-05-18…20; km 43–46 i 6–9,4) — odcinki tsd_2_xml. Sprostowanie: udział „artefaktu wygładzania” (~40 %) liczony na korelacji łącznej; w obrębie sesji zysk z okna ±10 m jest w całości prawdziwy. Pilotaż GoF: pomysy_idee_plany/etap2_koncepcja_dopasowania.md rozdz. 2 (wpis 26) |
| C27 | 337 | R3.8 | metodyka_zlotych_par.md; W169, W170 |
| C28 | 348 | R3.9 | raport_metodyka rozdz. 9.1–9.4, raport_techniczny rozdz. 14, 16.2; W167 |
| C29 | 353 | R3.9 (temperatura w FWD sieciowych) | W16, W17, W18; W168 |
| C30 | 360 | R3.10 | uwaga Jacka 2026-11-12: eksport nominalny TSD ma kolumny D-450…D1500; źródło W91 (F1 Lorentz D900/D1500 +106/+197 %, F2 rozciągnięta wykładnicza −51/−78 %; wpisy 105–106), W92 |
| C31 | 370 | R3.10 (całki nachyleń P0/T/PX) | kod SQL: `bak/e2a2b_beta.py` (CHANNELS_9 bez 1,51 m; dense_integral, INTSTEP 1 mm; P0 / T [e2a_autc_1b.autc_front, slope(0)=0] / PX [od x_max]), `bak/e2b2_values.py` (sieć: P0 w każdym wierszu, mediana całek w oknie), `bak/e2a4b_qa.py`, `bak/e2a4_dbeta.py` (mikroodcinki: p0_a031/a0361/a6191 ↔ SCI300/BDI/BCI), `bak/e2aR7_tsd_indices_from_slopes.py`, `bak/e2bR8_kontrola_E3.py` (T); baza `bazy/baza_analizy_e2a.db`, tabela e2a2_points; `tabele/e2a2_autc_var.csv`; `tabele/e2a2_beta_m8.csv`, `e2a2_beta_pairs_m8.csv` (P029, wpis 114; M8 quasi-Poisson, efekt stały punktu); `tabele/basin_1510off.csv`. Liczby: ilorazy eksport/P0 1,247 [1,036; 1,795] n 1253, T/P0 0,904, PX/P0 1,033, FWD/P0 1,131; korelacje log: eksport–P0 0,83, P0–FWD 0,79, eksport–FWD 0,82; niedodatnie: P0 55/1308, T 35/1308, PX 8/1244, eksport 0/1308; wrażliwości sci300_fwd 3,694; p0_a031 2,842 (diff [−1,455; +0,058]); px_a031 2,671 ([−1,570; −0,144]); autc_a031=T 2,623 ([−1,613; −0,230]); sci300_prod_tsd 2,204 ([−1,828; −0,929]); eksport nominalny d0_export/d0_prod_1510off: mediana 1,258, n 1241. „Do potwierdzenia przez SQL przy najbliższym zleceniu.” |
| C32 | 371 | R3.10 | plan_badan_etapy.md (K-dane, wpisy 85–106); W80–W92; raport_techniczny rozdz. 16.1, 20.5 |
| C34 | 402 | R3.12, **Tab. 3.3** | Z16 (DOKTORAT 5dec2b7, temp_model/output/z16/raport_Z16.md; E3-T59 bootstrap stacjonarny, długość bloku Politis–White 336–440 rekordów; E3-T60 test DM: HAC Bartlett/Andrews na szeregu 10-min i średnie dobowe z poprawką HLN); P068 (SQL 16b93cd, wpis 246: `tabele/e2x_niepewnosc_metody.csv`, `e2x_niepewnosc_werdykty.csv`, `kontrolne/e2x_synthetic_coverage.csv`; M1 = dziki bootstrap klastrowy, wagi Webba, 9999 replik; M2 = CR2 z poprawką Bella–McCaffreya). Jedyny wynik graniczny: Z16, profil stacjonarny TN, test DM po 7 foldach p = 0,05 |
| C35 | 415 | R4 (cały) | publikacja_1 v5.3 (załącznik A) §2–4; liczby na wspólnym wsparciu czasowym (Z8; n = 26 490 TN / 28 348 Podkowa); starsze „headline” z rozdz07 §7.6 (hybryda B 1,24/0,77; fizyka 1,46/1,06) NIE są używane |
| C36 | 438 | R4.2 | usunięte zdanie o teście przesunięcia czasu ±3 h (zimą dało zero mimo błędnych etykiet) — „do wyjaśnienia (Jacek), nie cytować” |
| C37 | 529 | R4.7, **Tab. 4.1** | Z15b (DOKTORAT d5602cd, wymiana/wyniki/raport_PWS/liczby_rozdz4.md): `temp_model/output/_omfix_check/E3-T06` + `E3-T20` (fold), łańcuch E3 po poprawce etykiet czasu Open-Meteo (Z14d cz. B); przed poprawką (=publikacja_1 Table 2): ML TN 2,44; fizyka TN 1,49; hybryda A TN 1,41; hybryda B 1,26 [1,08; 1,44]/0,74 [0,62; 0,87]; przewodnictwo TN 0,95 [0,79; 1,11] |
| C38 | 549 | R4.7, **Tab. 4.2** | Z15b, `temp_model/output/z14lite/z14d/Z15b_T41_robust.csv` (z `_omfix_check/E3-T07`, IV–X, snow=exclude, własna stacja). BELLS3, BELLS3_O, ML: łańcuch nie zapisuje predykcji — brak miar odpornych |
| C39 | 555 | R4.7 | `_omfix_check/E3-T06` (survey, monthly): BELLS3 TN 3,861 / bias −2,871; Podkowa 2,000 / −0,415; BELLS3_O 3,750 / −2,664; 1,567 / −0,082. Z14-lite (2026-10-31): BELLS3_O nic nie wnosi — odniesieniem jest BELLS3 |
| C40 | 562 | R4.7 (lato/noc) | Z16: `temp_model/output/z16/Z16_T1_lato_noc.csv` [E3-T58], `Z16_T1b_lato_noc_ci.csv` (różnica B−fizyka, bootstrap z losowaniem dób: lato TN −0,37 [−0,48; −0,27], Podkowa −0,36 [−0,45; −0,28]; noc TN −0,20 [−0,30; −0,10], Podkowa −0,28 [−0,39; −0,17]; wieczór −0,23/−0,39; dzień −0,32/−0,45); czas lokalny stanowiska |
| C41 | 573 | R4.7 (ekstrapolacja sezonowa) | Z15b, `_omfix_check/E3-T06` (split = seasonal); przed poprawką 2,44/1,83 → 3,46/2,61; 1,41/0,87 → 1,96/1,60; 1,49/1,12 → 1,58/1,14; 1,26/0,74 → 1,33/0,82 |
| C42 | 607 | R4.9 | publikacja_1 §4.4; β D0 = 1,60 %/°C z W136; 1,22×1,6=1,95; 0,72×1,6=1,15; 1,48×1,6=2,37; 1,12×1,6=1,79; BELLS3 3,86×1,6=6,18; 2,00×1,6=3,20; σ=1,37 % — `e2a3_repeatability_v3` |
| C43 | 611 | R4.10 | DOKTORAT temp_model, Z14-lite → Z14d (`output/z14lite/**/raport_*.md`); liczby Z14d (E3-T46..T55); tabele i rysunki PL do wygenerowania (E3-F29, E3-F31) |
| C44 | 639 | R4.10, **Tab. 4.3** | E3-T46/T47 (Z14d); mediana i P90: Z15b, `temp_model/output/z14lite/z14d/Z15b_T42_robust.csv` (bootstrap po sesjach, 2000 replik); kontrola RMSE/MAE/obciążenie zgodne z E3-T46 do 0,001 °C |
| C45 | 665 | R4.10, **Tab. 4.4** | E3-T53 (Z14d, C v2) — RMSE i przedziały; MAE, mediana, P90: Z15b `Z15b_T43_robust.csv` (kontrola RMSE do 0,01 °C); na stanowiskach modele stanowiskowe z podziału z wyłączonym miesiącem wizyty |
| C46 | 672 | R4.10 (znaczenie dla korekty D0) | E3-T48 (Z14d), wariant wykładniczy β = 0,016 |
| C47 | 681 | R4.10 | rozstrzygnięcia Jacka 2026-11-06/09: Tab. 4.1 i liczby 4.7–4.9 po poprawce czasu reanalizy; „latem/w nocy” — Z16 |
| C48 | 687 | R5 (cały) | publikacja_2 = PUB-E_normalizacja_FWD_stacje.md (stan a2440fe); estymator referencyjny P040 (wpisy 143–145); liczby W102–W140 |
| C49 | 729 | R5.2 | W136, W137; wpisy 144, 145; `e2a3_final_k_profile`, `e2a3_final_norm_test` |
| C50 | 748 | R5.3, **Tab. 5.1** | `tabele/e2a3_final_k_profile.csv` (k_guide), commit a2440fe; Podkowa D900–D1800: przedziały obejmują 0 |
| C51 | 749 | R5.3 | W136, wpis 144; przedziały ufności i wartości osobno dla stanowisk — „załącznik C”; współczynniki wskaźników (k_guide SCI300/BDI/BCI w e2a3_final_k_profile) usunięte w v1.8 — decyzja Jacka 2026-11-12 |
| C52 | 759 | R5.3 (CV wariantów korekty) | W137; `e2a3_final_norm_test` (łącznie, cv_month, trend_resid; średnia 9 czujników D0–D1800: i_k02 0,0423/−1,089; ii_beta_D0 0,0331/−0,679; iii_beta_own 0,0191/−0,002; D900–D1800: i_k02 0,0490–0,0526, iii_beta_own 0,0152–0,0189); SCI300 z ugięć skorygowanych: `e2aR4_indices_norm` (R1 0,0939/+0,430; CB 0,0756/+0,0068) |
| C53 | 770 | R5.4 | W115; wpisy 126, 127; `e2a3_nonlin` |
| C54 | 773 | R5.4 (próg pasm) | `e2aR2_rules_bands_R4.csv` (D0, R4, łącznie, no_thaw): 0–5 i 5–10 °C n_with_ref 0; 10–15 °C n_with_ref 18 (<20 — próg pasma); od 15–20 °C n ≥ 108 |
| C55 | 804 | R5.4, **Tab. 5.2** | `e2aR_equivalence.csv` (P049, commit 1c0ccb8; errata — wpis 192; form = guideline/exponential, boot_day, band_wide); `e2aR4_indices_bands.csv` (P052, wpis 201, commity 4618ceb, 55a1871; error_def = log; wariant CB przyjęty do publikacji_2 — wpis 202); SCI300 CB 30–35 °C: n = 24 (1 wizyta z SCI300₂₀ ≤ 0 wyłączona; wariant ilorazowy −12,1 %); pasmo 30–35 °C: D200 −0,58 [−3,12; +1,20], D600 +0,45 [−2,00; +2,39], D900 +0,95 [−1,44; +2,76]; mikroodcinki 30–35 °C: brak danych |
| C56 | 813 | R5.4 (mechanizm błędu SCI300) | SQL P070 (wpis 252, commit 66d64b1): `e2bR8_sci_wzmocnienie.csv` (25_30_CB łącznie: n 49, A mediana 4,86 — TN 4,97, Podkowa 4,22; średnia e_SCI −6,77; rozkład per obserwacja −7,08, R² 0,99); `e2bR8_ksztalt_czaszy_T.csv` (ln_D300_D0: 5–25 °C −0,46 [−0,58; −0,35], ≥25 °C +0,10 [−0,03; +0,32] %/°C); `e2bR8_mikro_zmiennosc_sci.csv` (119 grup odcinek × noc: CV FWD D0 0,108, D300 0,105, SCI300 0,174, korelacja D0–D300 0,958; między nocami po korekcie, 8 odcinków: D0 0,066, SCI300 0,130); `e2aR7_sci_noise_decomp`, `e2aR7_bands_minn5` |
| C57 | 816 | R5.4 (obecny wzór k=0,02) | `e2aR2_rules_bands.csv` (P050, commit 7cfe5d1; łącznie, no_thaw, R1 = k 0,02 na każdym czujniku, R2 = k 0,01; przedziały 90 %, bootstrap po dniach): D0 15–20 +0,44 [0,09; 0,76], 20–25 −0,44 [−0,76; −0,08], 25–30 −3,96 [−5,02; −2,87], 30–35 −9,00 [−12,60; −6,11]; D300 15–20 +1,23 [0,61; 1,64], 20–25 −1,20 [−1,55; −0,63], 25–30 −5,83 [−6,85; −4,83], 30–35 −11,39 [−12,60; −9,92]; D900 15–20 +2,99 [1,91; 3,64], 20–25 −2,94 [−3,51; −1,91], 25–30 −11,18 [−12,35; −9,73], 30–35 −20,17 [−22,15; −18,01]; R2 D0 25–30 +3,28 [2,20; 4,17]. Zgodne z publikacją_2 v2.8 Tabela 3 |
| C58 | 819 | R5.4 (pasmo 10–15) | P069 część A (wpis 250, 7c80b5a): `e2aR7_bands_minn5.csv` (band 10_15, n_with_ref 18, n_days 6, n_groups 8; R1: D0 +3,23 [0,96; 4,28], D300 +5,55 [2,30; 6,74], D900 +9,61 [5,67; 11,34], SCI300 −6,71 [−9,63; −2,88]; exp_beta525: D0 +1,81 [−0,20; 2,91], D300 +1,63 [−0,76; 2,69], D900 +0,66 [−1,35; 1,72]); TN 2, Podkowa 16 obserwacji |
| C59 | 822 | R5.4 (SCI300 przy k=0,02) | `e2aR4_indices_bands.csv` (R1; 95 %: SCI300 15–20 −2,69 [−3,99; −1,12], 20–25 +2,64 [1,08; 3,67]; BDI 15–20 −1,99 [−2,77; −1,09], 20–25 +1,95 [1,13; 2,60]); `e2a3_final_norm_test.csv` (SCI300 i_k02 trend_resid +0,430 µm/°C); `e2aR2_rules_bands_R4.csv` (P068b b2fd5ee; R4 / R3a_z_ugiec, SCI300, 90 %: 15–20 −0,68 [−1,62; +0,40] / −0,64 [−1,55; +0,38]; 20–25 +0,67 [−0,42; +1,48] / +0,63 [−0,40; +1,44]); SCI300 R1 25–30 +3,01 [−2,08; +7,92] (90 %) |
| C60 | 827 | R5.4 (wniosek, postać liniowa vs wykładnicza) | W122, W132; wpisy 128, 130–133, 191–192; `e2a3_range30_v2`, `e2a3_range30_micro_v2`, `e2a3_repeatability_v3`, `e2aR_equivalence`; postep_prac.md W2 |
| C61 | 830 | R5.4 (okno pomiarowe) | W123; `cowork_e2a3_okno_pomiarowe.csv` |
| C62 | 837 | R5.5 | W111; wpisy 122–124 |
| C63 | 844 | R5.5 | W112; PUB-E §4.6, §5 (plan S vs D) |
| C64–C66 | 859, 861, 873 | R5.6 | W134 („nie przypisywać przyczyny wartości α=0,01 dla autostrad”); W121, W130, W131, W134; `e2a3_station_vs_h_harm`, `e2a3_beta_bands`; `tabele/e2aR_lamb_k_profile.csv` (wariant (a) sonda, P049) |
| C67 | 890 | R5.7, **Tab. 5.3** | `e2a3_final_seasonal.csv` (łącznie, D0, 5_30, iii_beta_own; XI 1,0549→1,05); kwiecień: SQL P067 (wpis 244, commit 8a103be), `kontrolne/e2a3_final_seasonal_april.csv`; wiersze f_s jak publikacja_2 v2.6 Tabela 4 (DSN zał. A tab. 1.2; Graczyk 2008) |
| C68 | 899 | R5.7 | W138, W139; wpisy 144, 145; `e2a3_final_seasonal`, `e2a3_final_beta_seasonal*` |
| C69 | 916 | R5.8 | publikacja_2 v2.7 §3.6; P053 (`e2aR5_depth_dcv`), P054/P054b (wpisy 207–209): `e2aR6_depth_oos.csv` (ΔCV poza próbą: D300 −13,98 [−32,09; −6,06], D600 −23,86 [−38,84; −15,50], D900 −17,90 [−29,49; −6,64], BCI −24,06 [−29,38; −5,06], D0 −7,40 [−13,58; +16,22], SCI300 +1,74 [−15,83; +8,18]), `e2aR6_depth_time_split.csv`, `e2aR6_depth_probe_oos.csv` |
| C70 | 940 | R6.1, **Tab. 6.1** | P069 część E1 (wpis 250, 7c80b5a): `tabele/e2aR7_dbeta_slopes.csv` (M0, M1_WCU; dbeta_lo90/hi90; n_nights = 14); log `e2aR7_tsd_indices_from_slopes.log`; kontrola E0: Δβ d0 −0,102 odtworzone z `e2a4b_dbeta`; poprzednio Δβ odpowiedników SCI300/BDI/BCI: −0,53/−0,35/+0,10 %/°C |
| C71 | 961 | R6.1, **Tab. 6.2** | d0: `e2aR_equivalence.csv` (P049, wpis 192), `e2x_tab62_male_klastry.csv` (P068b, M1/M2; M3 dla d0: 5/10 %); nachylenia: `e2aR7_dbeta_slopes.csv` (M0, M1_WCU, M2_CR2); kanał 0,91 m poprawiony w P070 (`e2aR7_dbeta_slopes_v2.csv`); wariant z losowaniem odcinków pominięty (decyzja 2026-10-25) |
| C72 | 964 | R6.1 | P068b część A (wpis 248, b2fd5ee), `e2x_tab62_male_klastry.csv`: d0 e30 przedziały 90 % M1 [−3,71; +1,74], M2 [−3,45; +1,48], M3 [−4,48; +2,60] → min. δ = 5; e5 M1 [−2,55; +5,93], M2 [−2,18; +5,41] → δ = 7; M3 WCU [−3,89; +7,03] → δ = 10 |
| C73–C74 | 967, 970 | R6.1 | W146; W100 |
| C75 | 983 | R6.2 | to samo co C26 (P071, `e2bR9_*`) |
| C76 | 986 | R6.2 | W161–W163, W167, W169, W170; wpisy 176–189 |
| C77 | 990 | R6.3 | SQL_TSD_FWD P065 (wpis 240, commit e5d6791): `tabele/z15_korekta_TSD_FWD_{main,groups,deming,q1q3,conversion}.csv`, rysunki `plots/e2b/z15_*.png`; temperatura T12: DOKTORAT Z15 (E3-T57, `temp_model/output/z15/raport_Z15.md`, D007), model z R4.10 (Z14 v2). Mikroodcinki: obliczenie Cowork 2026-11-07 z `e2a4b_qa_section_night.csv`, `e2a4b_qa_section.csv` (P042 faza A, wpis 155): mediana ilorazu median_fwd_d0 / median_tsd_d0 po 119 kombinacjach odcinek × noc; **definicje wielkości sprawdzone w kodzie: FWD = D·50/F (p027_e2a2_build / e2b2_values); TSD d0 = B_1510off, okno ±5 m**; Pearson liczony na logarytmach (`e2b2_agreement.point_stats`) |
| C78 | 1026 | R6.3, **Tab. 6.3** | `z15_korekta_TSD_FWD_main.csv` wiersze main_before / main_after; mad_log_ratio = 1,4826·MAD; kolumna „przed” = `e2b2_agreement.csv`; **CCC nie podano w tekście; wartości CCC: przed 0,42, po 0,35** |
| C79 | 1052 | R6.3, **Tab. 6.4** | `z15_korekta_TSD_FWD_groups.csv` (device_group: hwd_2024, hwd_2026, old_2024, old_2025, unconfirmed_2026; „old”=8002-367, „unconfirmed”=8002-369 wg plik_wymiany_informacji.md; 8082-119 = hwd); Q2: `z15_korekta_TSD_FWD_q1q3.csv`; rozstęp median w skali log: ln(1,633/0,981)=0,510 → ln(1,773/1,310)=0,303 |
| C80 | 1067 | R6.3, **Tab. 6.5** | `z15_korekta_TSD_FWD_main.csv`, wiersze *_after (main, bells3, linear, strict_calib, operator_fresh); operator_fresh_before w CSV to kopia main_before (n=5511), nie podzbiór 33 par — nie cytować |
| C81 | 1070 | R6.3 (poziomy uśrednienia d0) | P066 (wpis 242, commit 3b92044), `z15_krzywizna_TSD_FWD_poziomy.csv` (metric = d0, L2/L3, main_after; λ jak na L1; bootstrap po sesjach) |
| C82 | 1085 | R6.3 (strona FWD krzywizny) | v1.10: P070 (wpis 252) nie rozstrzygnął wpływu korekty kanał po kanale na iloraz krzywizny (wariant kanałowy c_channel: wielkość FWD = całka nachyleń FWD (autc_front), w innych wariantach D0−D300 → rozkład 1,28→0,95 miesza zmianę korekty ze zmianą definicji). Mikroodcinki: metoda R6.3 1,10, bez korekty 1,09 (742 pary, całkowanie trapezowe). Nachylenie Deminga <1 we wszystkich wariantach skorygowanych |
| C83 | 1113 | R6.3, **Tab. 6.6** | P066 (wpis 242, commity 3b92044, efca1ec): `z15_krzywizna_TSD_FWD_poziomy.csv` (main_after), `z15_krzywizna_TSD_FWD_q.csv` (Q1–Q4); n = pary/przedziały z dodatnimi wartościami po obu stronach; kontrole STOP P066 przeszły |
| C84 | 1120 | R6.3 (mikroodcinki, krzywizna) | P066 `z15_krzywizna_TSD_FWD_mikro.csv`; oba zbiory P0 (PCHIP, dense_integral): mikroodcinki p0_a031 z `e2a2_autc_var` przez `e2a4b_qa` (całka z median nachyleń w oknie), sieć `e2b2_values` (mediana całek z rekordów) |
| C85 | 1123 | R6.3 (interpretacja) | `e2a3_repeatability_v3.csv` (SCI300 TN 2,389 %, Podkowa 14,61 %; D0 1,369/4,633 %); `e2b2_lambda.csv` (sigma_tsd a031 0,593, d0 0,296) |
| C86 | 1130 | R6.3 (przelicznik SCI300) | `z15_krzywizna_TSD_FWD_poziomy.csv`, sci300 main_after: L1 median 2,2384 [1,99; 2,53]; Deming log-log L1: wyraz wolny 1,96 [1,80; 2,20], nachylenie 0,57 [0,45; 0,63] → exp(1,96)=7,1; mad_log_ratio 0,80 → połowa par w ×/÷ exp(0,674·0,80)=1,72; share_nonpos_tsd L1 po korekcie 0,37; L2 2,29; L3 2,75; mikro 1,28. Decyzja Jacka 2026-11-09: przelicznik SCI podać nawet z dużym błędem |
| C87 | 1145 | R7.1 (wariant A, błędy w 25–35 °C) | P068b część B (wpis 248, commit b2fd5ee): `tabele/e2aR2_rules_bands_R4.csv` — **reguła R4 = postać liniowa ze stałymi k_guide z e2a3_final_k_profile (D0 0,01611; D300 0,01234; D600 0,00703; D900 0,00329)**, łącznie, bez roztopów, referencja 15–25 °C w grupie punkt × miesiąc, bootstrap po dniach, 90 %: D0 15–20 −0,22 [−0,49; +0,09], 20–25 +0,22 [−0,10; +0,49], 25–30 −1,06 [−2,07; −0,05], 30–35 −3,76 [−6,83; −1,20]; D300 15–20/20–25 ±0,09; SCI300 z ugięć 15–20 −0,68 [−1,62; +0,40], 20–25 +0,67 [−0,42; +1,48], 25–30 −6,02 [−12,26; −0,37]. Wariant B ze stałymi β (R3a, `e2aR2_rules_bands.csv`, no_thaw): D0 25–30 −0,31 [−1,39; +0,63], 30–35 −1,77 [−4,74; +0,76]; SCI300 z ugięć (R3a_z_ugiec, `e2aR2_rules_bands_R4.csv`) 25–30 −4,13 [−10,30; +1,42] |
| C88 | 1166 | R7.1, **Tab. 7.1** | `tabele/e2a3_final_k_profile.csv`, scope = łącznie (k_guide, beta_pct); jak Tab. 5.1. Na Podkowie k dla D900–D1800 bliskie zeru (przedziały obejmują 0) — wartości łączne dla dalekich czujników orientacyjne. Współczynników wskaźników nie podaje się (v1.8) |
| C89 | 1168 | R7.1 | błędy obu wariantów w 25–30 °C z testu zakresu (R5.4, Tab. 5.2): współczynniki dopasowane na 5–25 °C, odniesienie 15–25 °C (e2aR_equivalence guideline/exponential; e2aR4_indices_bands CB). **Tab. 7.1 = dopasowanie 5–30 °C (Tab. 5.1); w teście zakresu postać liniowa miała k dopasowane na 5–25 °C (łącznie 0,0175, e2a3_range30_v2), nie stałe 0,016**; wynik dla stałych k z Tab. 7.1 (reguła R4): P068b część B |
| C90 | 1215 | **R7.3 p. 7 („D Tkor”)** | **`C:\WORK\DOKTORAT\tsd_2_xml` (README_workflow.md, tsd_pipeline.py, calibrate_conversion.py, compare_tsd_fwd.py; stan 2026-07-01): czasza „D Tkor” z pliku 1 m — BELLS3_BT + k = 0,02 (informacja Jacka 2026-11-13), Hampel na D0 + średnia ±10 m, konwersja afiniczna DK50 a 0,849 b +24,35, S8 a 0,473 b +41,72; dopasowanie „value ±5 m” w compare_tsd_fwd.py** |

### 1.2 Komentarze historyczne / redakcyjne / bibliograficzne (bez znaczenia dla funkcji narzędzi)
C01 (L6, wieloliniowy: historia wersji v0.1–v1.12 — patrz Aneks A; zawiera m.in. zasadę „najpierw korekta na czujnikach, potem wskaźniki” (v1.8), „postać liniowa tylko 5–25 °C, szerszy zakres tylko wykładnicza” (v1.3), P068b/P069/P070/P071), C02 (L66 f_s: III 1,00; IV 1,04; V 1,08; VI 1,12; VII 1,15; VIII 1,17; IX 1,20; X 1,22; XI 1,25; XII 1,28), C03 (L69 decyzja 2026-11-09: źródła Janowskiego niedostępne), C04 (L70 W113), C05–C09 (R2.1: PUB-E §2; publikacja_1 §2; 52 560 wierszy/stację, braki 0,13–0,17 %, DST 12 wierszy; 593 wizyty), C10–C11 (R2.2: W115 mróz D0 82–88 µm, roztopy 134–196 µm), C12–C14 (R2.3: W102, W106, wpis 124), C15–C17 (R2.4: raport_metodyka 10.1; PUB-E §4.7 estymator T10), C18–C22 (R3.1–3.5: raport_techniczny_baza_TSD_FWD.md), C33 (R3.11), C91 (L1249 rejestr językowy wniosków), C92–C95 (L1270–L1320: literatura/numeracja).

---------------------------------------------------------------------
## 2. SPECYFIKACJA FUNKCJONALNA — N1 `fwd_tempcorr` (korekta temperaturowa ugięć FWD; R7.1, R5, R2.2, R3.9)

### 2.1 Cel i wejścia/wyjścia (R7.4)
„współczynniki czujników z Tab. 7.1 (wariant A lub B), wskaźniki z ugięć skorygowanych, odczyt plików pomiarowych FWD i zapis wyników z oznaczeniem pomiarów spoza zakresu temperatury.” Pliki FWD: Dynatest (zrzuty, siły, historie czasowe; R3.4 p.1); w danych bazy także XLS/MDB wg skilla projektu (nie w raporcie).
Wejście per stacja/zrzut: ugięcia D0…D1800, siła F, T_mid [°C], metadane (głębokość odczytu T, źródło T, aparat).
Wyjście: ugięcia skorygowane do 20 °C dla wszystkich czujników, SCI300/BDI/BCI z ugięć skorygowanych, flagi zakresu/jakości T, wariant, wersja współczynników.

### 2.2 Wzory
**Normalizacja siły (R2.2, R6.3, kom. C77):** D_norm = D · 50/F (F = siła zrzutu w kN); do analiz przyjęto drugi zrzut przy nominalnym obciążeniu 50 kN; na stanowiskach tylko 50 kN. R3.8: „Ugięcia obu urządzeń przelicza się do wspólnego obciążenia 50 kN”.
**Czujniki FWD (R2.2):** 0, 200, 300, 450, 600, 900, 1200, 1500, 1800 mm od środka obciążenia (D0, D200, D300, D450, D600, D900, D1200, D1500, D1800).
**Wskaźniki krzywizny (R2.2):** SCI300 = D0 − D300; BDI = D300 − D600; BCI = D600 − D900. **Liczone z ugięć skorygowanych** (R5.3, R7.1): SCI300₂₀ = D0₂₀ − D300₂₀, BDI₂₀ = D300₂₀ − D600₂₀, BCI₂₀ = D600₂₀ − D900₂₀. Brak własnych współczynników wskaźników (decyzja 2026-11-12, v1.8). Uzasadnienie: współczynnik wskaźnika = (D0·f₀ − D300·f₃₀₀)/(D0 − D300) zależy od D300/D0 (kształt czaszy) i się nie przenosi (R5.3).
**Wariant A (R7.1):** d₂₀ = d_T · [1 + k_i · (20 − T_mid)], k_i z Tab. 7.1 [°C⁻¹]; D0: k = 0,016 (zamiast 0,02). **Zakres T_mid 5–25 °C.**
**Wariant B (R7.1):** d₂₀ = d_T · exp[β_i · (20 − T_mid)], β_i z Tab. 7.1 w %/°C (czyli β_i/100 w °C⁻¹); D0: β = 1,60 %/°C. **Zakres T_mid 5–30 °C.**
Temperatura odniesienia 20 °C. T_mid = temperatura w połowie grubości pakietu asfaltowego w chwili pomiaru (odpowiedź ugięcia praktycznie natychmiastowa; najlepiej temperatura bieżąca lub opóźniona ≤1–2 h; R5.5). Wzór krajowy dotychczasowy: d₂₀ = d_T·[1 + k·(20 − T_b)], k = 0,02 [R1.2, [2]]; w narzędziu jako tryb porównawczy/„legacy”.
**Estymacja współczynników (R5.1; jeśli narzędzie ma moduł dopasowania):** ln D = a_p + β·(T − 20) [+ efekt miesiąca], a_p = efekt stały punktu; GLM z funkcją wiążącą log na średniej (quasi-Poisson), plan S (między wizytami; stały efekt punkt × miesiąc, wizyty 5 ≤ T_mid < 30 °C) i D (w obrębie dnia; punkt × dzień); T_mid z czujników interpolowana liniowo na chwilę zrzutu i połowę grubości; niepewność: bootstrap blokowy po dniach, 1000 replik; k (postać krajowa) i β (%/°C) podawane obok siebie; β = k w temperaturze odniesienia.
**Równoważność postaci:** w 20 °C to samo nachylenie (β = k); R5.1 „w zakresie 5–30 °C korekty różnią się o mniej niż 2 %”; R7.1 B „w zakresie 5–25 °C różnią się o mniej niż 2 %” (obl. własne: D0 k=0,0161 — różnica exp/lin 2,55 % przy 5 °C, 1,18 % przy 10 °C, 0,34 % przy 25 °C, 1,47 % przy 30 °C, 3,56 % przy 35 °C; D200 1,96 % przy 5 °C; D300 1,54 %).

### 2.3 Zakresy ważności i flagi (R7.1, R5.4, R8)
- T_mid < 5 °C: **korekta nie ma zastosowania** (o ugięciu decyduje podłoże: mróz D0 82–88 µm vs roztopy 134–196 µm przy podobnej T; styczeń 2026 wyłączony z analiz).
- Wariant A: 5–25 °C; wariant B: 5–30 °C; poza zakresem — oznaczać (nie usuwać; R7.3 p.3, R3.9 „rejestr oznaczeń zamiast usuwania”).
- Test zakresu możliwy tylko od 15 °C (w 10–15 °C wizytę odniesienia ma 18 obserwacji, <10 °C żadna; próg: ≥2 wizyty odniesienia w grupie i ≥20 obserwacji w paśmie) — **w 5–15 °C ważność wynika z dopasowania i trendu resztkowego, nie z testu pasmowego**.
- Postać liniowa powyżej 25 °C: błąd rośnie szybciej niż wykładniczej (D0 25–30 °C: −1,1 %, 30–35 °C: −3,8 % dla stałych k z Tab. 7.1; −2,10 % przy k dopasowanym na 5–25 °C = 0,0175).
- Wariant B w 25–30 °C: D0 w ±3 %, D300 w ±2 %, **SCI300 zaniżony średnio ok. 7 %** (należy zaznaczyć w wynikach; „interpretować z tym zastrzeżeniem”). Ugięć dalszych niż 900 mm powyżej 25 °C nie badano. 30–35 °C: D0 −2,14 % nierozstrzygnięte; >35 °C błąd D0 −8…−9 %.
- Współczynniki D900–D1800 „mają charakter orientacyjny” (na Podkowie k≈0, przedziały obejmują 0).
- Współczynniki wyznaczone na pakietach 24–25 cm (TN 25 cm AC z PMB; Podkowa 24 cm AC), obie stacje łącznie, jeden rok danych (VIII 2025–VIII 2026). Zależność β(h) ≈ 0,38 + 0,049·h [%/°C], h w cm (15–30 cm: ok. 1,1–1,9 %/°C; błąd walidacji LOO 0,37 %/°C) jest **orientacyjna, nie wzór normatywny** (R7.1 p.1).
- Jedno k/β na cały rok; bez współczynników sezonowych (R5.7, R7.1 p.4).
- T_mid: z chwili pomiaru; jakość otworów sondy (błąd 1 otworu → błąd korekty ~5 %; Podkowa sonda 12 cm zawyża średnio +2,55 °C, RMSE 4,35 °C; odczyt 12 cm > 4 cm w 86 % pomiarów); zalecane dwie głębokości (4 cm i połowa pakietu) — poprawa CV D300–D900 o 14–24 % tylko dla czujników stacji (D300 −14 % [−32; −6], D600 −24 % [−39; −16], D900 −18 % [−29; −7], BCI −24 % [−29; −5]; D0, SCI300, BDI bez poprawy), dla sondy wynik niespójny (R5.8, C69). Formuły dwutemperaturowej korekty brak w raporcie.
- Flagi źródła temperatury (R3.5, R3.9): świeży wpis operatora / wartość przeniesiona / pomiar serii / sonda 4, 8, 12 cm / czujnik stacji / model; w FWD sieciowych świeża tylko ok. 1 % stacji, 38 % starsza niż 1 h, skrajnie 7,4 h przy ΔT_pow 4 °C; mediana 1 zmiana wartości na sesję (3 h); ≥1/4 sesji ma jedną wartość.
- Temperatura z modelu (N2) „między wpisami temperatury w pomiarach FWD”: błąd 1,75 °C/12 cm, mediana błędu korekty D0 ok. 2 % (R7.1 p.2, R4.10); w nocy kalibracja nie działa.

### 2.4 Tab. 7.1 — współczynniki korekty temperaturowej (przepisana w całości; R7.1, L1153–1166)
Tytuł: „Współczynniki korekty temperaturowej dla czujników czaszy (oba stanowiska łącznie, pakiety 24–25 cm, wizyty 5–30 °C)”.

| Wielkość | k [°C⁻¹] — wariant A | β [%/°C] — wariant B |
|---|---|---|
| D0 | 0,016 | 1,60 |
| D200 | 0,014 | 1,38 |
| D300 | 0,012 | 1,22 |
| D450 | 0,010 | 0,95 |
| D600 | 0,007 | 0,71 |
| D900 | 0,003 | 0,33 |
| D1200 | 0,002 | 0,22 |
| D1500 | 0,002 | 0,22 |
| D1800 | 0,003 | 0,27 |

Zakresy: A — T_mid 5–25 °C; B — T_mid 5–30 °C; <5 °C brak zastosowania. Kom. C88: scope = łącznie (k_guide, beta_pct) z `e2a3_final_k_profile.csv`.
**Pełna precyzja k (Tab. 5.1, „łącznie”):** D0 0,0161 | D200 0,0140 | D300 0,0123 | D450 0,0096 | D600 0,0070 | D900 0,0033 | D1200 0,0021 | D1500 0,0022 | D1800 0,0027. Kom. C87 (R4): D0 0,01611; D300 0,01234; D600 0,00703; D900 0,00329.
Zaokrąglenie Tab. 7.1: D450 0,0096→0,010 (+4 %), D900 0,00329→0,003 (−9 %), D300 0,01234→0,012 (−3 %), D1800 0,0027→0,003.

### 2.5 Tab. 5.1 — k wzdłuż czaszy, postać wzoru krajowego (T_mid z czujnika, punkt × miesiąc, wizyty 5–30 °C; n = 191 TN, 223 Podkowa, 414 łącznie)

| | D0 | D200 | D300 | D450 | D600 | D900 | D1200 | D1500 | D1800 |
|---|---|---|---|---|---|---|---|---|---|
| TN | 0,0152 | 0,0141 | 0,0132 | 0,0114 | 0,0093 | 0,0060 | 0,0046 | 0,0044 | 0,0046 |
| Podkowa | 0,0170 | 0,0139 | 0,0115 | 0,0078 | 0,0048 | 0,0006 | −0,0003 | −0,0001 | 0,0007 |
| łącznie | 0,0161 | 0,0140 | 0,0123 | 0,0096 | 0,0070 | 0,0033 | 0,0021 | 0,0022 | 0,0027 |

R5.2: D0 k = 0,0152 [0,0137; 0,0166] (TN), 0,0170 [0,0154; 0,0191] (Podkowa), **0,0161 [0,0153; 0,0173] łącznie, β = 1,60 %/°C**; Tab. 3.3: β D0 1,60 [1,51; 1,73], odpowiednik liniowy 1,58 (dziki bootstrap [1,46; 1,69], CR2 [1,46; 1,69], klaster tygodniowy [1,43; 1,72]). Wcześniejsza rozbieżność 0,0107 vs 0,0163 (dopasowanie na wszystkich T) wynikała z wizyt >30 °C na TN. Po korekcie k=0,02 trend resztkowy −0,69 µm/°C; CV skorygowanych D0: 0,030 (k=0,02) vs 0,026 (wyznaczony).

### 2.6 Wartości referencyjne dla testów N1 (zestawienie; Tab. = numer w raporcie)
Testy jednostkowe funkcji (obl. własne ze współczynników Tab. 7.1; NIE z raportu): D0=200 µm: T=5 → A 248,000 / B 254,250; T=10 → A 232,000 / B 234,702; T=25 → A 184,000 / B 184,623; T=30 → A 168,000 / B 170,429. D300=150 µm: T=10 → A 168,000 / B 169,463; T=30 → A 132,000 / B 132,772. SCI300₂₀ (D0=200, D300=150, T=10): A 64,000; B 65,239. T=20 → tożsamość.
Wartości z raportu (do testów akceptacyjnych/regresyjnych na danych stacji TN/Podkowa):
- **Tab. 7.1, Tab. 5.1** — współczynniki jw.
- **Tab. 5.2** — błąd korekty (postać wykładnicza, współczynniki dopasowane na 5–25 °C, 90 %), werdykt dla δ = 1,37/2/3/5 % (R równoważne, N nierozstrzygnięte, X różne):
  TN D0 25–30: −0,80 [−2,36; +0,60] N/N/R/R | oba D0 25–30: −0,53 [−2,37; +0,99] N/N/R/R | oba D0 30–35: −2,14 [−6,11; +0,95] N/N/N/N | mikroodcinki D0 25–30: +1,63 [−2,88; +6,00] N/N/N/N | D200 25–30: +0,30 [−1,25; +1,48] N/R/R/R | D300 25–30: +0,56 [−0,96; +1,57] N/R/R/R | D300 30–35: +0,37 [−1,93; +2,01] N/N/R/R | D600 25–30: +0,74 [−0,55; +1,69] N/R/R/R | D900 25–30: +0,90 [−0,31; +1,80] N/R/R/R | SCI300 (z ugięć) 25–30: −6,77 [−14,28; −0,21] N/N/N/N | SCI300 30–35: −17,79 [−44,82; +1,76] N/N/N/N | BDI(D300₂₀−D600₂₀) 25–30: −0,31 [−3,25; +2,17] N/N/N/R | BCI(D600₂₀−D900₂₀) 25–30: +0,14 [−2,50; +1,84] N/N/R/R | D0 postać liniowa (k z 5–25 °C) 25–30: −2,10 [−4,27; −0,29] N/N/N/R | D300 liniowa 25–30: −0,30 [−2,05; +0,82] N/N/R/R | SCI300 liniowa 25–30: −11,98 [−21,44; −3,92] X/X/X/X. (kom. C55: 30–35 °C: D200 −0,58 [−3,12; +1,20], D600 +0,45 [−2,00; +2,39], D900 +0,95 [−1,44; +2,76]).
- **R7.1 wariant A (kom. C87, R4: stałe k_guide D0 0,01611; D300 0,01234; D600 0,00703; D900 0,00329; ref 15–25 °C; 90 %):** D0 15–20 −0,22 [−0,49; +0,09]; 20–25 +0,22 [−0,10; +0,49]; 25–30 −1,06 [−2,07; −0,05]; 30–35 −3,76 [−6,83; −1,20]; D300 15–20/20–25 ±0,09; SCI300 z ugięć 15–20 −0,68 [−1,62; +0,40], 20–25 +0,67 [−0,42; +1,48], 25–30 −6,02 [−12,26; −0,37]. Wniosek tekstowy: równoważność w ±1,37 % (D0, D300) i ±2 % (SCI300) w pasmach 15–20 i 20–25 °C.
- **R7.1 wariant B (kom. C87, R3a stałe β):** D0 25–30 −0,31 [−1,39; +0,63], 30–35 −1,77 [−4,74; +0,76]; SCI300 25–30 (R3a_z_ugiec) −4,13 [−10,30; +1,42]. Tekst: D0 ±3 %, D300 ±2 %, SCI300 ≈ −7 %.
- **Obecny wzór k=0,02 na każdym czujniku (R5.4, kom. C57, 90 %):** D0 15–20 +0,44 [0,09; 0,76]; 20–25 −0,44 [−0,76; −0,08]; 25–30 −3,96 [−5,02; −2,87]; 30–35 −9,00 [−12,60; −6,11]; D300 +1,23 [0,61; 1,64] / −1,20 [−1,55; −0,63] / −5,83 [−6,85; −4,83] / −11,39 [−12,60; −9,92]; D900 +2,99 [1,91; 3,64] / −2,94 [−3,51; −1,91] / −11,18 [−12,35; −9,73] / −20,17 [−22,15; −18,01]; k=0,01 (R2) D0 25–30 +3,28 [2,20; 4,17]. SCI300 z k=0,02 (95 %, C59): 15–20 −2,69 [−3,99; −1,12]; 20–25 +2,64 [1,08; 3,67]; BDI 15–20 −1,99 [−2,77; −1,09]; 20–25 +1,95 [1,13; 2,60]; SCI300 25–30 +3,01 [−2,08; +7,92] (90 %); trend resztkowy +0,43 µm/°C. Pasmo 10–15 (C58, n=18, 6 dni; R1 k=0,02): D0 +3,23 [0,96; 4,28], D300 +5,55 [2,30; 6,74], D900 +9,61 [5,67; 11,34], SCI300 −6,71 [−9,63; −2,88]; exp β dopasowane 5–25: D0 +1,81 [−0,20; 2,91], D300 +1,63 [−0,76; 2,69], D900 +0,66 [−1,35; 1,72].
- **CV ugięć skorygowanych (R5.3, kom. C52; punkt × miesiąc):** średnia 9 czujników: k=0,02 → 0,0423, trend −1,089 µm/°C; β_D0 dla każdego czujnika → 0,0331, −0,679; własne → 0,0191, −0,002; D900–D1800: 0,049–0,053 vs 0,015–0,019; SCI300: 0,0939 (k=0,02) vs 0,0756 (własne), trend +0,430 vs +0,0068. Mnożnik 1,7–2,2.
- **Powtarzalność (R5.4, kom. C85):** D0 σ=1,37 % (TN), 4,6 % (Podkowa); SCI300 2,39 % (TN), 14,6 % (Podkowa) [e2a3_repeatability_v3: 1,369/4,633; 2,389/14,61].
- Mechanizm SCI300: e_SCI ≈ A·e_D0 − (A−1)·e_D300, A=D0/SCI300 ≈ 5 (mediana 4,86; TN 4,97; Podkowa 4,22; n=49; średnia e −6,77; rozkład per obserwacja −7,08, R²=0,99). ln(D300/D0): 5–25 °C −0,46 [−0,58; −0,35] %/°C; ≥25 °C +0,10 [−0,03; +0,32]. SCI300 przy stałych k wariantu A w 25–30 °C: TN −8,6 % (n=37, [−15,5; −2,1]), Podkowa +2,1 % (n=12, [−5,0; +8,8]).
- **Okno pomiarowe (R5.4):** udział godzin 8–16 (IV–X) z T_mid w zakresie: 64 % (≤25 °C) → 83 % (≤30 °C); VI–VIII 31–39 % → 62–70 %.
- Błąd korekty D0 od błędu T: δD/D ≈ β·ΔT (R4.9): hybryda B 1,9 %/1,1 %; fizyka 2,4 %/1,8 %; BELLS3 6,2 %/3,2 % (TN/Podkowa).
- Sezonowość (Tab. 5.3, informacyjnie): D0,III/D0,m: III 1,00; IV 1,11; V 1,11; VI 1,14; VII 1,11; VIII 1,12; IX 1,12; X 1,07; XI 1,05; XII 1,10; f_s wytyczne: 1,00; 1,04; 1,08; 1,12; 1,15; 1,17; 1,20; 1,22; 1,25; 1,28; f_s z pracy źródłowej [24]: 1,00; 1,00; 1,15; 1,15; 1,15; 1,15; 1,15; 1,25; 1,25; 1,25. CV poza próbą D0: 0,0253 (jedno β), 0,0266 (sezonowo), 0,0303 (miesięcznie).
- Plan D vs S: Podkowa β D0 2,6 vs 1,5 %/°C (plan S właściwy dla korekty rutynowej).
- Reakcja czasowa: cząstkowe R² 0,55–0,87 dla bieżącej lub ≤1–2 h opóźnionej T.

---------------------------------------------------------------------
## 3. SPECYFIKACJA FUNKCJONALNA — N2 `layer_temp` (temperatura warstwy asfaltowej; R4, R4.10, R7.1 p.2, R7.3 p.2)

### 3.1 Cel, wejścia, wyjścia (R4.1, R7.4)
Wejście: odczyt pirometru (temperatura powierzchni IR), czas, położenie, dane meteorologiczne (reanaliza; pobierane po pomiarze). Wyjście: temperatura na zadanej głębokości (standard sieci 12 cm; T_mid = połowa pakietu) z oceną niepewności. Przeznaczenie: korekta TSD i FWD bez wiercenia otworów. Dwa profile: pomiarowy (survey: chwilowy pirometr + T powietrza + reanaliza; właściwy cel) i stacjonarny (dodatkowo ciągła seria lokalna IR; porównawczo).

### 3.2 Model fizyczny (R4.3)
- Równanie przewodnictwa (postać zachowawcza): ∂T/∂t = ∂/∂z [α(z)·∂T/∂z]; siatka 10 mm; schemat niejawny; krok danych 10 min; w modelu podstawowym jedna efektywna dyfuzyjność α dla całego profilu. Weryfikacja FEM: max różnica 0,007 °C (próg akceptacji 0,05 °C).
- α kalibrowane przy zmierzonych T na 20 mm (górny WB) i 500 mm (dolny WB): **α_TN = 1,118·10⁻⁶ m²/s; α_Podkowa = 8,72·10⁻⁷ m²/s**; RMSE w obszarze 20–500 mm: 0,36 °C (TN) i 0,25 °C (Podkowa), obciążenie pomijalne. Wydłużenie zapisu o 6 tygodni zmieniło α o <0,3 %.
- Górny WB w trybie operacyjnym — bilans energii na powierzchni: pochłonięte promieniowanie krótkofalowe (współczynnik zbiorczy a_SW); długofalowe nieba z udziałem widoczności nieba (svf); konwekcja h = h₀ + h₁·u (u — prędkość wiatru); strumień przewodzony w głąb. Parametry a_SW, svf, h₀, h₁ i pojemność cieplna kalibrowane w części uczącej każdego podziału; to parametry efektywne, nie fizyczne. (Wartości liczbowe — brak w raporcie.)
- Dolny WB (500 mm) — model liniowy z harmonicznymi dnia roku oraz 7- i 30-dobowymi średnimi T powietrza z reanalizy; RMSE 0,8–1,4 °C na 500 mm; wpływ na T_mid +0,03…+0,09 °C. Błąd dolnego WB przenosi się na połowę pakietu w 28–48 % (3 °C → ok. 1,2 °C).
- Korekta odczytu IR: w profilu stacjonarnym różnica T_20mm − IR modelowana regresją na zmiennych meteorologicznych (wariant globalny i sezonowy). Obserwacje: IR niższy od T_20mm średnio o 2,6 °C (TN) i 1,4 °C (Podkowa); max ok. 13 °C (IR −25,8 vs −12,6 °C na 20 mm); największa różnica przy bezchmurnym niebie w nocy. IR jako warunek Dirichleta daje obciążenie −1,77 °C (TN) i −0,99 °C (Podkowa) w średniej rocznej dla 20–280 mm.
- Dane meteo (R4.2): ERA5 i ERA5-Land [17][18] przez Open-Meteo w konfiguracji domyślnej (pobranie sierpień 2026), godzinowe dla najbliższego węzła siatki: T powietrza, punkt rosy, wilgotność; ciśnienie, zachmurzenie, wiatr; promieniowanie krótkofalowe całkowite, bezpośrednie i rozproszone; opad i pokrywa śnieżna. **Pobierać w UTC i przeliczać na czas lokalny z czasem letnim** (interfejs przy podaniu strefy nadaje wszystkim godzinom przesunięcie obowiązujące w dniu pobrania; pierwsza wersja miała zimowe etykiety przesunięte o 1 h).
- Wielkość prognozowana: T_mid — TN interpolacja liniowa między czujnikami 120 i 180 mm do 125 mm; Podkowa czujnik 120 mm. Stanowiska: czujniki Pt100 kl. A na 2, 4, 8, 12, 18, 24(TN)/23(Podkowa), 28, 50 cm; IR Qulon-RTS; rejestracja co 10 min, od 2025-08-20.

### 3.3 Modele porównywane (R4.5)
1. BELLS3 oryginalny [19] (Lukanen, Stubstad, Briggs, FHWA-RD-98-085) i BELLS3_O [20] (parametry krajowe; „nic nie wnosi” — odniesieniem jest BELLS3). Regresja na odczycie pirometru, bez lokalnej rekalibracji.
2. ML bez fizyki (XGBoost, wejścia operacyjne; stała konfiguracja, bez strojenia hiperparametrów — wartości nie podano).
3. Fizyka operacyjna (przewodnictwo + bilans energii + modelowany dolny WB).
4. Hybryda A (prognoza fizyki jako cecha dla ML na T_mid).
5. Hybryda B (uczenie rezydualne: T_mid − T_fiz; prognoza = fizyka + poprawka). Najważniejsza cecha — kotwica pirometryczna (różnica odczytu pirometru i T powierzchni z modelu fizycznego); udział 28,5 % (TN) i 27,6 % (Podkowa) zysku (wartości sprzed poprawki czasu).
6. **Fizyka z kalibracją jednorazową (model operacyjny sieci; R4.10):** fizyka operacyjna, w której jeden parametr — efektywna absorpcja a_SW — dobiera się w chwili pomiaru tak, aby T powierzchni z modelu odpowiadała odczytowi pirometru aparatu (po korekcie IR → masa, R4.4); bez użycia sondy. Wersja stanowiska nasłonecznionego (TN). **Wniosek R4.10/R7.3: do wyznaczania T warstwy na sieci przyjęto ten model.** Hybryda B na sieci nie poprawia fizyki (poprawka z TN się nie przenosi).
- Skuteczność kalibracji jednorazowej (R6.3): skuteczna w 37 % pomiarów FWD i 55 % TSD; w pozostałych model działa z wartością domyślną parametru (jak fizyka bez kalibracji): nocne pomiary FWD (20 %), parametr na górnej granicy zakresu (43 % FWD, 45 % TSD).
- Czułość na ekspozycję: zamiana a_SW/svf między stanowiskami +2,4–2,7 °C błędu; zamiana α <0,02 °C; test bez informacji ze stanowiska: fizyka 4,96/4,87 °C, hybryda 4,60/4,03 °C; Podkowa chłodniejsza o 4,49 °C (20 mm) i 3,12 °C (500 mm). Model = „moduł kalibrowany stanowiskowo”. Grubość pakietu 80–320 mm nie zmienia prognozy operacyjnej (R4.8). Mierzone głębokości 20–240 mm odpowiadają połowie pakietów 40–480 mm; zysk z poprawki z 60 % przy powierzchni do 11 %/0 % na 230–240 mm.
- Protokół walidacji (R4.6): podziały blokowe (miesiące, sezony, stanowiska), bufor 2 dób, rekalibracja wszystkich elementów w podziale (α raz na stanowisko), okno oceny IV–X, wspólne wsparcie czasowe n = 26 490 (TN) / 28 348 (Podkowa), bootstrap z jednostką = podział walidacyjny.

### 3.4 Ograniczenia/zastrzeżenia (R4.10, R8, R7.3 p.2)
- Noc (0–6, 18–24): kalibracja nieskuteczna (pirometr bez informacji o promieniowaniu słonecznym), fizyka zawyża T (wieczorem +1,5 °C); BELLS3 nie jest w nocy gorszy; mikroodcinki (noc): BELLS3 2,01 [1,40; 2,54] vs fizyka z kal. 2,61 [2,04; 3,11] — różnica nieistotna. R7.3: „Pomiary nocne wymagają innego sposobu wyznaczenia temperatury (rozdz. 8)”; R8: opis ekspozycji i głębokiego poziomu termicznego — zadanie otwarte.
- Miejsca zacienione: 3,65 °C (Podkowa, model TN); „ekspozycja miejsca głównym źródłem błędu”; ~3/4 wariancji błędu to stała różnica między sesjami.
- Pirometr aparatu FWD vs stanowiska: średnio +1,9 °C, rozrzut ok. 4 °C; liniowa korekta przyrządu nie pomogła. Pirometr TSD nie sprawdzany względem T zmierzonej (R6.3, R8).
- Sonda 12 cm na Podkowie odpowiada ok. 2 cm (cel: czujnik wbudowany). Głębokość sondy często niezapisana — propozycja zapisu w polu komentarza pliku.
- Kryterium przyjęte ex ante (R4.10): RMSE ≤ 1,5 °C — łańcuch zamknięty; ≥ 3,0 °C — granice stosowalności; pośrednie — częściowy. Wynik 1,75 °C = częściowy (przed południem 1,38 °C spełnia). Dolna granica osiągalna (sonda vs czujnik wbudowany na 12 cm na TN): RMSE 1,1 °C, obciążenie −0,15 °C.
- Błąd w zależności od pory dnia (fizyka z kalibracją): 6–12 h **1,38**; 12–18 h 1,89; 0–6 i 18–24 h 2,17 (obciążenie wieczorem +1,5); między latami 1,2–2,3 °C.

### 3.5 Tab. 4.3 — Błąd temperatury na 12 cm, archiwum FWD 2020–2026, kwiecień–październik (549 obserwacji, 226 sesji; 95 % — bootstrap z losowaniem sesji) (przepisana w całości; L631–638)

| Model | RMSE [°C] | MAE [°C] | Mediana |błędu| [°C] | P90 |błędu| [°C] | Obciążenie [°C] | Udział wariancji błędu między sesjami |
|---|---|---|---|---|---|---|
| hybryda B | 2,12 [1,93; 2,30] | 1,71 | 1,45 [1,29; 1,63] | 3,48 [3,16; 3,76] | +1,03 | 76 % |
| fizyka operacyjna | 2,09 [1,92; 2,25] | 1,70 | 1,44 [1,30; 1,63] | 3,26 [2,96; 3,86] | +0,95 | 79 % |
| **fizyka z kalibracją jednorazową** | **1,75 [1,62; 1,87]** | **1,40** | **1,22 [1,11; 1,34]** | **2,82 [2,59; 2,99]** | **+0,27** | 73 % |
| BELLS3 | 2,41 [2,15; 2,69] | 1,82 | 1,37 [1,17; 1,55] | 3,87 [3,55; 4,47] | −0,34 | 86 % |

Zbiór: wpisy operatora w chwili wpisu (pierwszy wpis w sesji lub zmiana wartości), bez przeniesionych; IV–X; wyłączono 1 wpis (1,0 °C wśród 15–16 °C, pomyłka potwierdzona w pliku źródłowym). Inne zbiory R4.10: odcinki 1 km (2022) 11 obs. (9 z jedną głębokością): BELLS3 1,46; fizyka z kal. 2,25; hybryda 2,54 °C; mikroodcinki (noc, 120 grup, 8 odcinków × 15 nocy, sonda 10 cm): BELLS3 2,01 [1,40; 2,54]; fizyka z kal. 2,61 [2,04; 3,11]; hybryda 3,08.
Znaczenie dla korekty D0 (β=1,6 %/°C, wykładnicza): fizyka z kal.: mediana błędu korekty D0 1,95 %, P90 4,5 %, w ±3 % 72 %, w ±1,37 % 35 %; hybryda B 2,3 %/5,7 %/64 %/28 %; BELLS3 2,2 %/6,1 %/64 %/32 %.

### 3.6 Pozostałe tabele N2 (referencyjne)
**Tab. 4.1** RMSE T_mid [°C], IV–X, wyłączane miesiące (TN / Podkowa): pomiarowy: BELLS3 3,86 / 2,00; BELLS3_O 3,75 [2,87; 4,49] / 1,57 [1,45; 1,66]; ML 2,51 / 1,83; fizyka 1,48 [1,36; 1,60] / 1,12 [1,03; 1,21]; hybryda A 1,39 / 0,87; **hybryda B 1,22 [1,05; 1,34] / 0,72 [0,60; 0,84]**; stacjonarny: przewodnictwo + korekta IR 0,96 [0,79; 1,13] / 0,55 [0,48; 0,62]; hybryda B 0,65 [0,55; 0,74] / 0,41 [0,33; 0,48].
**Tab. 4.2** (TN | Podkowa; RMSE, MAE, obciążenie, mediana |e|, P90 |e|): pomiarowy fizyka 1,48/1,17/+0,08/0,97/2,39 | 1,12/0,88/+0,25/0,74/1,76; hybryda A 1,39/1,09/+0,15/0,89/2,20 | 0,87/0,67/+0,09/0,55/1,37; hybryda B 1,22/0,94/−0,07/0,75/1,96 | 0,72/0,56/+0,01/0,47/1,17; stacjonarny przewodnictwo+IR 0,96/0,78/−0,28/0,69/1,54 | 0,55/0,45/+0,01/0,39/0,89; hybryda A 0,90/0,72/+0,12/0,62/1,41 | 0,56/0,40/+0,04/0,31/0,82; hybryda B 0,65/0,52/+0,03/0,45/1,07 | 0,41/0,31/−0,05/0,25/0,66.
**Tab. 4.4** (n; RMSE [95 %]; MAE; mediana; P90): LAMB 4 cm: fizyka z kal. 254; 2,48 [2,09; 2,86]; 1,82; 1,22; 4,18 | hybryda B 4,88 [4,13; 5,54]; 3,77; 2,80; 8,95 | BELLS3 2,54 [2,23; 2,82]; 2,11; 1,86; 3,92. Podkowa 12 cm, model TN (187): fizyka z kal. 3,65 [3,25; 4,03]; 2,96; 2,38; 6,06 | hybryda B 5,73 [5,09; 6,26]; 5,03; 4,36; 9,73 | BELLS3 4,03 [3,38; 4,56]; 2,71; 1,48; 8,02. TN 12 cm, model na którym uczono (324): fizyka z kal. 2,69 [2,35; 3,00]; 1,92; 1,37; 4,26 | **hybryda B 1,84 [1,58; 2,12]; 1,37; 1,00; 2,96** | BELLS3 2,64 [2,32; 2,93]; 1,98; 1,51; 4,58. Podkowa 12 cm, model Podkowa (187): fizyka z kal. 2,88 [2,48; 3,22]; 2,04; 1,39; 4,96 | **hybryda B 0,82 [0,72; 0,92]; 0,66; 0,58; 1,32** | BELLS3 4,03; 2,71; 1,48; 8,02.
Inne liczby: hybryda B vs fizyka: −0,27 [−0,43; −0,10] (TN), −0,40 [−0,49; −0,34] (Podkowa); w podziałach miesięcznych lepsza w 21 z 22 przypadków; lato VI–VIII 1,23 vs 1,60 (TN), 0,74 vs 1,10 (Pod); dzień 6–18: 1,28 vs 1,60 / 0,73 vs 1,18; wieczór 18–24: 1,28 vs 1,52 / 0,76 vs 1,15; noc 0–6: 0,99 vs 1,18 / 0,64 vs 0,92. Ekstrapolacja sezonowa: ML 2,51/1,83 → 3,47/2,64; hybryda A 1,39/0,87 → 2,01/1,62; fizyka 1,48/1,12 → 1,58/1,14; hybryda B 1,22/0,72 → 1,33/0,83. ML + 3 h historii: 1,90/1,37 vs fizyka 0,96/0,55 (stacjonarny). BELLS3: TN RMSE 3,861, bias −2,871; Podkowa 2,000/−0,415 (kom. C39). Powtarzalność/test DM p<0,0001 (TN profil stacjonarny graniczny p=0,05; kom. C34).

---------------------------------------------------------------------
## 4. SPECYFIKACJA FUNKCJONALNA — N3 `tsd_network` (przetwarzanie TSD na sieci + eksport XML; R7.3, R3.9, R3.10, R6.3)

### 4.1 Kroki wg R7.3 (7 punktów) z doprecyzowaniem z rozdziałów tłowych
**p.1 Ugięcia i krzywizna.** d0 TSD przeliczone **jednym zestawem współczynników kalibracyjnych przedziału kalibracji, bez czujnika 1,51 m** (R3.10). Przedział kalibracji = atrybut przejazdu, odtworzony z dziennika kalibracji (zdarzenia kalibracyjne zmieniały zestaw współczynników w serii wieloletniej). Przeliczenie dotyczy przejazdów 2024–2026 (R3.4 krok 7), poprawność sprawdzona przez zrównanie z eksportem oryginalnym na odcinkach 1 km (2022, 28 przejazdów). Uzasadnienie: d0 z eksportu producenta prawie nie reagował na temperaturę (wpływ czujnika 1,51 m w nieliniowym modelu czaszy + zmiana współczynników + przypisanie kanałów). Eksport nominalny (z 1,51 m) daje d0 średnio ok. 26 % większe (mediana 200,5 vs 131,9 µm; iloraz mediana 1,258, n 1241). Eksport producenta podaje D-450…D1500 (dopasowanie funkcji czaszy do nachyleń; D900/D1500 odtwarzane z błędem od −78 do +197 % zależnie od funkcji) — **D300…D1500 z eksportu NIE używać**.
 - Kanały nachyleń (9): za kołem −0,45, −0,30, −0,20 m; przed kołem 0,11; 0,21; 0,31; 0,46; 0,61; 0,91 m (1,51 pominięty). Krok TSD 1 m.
 - **Całki nachyleń**: różnica ugięć między osią koła a odległością x = całka nachylenia od 0 do x. Odpowiedniki: **SCI300_TSD = ∫₀^0,31 m, BDI_TSD = ∫0,31–0,61 m, BCI_TSD = ∫0,61–0,91 m** (granice = położenie czujników TSD, nie geofonów FWD). Warianty: **P0 (główny)** — nachylenia 9 czujników interpolowane monotoniczną funkcją sklejaną 3. stopnia (PCHIP), całka numerycznie na siatce 1 mm od osi koła; **T** — trapezy na czujnikach przed kołem, z założeniem zerowego nachylenia w osi koła (slope(0)=0); **PX** — jak P0, ale całkowanie od maksimum czaszy, gdzie interpolowane nachylenie = 0 (średnio 34 mm za osią koła; przesuwa się ok. 1 mm/°C [0,28; 1,89], 7/8 odcinków). Sieć: całka w każdym rekordzie, potem mediana całek w oknie; mikroodcinki: całka z median nachyleń w oknie punktu. Wariant T stosowano w kontrolach kanał-po-kanale.
 - Porównanie na mikroodcinkach (1308 kombinacji punkt × noc, 8 odcinków; kom. C31): mediana D0−D300 z eksportu 52,3 µm; P0 39,5; T 35,7; PX 44,0; SCI300 FWD 50,2 µm. Iloraz eksport/P0 1,25 (IQR 1,04–1,80); T/P0 0,904; PX/P0 1,033; FWD/P0 1,131; niedodatnie: eksport 0 %, P0 4,2 % (55/1308), T 2,7 % (35/1308), PX 0,6 % (8/1244). Korelacje log: eksport–P0 0,83; P0–FWD 0,79; eksport–FWD 0,82. Wrażliwość temperaturowa (quasi-Poisson, efekt punktu, wszystkie T): SCI300 FWD 3,69 %/°C; P0 2,84; PX 2,67; T 2,62; eksport 2,20; różnica wrażliwości TSD−FWD [95 %]: P0 [−1,46; +0,06] (jedyna obejmująca 0), eksport [−1,83; −0,93].
**p.2 Temperatura warstwy.** Model N2 (fizyka z kalibracją jednorazową do pirometru w chwili przejazdu); błąd 1,75 °C/12 cm (przed południem ok. 1,4 °C). **Odczytu pirometru nie stosować jako T warstwy; normalizacji temperaturą powierzchni — wcale** (R3.9: sprawdzona i wycofana — „wynik bez sensu fizycznego”). Noc — inny sposób (R8).
**p.3 Korekta.** d0 w postaci wykładniczej, β = 1,60 %/°C, zakres T warstwy 5–30 °C; wyniki spoza zakresu **oznaczać**. W R6.3: d0_TSD,20 = d0_TSD · exp[0,016·(20 − T12_TSD)]; T12 = T warstwy na 12 cm w chwili przejazdu (modelem); ta sama β co D0 FWD (R6.1). Granice przenoszenia korekty FWD na d0 TSD (R6.1, R7.2 p.4): błąd do ok. ±5 % przy sprowadzaniu z 20–30 °C i do ok. ±10 % z 5–20 °C (metody odporne; metodą główną ±3 % i ±5 %). **Nachyleń/całek TSD nie korygować współczynnikami FWD bez weryfikacji** (R6.1; R7.2 p.4).
**p.4 Odszumianie i agregacja.** Odrzucenie odstających d0 **filtrem Hampela z odrzutem całej czaszy** (cały rekord), potem **mediana lub średnia z okna ±5–10 m**; ocena na poziomie odcinka diagnostycznego (50–100 m) lub całego przebiegu, nie pojedynczego metra. Parametry filtra Hampela (okno, próg) — **nie podane w raporcie** (tylko „Hampel na D0 + średnia ±10 m” w kom. C90). W R3.8: korelacja w obrębie sesji 0,28 (rekord najbliższy), 0,40 (mediana ±5 m), 0,51 (±10 m, także po filtrze odstających i średniej kroczącej ±10 m).
**p.5 Jakość.** Udział czasz o GoF ≥ 0,5 w oknie; kontrola spójności GPS z żyroskopem i drogomierzem (kurs z żyroskopu vs kurs z kolejnych pozycji GPS; rekonstrukcja położenia z drogomierza zakotwiczonego w poprawnym fragmencie); wykryte i skorygowane przesunięcie przypisania kanałów TSD; doba pomiarowa dla serii nocnych (zamiast daty kalendarzowej); **rejestr oznaczeń zamiast usuwania rekordów** (każda analiza deklaruje, co wyklucza). GoF (R6.2): przy progu eksportu GoF 0,01 ok. 56 % ugięć w bazie pochodzi z czasz GoF<0,5; pilotaż A2: iloraz FWD/TSD 1,75 (wszystkie pary) vs 0,89 (GoF≥0,5).
**p.6 Przeliczenie na skalę FWD.** **D0_FWD,20 = 1,62 · d0_TSD,20, przedział 95 % [1,54; 1,68]** (mediana ilorazu po korekcie; 5511 par, 36 sesji), dla wartości odcinkowych (≥100 m), z weryfikacją dla danego aparatu FWD i okresu kalibracji TSD na odcinkach kontrolnych mierzonych obydwoma urządzeniami tego samego dnia. Funkcję przeliczającą kalibrować na parach geometrycznych i oceniać poza próbą (z pominięciem sesji). Mnożnik, nie prosta afiniczna: nachylenie Deminga log–log 0,96 [0,90; 1,06] obejmuje 1.
 - **Orientacyjny przelicznik krzywizny (R6.3, R7.1 p.3, R8):** SCI300_FWD,20 ≈ 2,2·SCI300_TSD,20 (mediana 2,24 [1,99; 2,53]; poziom pary; 100 m: 2,29 [1,59; 5,50]; przebieg: 2,75 [2,27; 2,97]); postać potęgowa z Deminga: SCI300_FWD,20 = 7,1·SCI300_TSD,20^0,57 [µm] (wyraz wolny log-log 1,96 [1,80; 2,20]; nachylenie 0,57 [0,45; 0,63]; exp(1,96)=7,1); w ok. 37 % par odpowiednik TSD niedodatni (przelicznik niestosowalny); błąd pojedynczego punktu >1,7× w co drugim przypadku (odchylenie odporne ln ilorazu 0,80); tylko porównania odcinków. Mikroodcinki (ta sama noc): 1,28 (IQR 0,95–1,76), BDI 1,46, BCI 1,39, d0 1,54; niedodatnie 10/5/9 %. FWD strona: wskaźniki z ugięć skorygowanych własnymi współczynnikami (Tab. 5.1) — przy braku współczynników wskaźników w Tab. 7.1; strona TSD w R6.3 skorygowana „współczynnikiem odpowiedniego wskaźnika FWD” (patrz niejasności).
**p.7 Produkt XML dla bazy danych drogowych.** Obecna procedura (`C:\WORK\DOKTORAT\tsd_2_xml`; README_workflow.md, tsd_pipeline.py, calibrate_conversion.py, compare_tsd_fwd.py; stan 2026-07-01): czasza **„D Tkor” z pliku 1 m = ugięcia eksportu sprowadzone do 20 °C temperaturą z modelu BELLS3_BT i k = 0,02**; Hampel na D0 + średnia ±10 m; **konwersja afiniczna**: DK50: a = 0,849, b = +24,35; S8: a = 0,473, b = +41,72 (zapewne D_FWD = a·D_TSD + b, µm — brak definicji w raporcie); dopasowanie „value ±5 m” w compare_tsd_fwd.py (kalibracja na parach dobieranych w oknie wg wartości FWD — wybór kandydata na podstawie ugięć FWD, czego R3.8/R7.2 zakazują). Zalecenie raportu: **zastąpić wejście danymi z p.1–3 (d0 bez 1,51 m, T z modelu N2, korekta wykładnicza β=1,60), a funkcję konwersji kalibrować na parach geometrycznych z oceną poza próbą**; „sama kalibracja afiniczna jest stabilna” (R6.2: mnożnik z pominięciem sesji MAE 27,7 µm = w próbie; afiniczna C_X MAE 22,89 w próbie / 23,71 poza próbą; mnożnik W5 k02: 27,68/27,74 µm). (obl. własne: konwersja DK50 dla D=100/150/200 µm → 109,2/151,7/194,1; S8 → 89,0/112,7/136,3 — czyli ok. 1,0× i 0,75× wejścia, zgodne ze stwierdzeniem R3.8, że wybór wg FWD daje „zgodność 1:1” jako artefakt, a nie z mnożnikiem 1,62.)

### 4.2 Referencyjne wartości dla testów N3 (wg tabel)
- **Tab. 6.3** (5511 par, 36 sesji; „przed” → „po” korekcie do 20 °C; 95 %): mediana ilorazu D0 FWD/d0 TSD 1,41 [1,32; 1,49] → **1,62 [1,54; 1,68]**; SD ln 0,343 [0,318; 0,368] → 0,321 [0,301; 0,341]; odchylenie odporne 1,4826·MAD 0,320 → 0,290; Pearson (log) 0,61 [0,44; 0,75] → 0,66 [0,51; 0,77]; Spearman 0,50 [0,40; 0,59] → 0,58 [0,48; 0,65]; Deming log–log 1,05 [0,95; 1,23] → 0,96 [0,90; 1,06]; wyraz wolny Deminga (liniowy) −5,7 [−29,2; 3,0] → +8,2 [−9,0; 14,1] µm; granice Blanda–Altmana dla ilorazu (95 %) 0,71–2,71 → 0,85–3,00 (obciążenie 1,60). CCC (kom. C78): 0,42 → 0,35.
- Różnica SD ln: −0,022 [−0,037; −0,006]; Wariancja ln ilorazu −12 %; rozstęp median grupowych (log) −0,21 [0,08; 0,34] (stosunek skrajnych 1,66 → 1,35; ln: 0,510 → 0,303); SD median grupowych −0,085 [0,042; 0,123].
- **Temperatury w parach (R6.3):** T12 mediana FWD 10,9 °C (zakres 4,2–24,1), TSD 21,8 °C (14,0–30,8); średnia różnica 8,9 °C → exp(0,016·8,86)=1,152 (obl. własne potwierdza 1,1523); mediana odstępu 75 dni; 5 % par tej samej doby; TSD tylko 8–18 h; 43 % FWD przed 5:00 lub po 21:00. Kontrola z wpisami operatora (33): RMSE 1,35 °C, obciążenie −0,10, mediana |e| 1,06, P90 2,12 (tylko opisowa).
- **Tab. 6.4** (aparat × rok TSD | pary | sesje | przed | po): HWD 8082-119/2024 | 1546 | 4 | 1,40 [1,36; 1,42] | 1,66 [1,63; 1,70]; HWD 8082-119/2026 | 703 | 5 | 0,98 [0,91; 1,04] | 1,31 [1,29; 1,32]; FWD 8002-367/2024 | 1087 | 9 | 1,48 [1,43; 1,60] | 1,58 [1,55; 1,65]; FWD 8002-367/2025 | 1805 | 15 | 1,53 [1,47; 1,59] | 1,77 [1,73; 1,82]; FWD 8002-369/2026 | 370 | 3 | 1,63 [1,39; 1,78] | 1,65 [1,43; 1,80]; wszystkie | 5511 | 36 | 1,41 [1,32; 1,49] | 1,62 [1,54; 1,68]. Rozstęp ok. 35 % (1,77/1,31). W dzikim bootstrapie: HWD 2026 1,30 [1,28; 1,32], FWD 8002-367/2025 1,73 [1,69; 1,77].
- **Tab. 6.5** (pary | mnożnik | Deming log–log): główny 5511 | 1,62 [1,54; 1,68] | 0,96 [0,90; 1,06]; BELLS3 po obu stronach 5511 | 1,64 [1,58; 1,71] | 0,97 [0,92; 1,08]; liniowy k=0,02 5511 | 1,65 [1,59; 1,72] | 0,95 [0,89; 1,04]; tylko skuteczna kalibracja jednorazowa 1733 | 1,56 [1,42; 1,73] | 0,91 [0,79; 1,03]; FWD T ze świeżego wpisu + TSD model 33 | 1,65 [1,21; 2,07] | 0,78 [0,53; 1,39].
- **Poziomy uśrednienia (Tab. 6.6; po korekcie; 95 %):** d0 para 5511 | 1,62 [1,54; 1,68] | SD ln 0,32 | Deming 0,96 [0,90; 1,06]; d0 100 m 395 | 1,69 [1,60; 1,75] | 0,22 | 0,93 [0,89; 1,14]; d0 przebieg 63 | 1,65 [1,60; 1,67] | 0,14 | 0,85 [0,72; 0,92]. SCI300 para 3468 | 2,24 [1,99; 2,53] | 1,03 | 0,57 [0,45; 0,63] | rozrzut wzgl. d0 3,2 [3,0; 3,4] | TSD≤0 37 %; SCI300 100 m 204 | 2,29 [1,59; 5,50] | 1,09 | 0,48 [0,32; 0,59] | 5,0 [4,1; 5,5] | 48 %; SCI300 przebieg 40 | 2,75 [2,27; 2,97] | 1,20 | 0,25 [0,08; 0,49] | 8,5 [4,8; 12,6] | 37 %. BDI para 3935 | 1,73 [1,54; 1,94] | 0,96 | 0,79 [0,68; 0,93] | 3,0 [2,7; 3,3] | 29 %; 100 m 239 | 1,88 [1,33; 2,37] | 0,94 | 0,66 [0,49; 0,77] | 4,4 [3,4; 5,3] | 39 %; przebieg 52 | 2,40 [1,93; 2,85] | 1,37 | 0,31 [0,16; 0,43] | 9,8 [6,1; 13,8] | 17 %. BCI para 3936 | 1,33 [1,27; 1,39] | 0,96 | 0,82 [0,73; 0,89] | 3,0 [2,8; 3,2] | 29 %; 100 m 216 | 1,68 [1,34; 2,71] | 0,91 | 0,65 [0,41; 0,77] | 4,2 [3,1; 5,4] | 45 %; przebieg 42 | 1,43 [1,23; 1,76] | 0,83 | 0,44 [0,26; 0,64] | 5,9 [3,8; 8,4] | 33 %. SCI300 różnica SD ln po−przed na poziomie pary −0,014 [−0,040; +0,011]. Nachylenia Deminga SCI300 0,57/0,48/0,25.
- Mikroodcinki (ta sama noc, bez korekty T): mediana ilorazu D0 FWD/d0 TSD **1,54** (IQR 1,33–1,72), 119 kombinacji odcinek × noc; przedziały kalibracji TSD 1,52 i 1,54; na odcinkach 1,08–1,73. Rozrzut ln ilorazu w odcinku 0,13–0,24 (mediana 0,17). SD ilorazu d0/D0 w odcinek × noc ok. 8 %. Szum rekordu TSD (SD ln): odpowiednik SCI300 0,593 vs d0 0,296 (kom. C85).
- **Tab. 6.1 / 6.2** — wrażliwość TSD vs FWD (jeśli N3/N4 mają weryfikować): patrz sekcja 6.

---------------------------------------------------------------------
## 5. SPECYFIKACJA FUNKCJONALNA — N4 `tsd_fwd_compare` (R7.2, R3.6–3.8, R3.12, R6.1–6.3)

### 5.1 Zalecenia R7.2 (6 punktów)
1. **Plan pomiaru:** oba urządzenia tego samego dnia, najlepiej bezpośrednio po sobie (przy odstępie >1 dnia zgodność spada z ok. 0,86 do 0,32–0,37); odcinki o zróżnicowanej nośności; temperatura warstwy przy FWD zmierzona (z kontrolą otworów) + zapis głębokości; TSD — model N2 lub pomiar; FWD GNSS metrowej dokładności + dystansomierz; TSD (DGPS) jako odniesienie.
2. **Dane TSD:** d0 przeliczone jednym zestawem współczynników bez 1,51 m; krzywizna z całek nachyleń P0; dla każdej pary udział czasz GoF ≥ 0,5 w oknie — wyniki osobno dla wysokiego i niskiego udziału.
3. **Parowanie:** wyłącznie geometryczne wg Tab. 3.2 z weryfikacją „linia do linii”; dla stacji FWD mediana TSD z okna ±5 m wokół najbliższego punktu przejazdu (okno ±10 m: wyższa zgodność 0,51 vs 0,40 w obrębie sesji, kosztem rozdzielczości); **nigdy wybór rekordu TSD na podstawie ugięć FWD**; obowiązkowa kontrola zerowa: te same miary dla par przesuniętych o ±200 m i z permutacją stacji.
4. **Korekta temperaturowa przed porównaniem:** FWD — współczynniki czujników z R7.1, wskaźniki z ugięć skorygowanych; TSD — d0 współczynnikiem D0 FWD (błąd do ±5 % z 20–30 °C, ±10 % z 5–20 °C); nachyleń TSD nie korygować współczynnikami FWD bez weryfikacji.
5. **Miary i niepewność:** mediana ilorazu FWD/TSD; SD logarytmu ilorazu; korelacja w obrębie sesji; współczynnik zgodności Lina; granice zgodności Blanda–Altmana; nachylenie Deminga w skali log–log ze stosunkiem wariancji błędów z powtórzeń przejazdów; przedziały — bootstrap z losowaniem sesji (nocy) i metody dla małej liczby jednostek (R3.12); wyniki w podziale na: odstęp czasu, udział GoF, zmienność D0 odcinka, aparat FWD × okres kalibracji TSD.
6. **Krzywizna:** SCI300 FWD z ugięć skorygowanych; odpowiednik TSD = całka nachyleń 0–0,31 m; przelicznik orientacyjny; do porównań odcinków, nie punktów.

### 5.2 Detekcja wspólnych odcinków (R3.6–3.7)
Jednostka akceptacji = odcinek wspólnego przebiegu (nie punkt); do bazy trafiają wszystkie dane wewnątrz odcinka, także stacje FWD bez lokalnego punktu TSD. Dwie osie kryteriów: położenie (ta sama linia, zgodny kierunek) — rygorystycznie; liczba pokrywających się punktów — liberalnie. Algorytm dla każdej pary (sesja FWD, przejazd TSD) o nachodzących prostokątach otaczających: rzutowanie współrzędnych do lokalnego układu metrycznego; dla każdej stacji FWD najbliższy punkt TSD (drzewo k-d); weryfikacja odległości wzorem haversine; dla pary — odsunięcie poprzeczne ze znakiem (względem kursu TSD) i różnica kursów. TSD: ciągły, krok 1 m, z prędkością ruchu; FWD: stacje co 25–100 m z postoju. Pikietaż operatora NIE jest używany (różne jednostki); stacje rzutowane na oś przejazdu TSD przez najbliższy punkt.
**Tab. 3.2 — Parametry detekcji wspólnych odcinków (przepisana; L292–303):**

| Parametr | Wartość |
|---|---|
| Promień dopasowania r | 8 m |
| Minimalne pokrycie (względem stacji w zasięgu przejazdu TSD) | 30 % |
| Minimalna liczba dopasowanych stacji FWD | 5 |
| Minimalna długość wspólnego odcinka | 500 m |
| Minimalne |ρ Spearmana| (monotoniczność) | 0,80 |
| Tolerancja kierunku | 30° (zgodny) / 150° (przeciwny) |
| Granica klas pasa `same` / `adjacent` | 0,75 m / 2,0 m |
| Warunek czasowy | ten sam rok kalendarzowy |

Uzasadnienie progów: pierwsza wersja (3 stacje, pokrycie liczone w obrębie nakładania) dała fałszywy „odcinek” (przejazd TSD 3,16 km przecinający trasę FWD 24 km: wspólny fragment 152 m, 3 stacje, pokrycie 100 %); progi 5 stacji i 500 m usunęły 11 takich przypadków, skracając łączną długość klasy `same` o 0,18 %. Warunek roku: różne lata = inny stan nawierzchni.
**Weryfikacja (R3.7):** każdy odcinek ręcznie, wizualizacja „linia do linii” (oś = pikietaż przejazdu TSD; wszystkie pomiary TSD co 1 m i wszystkie stacje sesji FWD, nie tylko dopasowane); ciągłość oceniana nachyleniem czaszy przy 0,310 m, poziom — D0; ślad GPS z zakresem odcinka. Odcinki z jedną parą dla przejazdu TSD — auto-zatwierdzane (41); 123 ręcznie; **wszystkie 164 zatwierdzone, bez odrzuceń**; baza bieżąca: 167 odcinków. Przeniesienie decyzji do nowej wersji bazy po kluczu geometrycznym (przejazd TSD, plik i sesja FWD, kierunek, klasa pasa, zasięg pikietażu, liczba dopasowanych stacji, mediana odsunięcia poprzecznego); nowe odcinki — ręcznie, bez auto-zatwierdzania. Najdłuższy odcinek 18,9 km: rozrzut boczny stacji FWD −3,9…+3,4 m (10.–90. percentyl, mediana −0,33 m), lokalne odchylenia do 27 m (zaburzenia GPS FWD).

### 5.3 Dopasowanie punktowe i kontrola zerowa (R3.8)
- Procedura „kandydatów” (opisowa; nie „złote pary”): okno ±5 m od punktu najbliższego stacji; każdy rekord TSD osobnym kandydatem (bez uśredniania); ugięcia obu urządzeń do wspólnego obciążenia 50 kN; ocena trzema składnikami: kształt czaszy (skala log, względem czujnika centralnego), poziom ugięcia, odległość od punktu bazowego; systematyczna różnica urządzeń szacowana na pozostałych stacjach tej samej pary przejazd–sesja (leave-one-out). Kontrola: 1000 permutacji czasz FWD; odsetek permutacji ≥ wyniku rzeczywistego ≈ 0,10 i 0,31 — wybór niepotwierdzony. Ustalenia: dopasowanie położenia kształtem czaszy nie działa; zawężenie okna do ±1 m / 1 rekordu pogarsza zgodność.
- **Zalecana procedura (geometryczna, bez wartości FWD):** mediana TSD z okna ±5 m (W5) lub ±10 m (W10).
- Kontrola na 5511 parach (36 sesji): korelacja logarytmów w obrębie sesji (r_within_session): wybór wg FWD (C_raw) 0,615 (zerowe 0,565/0,557/0,559; w tekście 0,62 vs ok. 0,56); rekord najbliższy 0,28; **W5 0,403** (zerowe 0,155/0,135/0,096); **W10 0,511** (zerowe 0,150/0,153/0,087); X_b1510 0,508 (zerowe 0,149/0,163/0,076); X_nom (eksport nominalny, z 1,51 m) 0,405; zerowe w tekście 0,08–0,16. Mediana ilorazu FWD/TSD: X_nom 0,523 → C_raw 1,063 (wybór wg FWD przesuwa poziom: „zgodność 1:1” artefaktem); W5 1,615. Pearson (łącznie): X_nom 0,257; X_b1510 0,750. Kalibracja przelicznika: W5 mnożnik k02 MAE 27,68 µm (próba) / 27,74 µm (poza próbą); C_X afiniczna 22,89 / 23,71 µm.
- Warunki zgodności (R6.2; r Pearsona logarytmów, wszystkie pary warstwy łącznie, bez przedziałów): odstęp ≤1 dzień (3 sesje maj 2026 DK50 i S8, 119 par) **0,86** vs 0,32–0,37 przy odstępie 2–30 i >30 dni; udział GoF≥0,5 ≥80 % w oknie: 0,81 (1481 par), <50 %: 0,38 (1315 par); górny tercyl zmienności D0 FWD 0,82, dolny 0,49; eksport nominalny vs przeliczone: 0,41 vs 0,51; stosunek eksport/przeliczone 1–5,5 między rekordami. Pary z tego samego dnia pochodzą z aparatu z nowym GPS — wpływy nierozdzielne.
- Pary sieciowe (R6.2): 5511 par/36 sesji FWD, lata 2024–2026; różnica korelacji pary prawdziwe vs zerowe (±200 m, permutacja) 0,14–0,26 (przedziały >0); mediana odstępu 75 dni; mediana T warstwy FWD 9 °C; mediana T powierzchni TSD 24 °C.

### 5.4 Miary i niepewność (R3.12, R6.3)
- Przedziały: **bootstrap klastrowy** (losowanie całych jednostek ze zwracaniem: sesje FWD dla par TSD–FWD, noce dla mikroodcinków, dni dla współczynników, foldy/doby dla temperatury); przedział percentylowy; 1000 powtórzeń (R6.3; R5.1), 2000 (R4.10 po sesjach). Losowanie pojedynczych rekordów zabronione.
- Przy małej liczbie jednostek: dziki bootstrap klastrowy z wagami Webba [15] (M1; 9999 replik; Cameron–Gelbach–Miller [14]), CR2 z poprawką Bella–McCaffreya [16] (M2), klaster tygodniowy (M3; 13 tygodni); dla szeregów temperatury: bootstrap stacjonarny Politis–Romano [9] z blokiem Politis–White [10][11] (336–440 rekordów) i test Diebolda–Mariano [12] z poprawką Harvey–Leybourne–Newbold [13]. Pokrycie w teście syntetycznym 95 %-owego przedziału: 86 % (5 jednostek), 92–94 % (15–73 jednostek).
- Test równoważności [23] (Lakens; R5.4, R6.1): korekta równoważna w ±δ, gdy cały przedział 90 % błędu mieści się w ±δ; δ ∈ {1,37; 2; 3; 5; 7; 10 %}; wynik: R/N/X.
- Miara ilorazu: mediana ilorazu D0 FWD/d0 TSD (mnożnik), też średnia geometryczna (1,60); SD ln ilorazu; odchylenie odporne 1,4826·MAD(ln ilorazu); korelacja Pearsona na logarytmach (`e2b2_agreement.point_stats`); Spearman; Lin CCC; **granice zgodności Blanda–Altmana dla ilorazu** (wniosek z liczb: GM_ratio·exp(±1,96·SD ln): 1,60·exp(±1,96·0,321) = 0,85–3,00 po korekcie; przed: 0,71–2,71; obl. własne zgodne); **Deming** w skali log–log (nachylenie; wyraz wolny w skali liniowej w µm osobno) ze stosunkiem wariancji błędów λ z powtórzeń przejazdów (`e2b2_lambda.csv`: sigma_tsd a031 0,593, d0 0,296 — wartość λ dla d0 w raporcie nie podana; wrażliwość: λ ×0,5 i ×2 nie zmienia wniosków). Logarytmy liczone tylko na parach z dodatnimi wartościami po obu stronach.
- Poziomy uśrednienia (R6.3): L1 para; L2 przedziały 100 m w obrębie pary sesja FWD × przejazd TSD (mediana obu stron; 395 przedziałów d0, 16 sesji); L3 całe wspólne przebiegi (63 przebiegi, 35 sesji).
- Stratyfikacja wyników: odstęp czasu (≤1 d; 2–30; >30), udział GoF (≥80 %; <50 %), tercyl zmienności D0, aparat FWD × okres kalibracji TSD (hwd_2024, hwd_2026, old_2024 [8002-367], old_2025, unconfirmed_2026 [8002-369]).
- Pytania/kryteria ex ante R6.3: (1) Δ SD ln ilorazu po−przed, potwierdzona gdy cały przedział 95 % <0; (2) rozstęp i SD median grupowych w skali log — to samo; (3) proporcjonalność: Deming log–log obejmuje 1 → mnożnik zamiast prostej z wyrazem wolnym; (4) dla krzywizny: czy uśrednienie zbliża rozrzut ilorazu do rozrzutu d0 (nie).

### 5.5 Wrażliwość temperaturowa TSD vs FWD na mikroodcinkach (R6.1; jeśli N4 ma to testować)
Zbiór: 1131 par z 15 nocy (d0; bez nocy HWD, odstających i kombinacji <5 par); nachylenia: 1154 pary z 14 nocy; kanały 792–1122 pary po odrzuceniu niedodatnich nachyleń TSD. T10 (sonda 10 cm, raz na odcinek/serię). Estymator jak R5.1 (GLM log-link, efekt punktu; punkt × miesiąc/odcinek), bootstrap po nocach (M0), M1, M2. Δβ d0 = β_TSD − β_FWD = −0,10 [−0,29; +0,16] %/°C (M0; Tab. 3.3), M1 [−0,45; +0,25], CR2 [−0,41; +0,21]; warianty zbioru −0,12…+0,05; Δβ d0 −0,102 (kom. C70). β_FWD D0 1,60 %/°C. 30–60 nocy dałoby ±0,2 %/°C.
**Tab. 6.1 (przepisana; Δβ = β_TSD − β_FWD [%/°C], 90 %):**

| Kanał nachylenia [m] | n par | β_FWD nachylenia [%/°C] | Δβ | Przedział 90 % | Przedział 90 %, M1 |
|---|---|---|---|---|---|
| 0,11 | 1104 | +4,14 | −0,29 | [−1,16; +0,93] | [−1,64; +1,07] |
| 0,21 | 1121 | +3,54 | −0,16 | [−0,77; +0,62] | [−0,98; +0,65] |
| 0,31 | 1047 | +2,54 | −0,14 | [−1,16; +1,15] | [−1,56; +1,30] |
| 0,46 | 1087 | +1,57 | −0,21 | [−0,54; +0,22] | [−0,73; +0,29] |
| 0,61 | 1122 | +0,83 | +0,27 | [−0,28; +0,85] | [−0,48; +1,02] |
| 0,91 | 792 | −0,16 | −1,86 | [−2,64; −0,85] | [−2,86; −0,80] |

Nachylenia FWD z ugięć geofonów interpolacją PCHIP (kontrolnie ilorazem różnicowym: Δβ 0,02–0,18 %/°C).
**Tab. 6.2 (przepisana; test równoważności; najmniejsza tolerancja M0 / M1–M2):**

| Wielkość | e(30 °C) [%], 90 % | tol. M0 / M1–M2 | e(5 °C) [%], 90 % | tol. M0 / M1–M2 |
|---|---|---|---|---|
| d0 | −1,02 [−2,67; +1,14] | 3 % / 5 % | +1,55 [−1,68; +4,14] | 5 % / 7 % |
| nachylenie 0,11 m | −2,85 [−10,94; +9,71] | — / — | +4,43 [−12,98; +18,99] | — / — |
| nachylenie 0,21 m | −1,54 [−7,45; +6,35] | — / 10 % | +2,36 [−8,82; +12,32] | — / — |
| nachylenie 0,31 m | −1,38 [−10,94; +12,24] | — / — | +2,11 [−15,90; +18,98] | — / — |
| nachylenie 0,46 m | −2,03 [−5,22; +2,18] | — / 7 % | +3,13 [−3,18; +8,38] | — / — |
| nachylenie 0,61 m | +2,74 [−2,76; +8,82] | — / — | −3,98 [−11,91; +4,29] | — / — |
| nachylenie 0,91 m | −16,95 [−23,22; −8,17] | różny / różny | +32,13 [+13,64; +48,63] | różny / różny |

(„—” brak równoważności do 10 %; kom. C72: d0 e30 M1 [−3,71; +1,74], M2 [−3,45; +1,48], M3 [−4,48; +2,60] → δ=5; e5 M1 [−2,55; +5,93], M2 [−2,18; +5,41] → δ=7; M3 [−3,89; +7,03] → δ=10.)

### 5.6 Tab. 3.3 — odporność wyników na metodę niepewności (przedziały 95 %; referencje; L390–401)

| Wynik | Metoda główna | Alternatywne | Czy wniosek się zmienia |
|---|---|---|---|
| Różnica RMSE hybryda B − fizyka (Tab. 4.1) | TN −0,27 [−0,43; −0,10], Podkowa −0,40 [−0,49; −0,34] °C (foldy) | bootstrap stacjonarny TN [−0,37; −0,17], Podkowa [−0,48; −0,32]; DM p<0,0001 | nie |
| β D0, oba stanowiska (Tab. 5.1) | 1,60 [1,51; 1,73] %/°C | odp. liniowy 1,58: dziki [1,46; 1,69], CR2 [1,46; 1,69], tygodniowy [1,43; 1,72] | nie — k=0,02 poza każdym przedziałem |
| Błąd korekty D0, 25–30 °C (Tab. 5.2) | równoważny w ±3 % | j.w. w każdej metodzie | nie |
| Błąd D300 i D900, 25–35 °C | współczynniki czujników: ±3 % (25–30 °C także ±2 %); k=0,02: ≠0 | M1, M2, tygodniowy: k=0,02 ≠0; współczynniki czujników ±3 % w 25–30 °C; przy tygodniowym D900 nierozstrzygnięty w ±2 % (25–30) i ±3 % (30–35) | nie dla 25–30 °C; w 30–35 °C D900 tylko metoda główna |
| Błąd SCI300, 25–30 °C | nierozstrzygnięty w ±5 % | j.w. | nie |
| Mnożnik d0 TSD → D0 FWD (R6.3) | 1,62 [1,54; 1,68] (mediana) | śr. geom. 1,60: dziki [1,54; 1,66], CR2 [1,54; 1,66] | nie; w grupach aparat × rok (3–15 sesji) przedziały 1,3–2,0 razy szersze |
| Błąd korekty d0 TSD współczynnikiem FWD (Tab. 6.2) | ±3 % (20–30 °C), ±5 % (5–20 °C) | ±5 % (20–30), ±7–10 % (5–20) | tak — szersze granice |
| Δβ d0 TSD−FWD, mikroodcinki (Tab. 6.1) | −0,10 [−0,29; +0,16] %/°C | dziki [−0,45; +0,25], CR2 [−0,41; +0,21] (14 nocy) | nie wykryto, możliwa wielkość 0,3 → 0,45 %/°C |

---------------------------------------------------------------------
## 6. ZASTRZEŻENIA I OGRANICZENIA (R6, R7, R8) — skrót do wymagań niefunkcjonalnych
- Stanowiska: 2 (TN nasłonecznione z PMB 25 cm; Podkowa zacienione 24 cm), nierozdzielne efekty rodzaju pakietu i ekspozycji; 1 rok czujników; wizyty tylko dzienne (7–15 h); jedno obciążenie 50 kN; mało wizyt HWD; współczynniki sezonowe wstępne.
- Model temperatury sieciowy: 1,75 °C (>1,5 °C); noc nie działa; ekspozycja otwarta.
- TSD→FWD: pary niesynchroniczne; pirometr TSD niesprawdzony; mnożnik różni się do ok. 35 % między aparat × rok (przyczyny nierozdzielne); brak testu na mikroodcinkach korekty d0 TSD temperaturą zmierzoną vs modelowaną; przelicznik SCI orientacyjny (TSD niedodatni ~40 % par; rozrzut ilorazu 3–10× d0).
- Mnożnik tylko do wartości uśrednionych (≥100 m), nie do punktów; dla d0 TSD z innej definicji (np. eksport) przeliczyć od nowa; β wyznaczone dla 24–25 cm, grubość na sieci nieznana (wariant k=0,02 zmienia mnożnik o 2 %); sieć: T12 niezależnie od grubości.
- Przeliczanie d0 TSD ważne dla serii nocnych i dziennych? — dane sieciowe TSD tylko 8–18 h; mikroodcinki noc.
- Ważność ugięć skorygowanych FWD: SCI niestabilny także w powtarzanych pomiarach FWD (R8).
- Etap III (2027): narzędzia (N1–N4) do stosowania w Zakładzie; kampania porównawcza TSD–FWD wg R7.2; przelicznik w podziale aparat × przedział kalibracji; stabilizacja SCI; drugi rok stacji. **R7.4: każde narzędzie — zapisana konfiguracja, test na zbiorze referencyjnym (stanowiska TN i Podkowa, mikroodcinki, odcinki DK50 i S8 z maja 2026), krótka instrukcja.**
- Zasady reprodukowalności (R3.1, R3.11, R3.5): wartości surowe nietykane (ugięcia TSD bez filtracji/wygładzania/korekt); normalizacje, odszumianie, korekty tylko jako jawne wersjonowane produkty pochodne; testy regresyjne (11 tabel produktów); skrypty Python z testami jednostkowymi; sumy MD5; rejestr przebiegów (skrypt, parametry, czas).

---------------------------------------------------------------------
## 7. NIEJASNOŚCI I SPRZECZNOŚCI W RAPORCIE (pytania do autora)

Priorytet: **K** = blokuje implementację lub test akceptacyjny; **W** = ważne; **N** = drobne.

### 7.1 N3 / XML
1. **[K] Parametry filtra Hampela** (długość okna w rekordach/metrach, próg k·MAD i czy ze współczynnikiem 1,4826; kryterium: tylko d0 czy też inne kanały; „odrzut całej czaszy”) nie występują w raporcie (R7.3 p.4, R3.8 tylko ogólnie; kom. C90: „Hampel na D0 + średnia ±10 m”). Brak też rozstrzygnięcia: mediana czy średnia w oknie, ±5 m czy ±10 m (R7.3 p.4 podaje „±5–10 m”, XML „±10 m”, N4 zalecenie ±5 m). Skąd brać wartości — z `tsd_pipeline.py`?
2. **[K] Schemat XML („UC”) nieopisany.** Raport nie zawiera pojęcia „UC”, nie definiuje struktury XML, nazw pól, jednostek, segmentacji (co ile m), ani tego, które wielkości trafiają do pliku (d0 z konwersją? całą czaszę „D Tkor”? SCI?). Odesłanie wyłącznie do `C:\WORK\DOKTORAT\tsd_2_xml\README_workflow.md`. Co jest specyfikacją docelową: obecny format czy format „po zmianach” z p.1–3?
3. **[K] „D Tkor” i „BELLS3_BT”.** (R7.3 p.7, kom. C90) „BELLS3_BT” nie występuje w rozdz. 4 (tam: BELLS3 [19] i BELLS3_O [20]); co znaczy „BT”? Czy „D Tkor” (czasza z pliku 1 m) jest kolumną już skorygowaną (BELLS3_BT + k=0,02) w samym eksporcie TSD, czy wynikiem skryptu tsd_pipeline.py? Informacja pochodzi z „informacji Jacka 2026-11-13”, a stan skryptów z 2026-07-01 — czy sprawdzono w kodzie? Ryzyko **podwójnej korekty**, jeżeli N3 weźmie „D Tkor” zamiast ugięć surowych/„bez 1,51 m”. Narzędzie musi wiedzieć, której kolumny używać i jak wykryć, że wejście jest już skorygowane.
4. **[K] Konwersja afiniczna w XML.** „DK50 a 0,849 b +24,35; S8 a 0,473 b +41,72” — brak: kierunek (D_FWD = a·D_TSD + b?), jednostki (µm?), obciążenie, definicja wejścia (D Tkor po Hampelu +śr. ±10 m z czujnikiem 1,51 m?). Nachylenia <1 (DK50 0,849; S8 0,473) wydają się niezgodne z mnożnikiem 1,62 (D0_FWD,20 = 1,62·d0_TSD,20); wg obliczeń własnych dają przelicznik ≈1,0× i ≈0,75× — zgodne z ostrzeżeniem R3.8 (wybór wg wartości FWD zawyża „zgodność 1:1”), ale raport tego nie komentuje przy p.7. Czy N3 ma zachować dotychczasowy tryb afiniczny jako opcję legacy? Stałe dotyczą odcinków DK50 i S8 z maja 2026 = te same, które mają być zbiorem referencyjnym testu (R7.4) — test byłby kołowy.
5. **[K] Algorytm „d0 bez czujnika 1,51 m jednym zestawem współczynników”** (R3.10, R3.4 krok 7): raport podaje cel i skutki, ale nie algorytm (z jakich kolumn eksportu: surowe nachylenia? które współczynniki kalibracyjne i skąd; jaka funkcja czaszy; jak zrównano z eksportem oryginalnym na odcinkach 1 km i z jaką tolerancją). Dotyczy tylko 2024–2026 — co z przejazdami przed 2024 (kampania 2022, sieć 2020–2023)? N3 nie jest implementowalne bez kodu (`bak/e2a2b_beta.py`, `e2b2_values.py`).
6. **[K] Korekta temperaturowa krzywizny TSD nieokreślona.** R7.3 p.3 koryguje tylko d0; p.1 daje krzywiznę z całek P0 bez opisu korekty T. R6.3 (strona TSD) korygował całki „współczynnikiem odpowiedniego wskaźnika FWD”, ale Tab. 5.1/7.1 nie zawierają współczynników wskaźników (usunięte w v1.8, kom. C51), a R6.1/R7.2 mówią „nie korygować nachyleń TSD współczynnikami FWD bez weryfikacji”. Jakie współczynniki wskaźników zastosowano w P066 (Tab. 6.6) i czy N3/N4 mają je stosować? Bez tego nie da się odtworzyć Tab. 6.6.
7. **[K] Zakres vs referencyjne 1,62.** 1,62 [1,54; 1,68] policzono po korekcie wszystkich 5511 par, w tym T12 spoza zakresu 5–30 °C (FWD min 4,2 °C, TSD max 30,8 °C; Tab. 6.3 ↔ R6.3 „Temperatura w parach”), a R7.3 p.3 każe wyniki spoza zakresu oznaczać. Czy oznaczone wartości są wyłączane z konwersji? Test akceptacyjny „1,62” musi to wiedzieć.
8. **[W] Definicja jednostki „pomiar” przy kalibracji jednorazowej TSD:** czy a_SW dobiera się dla każdego rekordu 1 m, dla uśrednionego okna czy dla całego przejazdu? Które pozycje/czas: pomiar GPS rekordu? „skuteczna w 55 % pomiarów TSD” — jednostka niezdefiniowana.
9. **[W] Brak normalizacji obciążenia TSD**: R3.8 mówi o „wspólnym obciążeniu 50 kN” dla obu urządzeń, kom. C77 potwierdza tylko FWD D·50/F; jak normalizować TSD (siła na kole)?
10. **[W] N3: tryb nocny** — R7.3 p.2: „Pomiary nocne wymagają innego sposobu wyznaczenia temperatury (rozdz. 8)”, ale R8 tylko stwierdza, że to zadanie otwarte (a R4.10: BELLS3 nie gorszy w nocy; mikroodcinki noc: BELLS3 2,01 vs 2,61). Co ma zrobić narzędzie w nocy: BELLS3 fallback, T zmierzona, flaga i brak korekty?

### 7.2 N2
11. **[K] Brak wartości liczbowych parametrów modelu fizycznego**: a_SW (domyślny, zakres/granice poszukiwania — „górna granica” osiągana w 43–45 %), svf, h₀, h₁, pojemność cieplna, współczynniki modelu dolnego WB (regresja z harmonicznymi + 7/30-dobowymi średnimi), postać korekty IR→masa w trybie „survey” (R4.4 podaje tylko średnie różnice, a regresję IR opisano dla profilu stacjonarnego), hiperparametry XGBoost. „Wersja stanowiska nasłonecznionego” = które dopasowanie (który fold/pełny rok TN)? N2 nie da się zaimplementować z raportu — potrzebny kod `DOKTORAT\temp_model` (Z14d/Z15).
12. **[K] Głębokość wyjściowa i grubość pakietu:** standard sieciowy = 12 cm, ale T_mid = połowa pakietu; na sieci grubość nieznana (R6.3: „nie uwzględniano”), β wyznaczone dla 24–25 cm. Czy N2 ma zawsze wyznaczać T12, czy T(h/2) z grubości podanej przez użytkownika? Jak ostrzegać dla h ≠ 24–25 cm? (R7.4: „na zadanej głębokości”.)
13. **[W] Ocena niepewności N2** (R7.4 „z oceną niepewności”): brak zdefiniowanej formuły; propozycja z danych: RMSE zależne od pory dnia (6–12: 1,38; 12–18: 1,89; 0–6/18–24: 2,17 °C) — czy to ma być wyjście? Czy zastosować obciążenie +1,5 °C wieczorem?
14. **[W] Pirometr TSD vs FWD:** różnica pirometr aparatu FWD vs stanowisko +1,9 °C (SD ~4), brak korekty przyrządu („liniowa korekta nie zmniejszyła błędu”), pirometr TSD niesprawdzony — czy N2 ma mieć parametr przesunięcia pirometru?
15. **[W] Dane meteorologiczne:** wymóg dostępu do Open-Meteo/ERA5-Land (pobranie sierpień 2026, „konfiguracja domyślna”): dokładne zmienne/nazwy, model (ERA5 vs ERA5-Land), przetwarzanie UTC→czas lokalny; dla offline testów potrzebny zapisany plik. Dyskusja: niewyjaśniony test przesunięcia czasu zimą (kom. C36) — „do wyjaśnienia (Jacek), nie cytować”.
16. **[N] Różne wersje liczb:** Tab. 4.1/4.2 po poprawce czasu reanalizy vs publikacja_1 (do 0,07 °C); R4.8 i udział kotwicy (28,5 %/27,6 %) „sprzed poprawki”; Rys. 4.3 sprzed poprawki; starsze „headline” (kom. C35). Które liczby są referencyjne dla testów — przyjmuję: Tab. 4.1/4.2/4.3 po poprawce.
17. **[N] Odcinki 1 km:** „11 obserwacji” (zbiór) vs „9 obserwacji z jedną głębokością” w wynikach (R4.10) — wyjaśnić.

### 7.3 N1
18. **[K] Wartość k_D0 dla wariantu A: 0,016 (Tab. 7.1, dopasowanie 5–30 °C) vs 0,0175 (dopasowanie 5–25 °C, kom. C89) vs 0,01611 (R4/P068b).** Zakres A = 5–25 °C, więc spójniejsze byłoby k z dopasowania 5–25 °C (0,0175), co daje błąd D0 −2,10 % w 25–30 °C (Tab. 5.2), vs −1,06 % dla stałego 0,016. Zakres 5–15 °C nie ma testu pasmowego (brak wizyt odniesienia; kom. C54), ważność tam wynika wyłącznie z trendu resztkowego w 5–30 °C. Czy 0,016 jest ostateczne dla A?
19. **[W] Zaokrąglenie Tab. 7.1 vs pełna precyzja** (k: 3 miejsca; β: 2 miejsca %). Test akceptacyjny R4 wykonano dla niezaokrąglonych k_guide (D0 0,01611; D300 0,01234; D600 0,00703; D900 0,00329). Czy narzędzie ma używać wartości z Tab. 7.1 dosłownie czy z `e2a3_final_k_profile.csv`? Różnice względem pełnej precyzji: D450 +4 %, D900 −9 %, D300 −3 %. D450 w R4 w ogóle nie testowano.
20. **[W] Sprzeczność dot. zakresu „<2 %”:** R5.1: „w zakresie 5–30 °C korekty różnią się o mniej niż 2 %”; R7.1 B: „w zakresie 5–25 °C różnią się o mniej niż 2 %”. Obliczenie własne (k=0,0161): różnica exp/lin 2,55 % przy 5 °C (D0), 1,47 % przy 30 °C; <2 % dopiero od ok. 7 °C do ok. 31 °C. Sformułowanie wymaga poprawki lub zakresu.
21. **[W] SCI300 w wariancie B: ok. 7 % (Tab. 5.2: −6,77 [−14,28; −0,21]) czy −4,13 [−10,30; +1,42]** (reguła R3a_z_ugiec, stałe β z Tab. 7.1; kom. C87)? Tekst R7.1/R9 używa „ok. 7 %”, które pochodzi z dopasowania 5–25 °C. Analogicznie D0 25–30 °C: −0,53 (5–25) vs −0,31 (stałe β). Który zestaw jest referencją testu N1: współczynniki Tab. 7.1 (5–30) czy z dopasowania 5–25?
22. **[W] Poziomy ufności w tekście R5.4 vs tabela:** TN D0 25–30: tekst −0,8 % [−2,6; 0,9], tabela −0,80 [−2,36; +0,60]; oba stanowiska: tekst −0,5 [−2,7; 1,3], tabela [−2,37; +0,99]; mikroodcinki: tekst +1,6 [−3,1; 6,2], tabela [−2,88; +6,00] — tekst prawdopodobnie przedziały 95 %, tabela 90 %, ale tekst nie mówi. Test akceptacyjny: który przedział?
23. **[W] Mapowanie czujników:** Tab. 7.1 dotyczy 9 pozycji (0…1800 mm). Brak reguły dla aparatów/konfiguracji o innych pozycjach geofonów, brakujących czujników (np. brak D1800, D200), interpolacji współczynnika; dla HWD? Brak też informacji, czy dla D450, D1200–D1800 stosować korektę, skoro współczynniki „orientacyjne”.
24. **[W] Temperatura wejściowa FWD sieciowego:** w plikach FWD temperatura warstwy wpisywana ręcznie raz na zmianę i przenoszona (R3.9). Raport nie podaje reguły, ile wynosi dopuszczalny wiek wpisu (1 h to tylko statystyka), kiedy zastępować modelem N2, czy interpolować między wpisami, ani jak łączyć głębokość sondy (4/8/12 cm) z T_mid. Zakres „oznaczenie pomiarów spoza zakresu” dotyczy tylko T? Brak kryteriów „kontroli jakości otworów” (R2.3; np. inwersja profilu 12 > 4 cm w >86 % pomiarów?).
25. **[W] Dwie głębokości T (4 cm i T_mid):** R7.1 zaleca, ale nie podaje wzoru ani współczynników korekty dwutemperaturowej (R5.8 opis modelu z gradientem T4−T_mid); wniosek „dla sondy niespójny”. Czy implementować?
26. **[N] Zastosowanie wariantu A dla TSD d0?** R7.1 „oba stosuje się także do d0 TSD”, ale R6.3/R7.3 używa wyłącznie wariantu B (β=1,60 %/°C); zakres liniowy 5–25 °C vs d0 TSD w 20–30 °C testowane (R6.1).
27. **[N] Pomiary <5 °C:** „korekta nie ma zastosowania” — narzędzie ma zwrócić NaN czy ugięcie niekorygowane z flagą?

### 7.4 N4
28. **[W] Definicje w Tab. 3.2:** „minimalne |ρ Spearmana| 0,80 (monotoniczność)” — między jakimi zmiennymi (pikietaż FWD vs pikietaż TSD rzutowany? lub kolejność stacji)? „Pokrycie względem stacji w zasięgu przejazdu TSD” — co to zasięg (prostokąt otaczający, buforowany r?). Czy klasy `same`/`adjacent` wg mediany |odsunięcia poprzecznego| ≤0,75 m / ≤2,0 m? Relacja r = 8 m do okna ±5 m i do rozrzutu bocznego −3,9…+3,4 m. Kierunek: „150° (przeciwny)” — czy obejmuje przeciwny kierunek ruchu jako akceptowany odcinek?
29. **[W] Definicja „korelacji w obrębie sesji”** (R3.8, kom. C26): średnia korelacji per sesja, czy korelacja po odjęciu średnich sesji, czy korelacja łączna ważona? Różni się od `pearson_r łącznie` (np. X_nom 0,405 vs 0,257). Kolejność trzech liczb „zerowe 0,155 / 0,135 / 0,096” w komentarzu nie jest opisana (zakładam: −200 m / +200 m / permutacja); w tekście tylko zakres 0,08–0,16. Wartość 0,28 (rekord najbliższy) w tekście R3.8 nie ma źródła w komentarzach.
30. **[W] Deming:** liczbowa wartość λ (stosunek wariancji błędów „z powtórzeń przejazdów”) nie jest podana; kom. C85: sigma_tsd (ln) d0 = 0,296 (a031: 0,593). Skąd wariancja błędu FWD (D0 powtarzalność 1,37 % TN / 4,6 % Podkowa)? Czy λ taka sama dla analiz log–log i liniowej (wyraz wolny w µm)? Wyraz wolny liniowy Deminga (−5,7 → +8,2 µm) wymaga osobnej definicji.
31. **[W] Współczynnik Lina:** R7.2 p.5 wymienia go jako miarę, ale R6.3 (kom. C78) świadomie go nie podaje („mierzy zgodność z linią 1:1, a nie jakość przeliczenia”; spada 0,42 → 0,35). Czy N4 ma go raportować na logarytmach czy w µm?
32. **[W] Mnożnik oficjalny:** mediana ilorazu 1,62 vs średnia geometryczna 1,60 (Tab. 3.3). Dla N4: raportować oba? Granice Blanda–Altmana są centrowane na 1,60 (GM), przelicznik na 1,62 (mediana).
33. **[W] Definicje GoF:** „udział czasz o GoF ≥ 0,5”, „próg eksportu GoF 0,01” — skąd pochodzi GoF (kolumna eksportu producenta?), co mierzy (dopasowanie funkcji czaszy do nachyleń?).
34. **[N] Liczby 119:** „119 par” (≤1 dzień, 3 sesje maj 2026), „119 kombinacji odcinek × noc” (mikroodcinki, R6.3, R5.4) i „120 grup” (R4.10, mikroodcinki) — czy to rzeczywiście niezależne liczby (nie błąd przepisania)?
35. **[N] Ten sam zbiór referencyjny** (R7.4: DK50 i S8 maj 2026; sesje 225–227, baza_odcinki_v4, km 43–46 i 6–9,4) jest wykorzystany do kalibracji XML i do pary „≤1 dnia (0,86)”: jaki jest podział kalibracja/test?
36. **[N] Pary mikroodcinkowe:** brak testu korekty d0 TSD temperaturą zmierzoną i modelowaną (R8) — nie ma więc liczby referencyjnej, którą narzędzie mogłoby odtworzyć dla ścieżki „mikroodcinki z korektą”; iloraz 1,54 jest bez korekty (ta sama temperatura).
37. **[N] Struktura raportu:** komentarz C94/C95 (numeracja literatury), odwołanie do „załącznika C” (R5.3, kom. C51) niewchodzącego w skład pliku; „Tab. 5.1 … przedziały ufności osobno dla stanowisk — załącznik C” — przedziałów brak w raporcie (wartości punktowe TN/Podkowa).

### 7.5 Pięć najważniejszych (do odpowiedzi końcowej)
(a) Parametry Hampela i definicje XML/„D Tkor”/BELLS3_BT/konwersji afinicznej (pozycje 1–4). (b) Brak liczbowych parametrów N2 i grubości/głębokości (11–12). (c) Brak algorytmu przeliczenia d0 TSD bez 1,51 m (5) i niezdefiniowana korekta temperaturowa krzywizny TSD (6). (d) Referencyjny mnożnik 1,62 policzony na wszystkich parach, także poza zakresem 5–30 °C (7). (e) k_D0 = 0,016 vs 0,0175 vs 0,01611 i zaokrąglenia Tab. 7.1; zakres 5–15 °C bez testu pasmowego (18–21).

---------------------------------------------------------------------
# ANEKS A — pełny tekst wszystkich 95 komentarzy HTML (wyciąg automatyczny, linie L i najbliższy poprzedzający nagłówek)

[C01] L6 | pod: # Weryfikacja zależności funkcyjnych wpływu temperatury na wartość modułu sztywności warstw asfaltowych — Etap II
WERSJA v1.12 (2026-11-13): wyniki P071 (SQL wpis 254, ffd2e85) — §3.8 kontrola wyboru w oknie na całej sieci, §6.2 akapit „Warunki zgodności” (odstęp czasu, GoF, zmienność D0, eksport nominalny, stabilność kalibracji); rozdz. 7 rozszerzony: 7.1 korekta temperaturowa (dotychczasowa treść), nowe 7.2 badania porównawcze TSD–FWD, 7.3 przetwarzanie TSD na sieci (w tym procedura XML tsd_2_xml), 7.4 narzędzia; rozdz. 8 — dwa punkty Etapu III; §1.4.
v1.11 (2026-11-12, noc): uwaga Jacka — eksport nominalny TSD zawiera D-450…D1500; §3.10 (skąd biorą się ugięcia eksportu i dlaczego krzywizna z całek nachyleń, W91; nowe akapity „Całki nachyleń” i „Całki a ugięcia z eksportu”), §6.3 (strona TSD; kontrola na mikroodcinkach — oba zbiory P0) i wniosek 8 poprawione (było: „TSD nie daje ugięcia D300”).
v1.10 (2026-11-12, noc): wyniki P070 (SQL wpis 252, 66d64b1) — §5.4: mechanizm błędu SCI300 (mnożnik A = D0/SCI300 ≈ 5, zmiana kształtu czaszy ln(D300/D0) powyżej 25 °C, zmienność przestrzenna na mikroodcinkach); §6.1 Tab. 6.2: werdykt M0 dla 0,91 m poprawiony w SQL (e2aR7_dbeta_slopes_v2); §6.3: notka o odstępstwie strony TSD od zasady „najpierw czujniki” (kontrola P070 nierozstrzygająca — w wariancie kanałowym inna wielkość po stronie FWD).
v1.9 (2026-11-12, wieczór): wyniki P069 (SQL wpis 250, 7c80b5a) — Tab. 3.3: wiersz D300/D900 (e2aR7_robust_D300_D900); §6.1 w kategoriach d0 i nachyleń czaszy (Tab. 6.1 i 6.2 z kanałami 0,11–0,91 m zamiast odpowiedników wskaźników; zasada „najpierw czujniki, potem wskaźniki”), wniosek 7; §5.4: pasmo 10–15 °C jako wariant orientacyjny (próg 5), błąd SCI300 na tle powtarzalności (symulacja „tylko szum”) i rozkład na stanowiska przy stałych współczynnikach (R4); Rys. 5.6 i 5.6b — wersje tylko z β D0. §6.3 (strona TSD) bez zmian do kontroli P070 (D017).
v1.8 (2026-11-12): zasada „najpierw korekta na czujnikach, potem wskaźniki” (decyzja Jacka 2026-11-12) — usunięto współczynniki wskaźników krzywizny (Tab. 5.1, §5.3, wiersze „SCI300, własny współczynnik” w Tab. 5.2, β SCI300 w obrębie dnia w §5.5, Tab. 7.1; panel SCI300 Rys. 5.6 — do przebudowy, D016); §5.3: porównanie CV na 9 czujnikach i SCI300 z ugięć skorygowanych, jak publikacja_2 §3.3 (było: średnia 12 wielkości z własnymi współczynnikami wskaźników), mnożnik 1,7–2,2 (było 1,4–1,7 / 1,4–2); §5.4: progi testu zakresu (20 obserwacji w paśmie, 2 wizyty odniesienia), nowy akapit „Obecny wzór dla całej czaszy” (k = 0,02 dla D0, D300, D900; k = 0,01 dla D0 — jak publikacja_2 Tabela 3), SCI300 przy k = 0,02 w 25–30 °C — znoszenie się błędów składowych; rozdz. 7: wstęp i Tab. 7.1 bez wskaźników; wniosek 3 od ugięć.
v1.7 (2026-11-11): zgodność z publikacją_2 v2.7 — §5.4: skala powtarzalności (TN typowa ekspozycja, Podkowa stale zacieniona), test zakresu tylko od 15 °C, nowy akapit „SCI300 w dopuszczalnym zakresie temperatury” (k = 0,02 vs współczynniki czujników); nowy §5.8 głębokość pomiaru temperatury (P053/P054); rozdz. 7: wariant A — pasma 15–25 °C, pkt 2 — dwie głębokości; wnioski 3 i 5; uwaga do [5]. Tab. 3.3 i wniosek 4 bez zmian (publikacja dostosowana do raportu).
v1.5 (2026-11-09, noc): bibliografia przenumerowana w kolejności cytowania i zweryfikowana (dawne [18]–[25]); §1.2 — zdanie o DOT bez źródeł Janowskiego (niedostępne; decyzja Jacka); kalendarz wizyt §2.2/§2.4 odpuszczony; rysunki zostają.
v1.4 (2026-11-09, wieczór): P068b — §6.1, Tab. 3.3 i wniosek 7: granice przenoszenia korekty FWD na d0 TSD ±5 % (20–30 °C) i ±10 % (5–20 °C) wg metod odpornych; rozdz. 7 i §5.4: wariant A ze stałymi k (R4) potwierdzony w 15–25 °C, uzasadnienie granicy 25 °C.
v1.3 (2026-11-09, uwagi Jacka 17:57 i 18:16 — zasada: postać liniowa tylko 5–25 °C, szerszy zakres tylko postać wykładnicza; BELLS3_O zostaje jak jest): odniesienie BELLS3 zamiast BELLS3_O (BELLS3_O tylko wiersz Tab. 4.1); rozdz. 7 — dwa warianty (A: obecny wzór liniowy z nowymi k; B: postać wykładnicza) dla D0 i SCI300 + Tab. 7.1 (k i β dla czaszy); Tab. 5.2 + wiersze postaci liniowej; zakres 25/30 °C bez kategorycznych stwierdzeń (5.4, 7, wniosek 4); przelicznik orientacyjny SCI300 TSD → FWD (6.3, 7, wniosek 8); wnioski 2, 3, 9 (f_s); D7 = tak (bez znaczników OPCJONALNIE).
v1.2 (2026-11-09, wieczór): §4.7 lato/noc z Z16 (przeformułowane — noc nie jest miejscem największej poprawy w IV–X); nowy §3.12 niepewność i jej odporność (Z16 + P068; Tab. 3.3; źródła [18]–[25]), dawny 3.12 → 3.13; §6.1 i wniosek 7: ±20–30 % zamiast ±20 %; Tab. 6.2 — [P068b]; §6.3 grupy; [3] rok 2024 potwierdzony.
v1.1 (2026-11-09): rozdz. 4 po Z15b (Tab. 4.1 po poprawce czasu reanalizy + przypis; nowa Tab. 4.2 miar odpornych; Tab. 4.3/4.4 = dawne 4.2/4.3 z medianą i P90; §4.2 czas reanalizy; §4.7 lato/noc = [Z16]); §6.3 krzywizna (P066) + poziomy uśrednienia d0; §5.7 = publikacja_2 v2.6 (Tab. 5.3, XI 1,05, IV 1,11); §6.2 bez znacznika; źródła [14]–[17] z publikacji_2; §7, §8, §9. Klon SQL: 779cfac.
v1.0 (2026-11-07, popr. po uwagach Jacka 11:17: Tab. 5.2 + D200…D900 i SCI300/BDI/BCI z ugięć skorygowanych (P052, wariant CB), 5.4, 7 pkt 2–3, wnioski 3, 4, 8 — luka SCI dla TSD; build: szerokości kolumn tabel. Wcześniej: rozdz. 6.3 napisany — przeliczanie TSD→FWD po korekcie temperaturowej, wyniki P065 + kontrola na mikroodcinkach; aktualizacja 1.1, 1.4, tab. harmonogramu, 6.2, 7, 8, 9; poprawka zaokrąglenia w 6.2: Deming 1,22 → 1,23. Klon SQL_TSD_FWD: commit 4619865 (P065c). Tab. 4.1/4.2 — czekają na Z15b).
v0.9 (2026-11-06: nowy rozdz. 4.10 — sprawdzenie modelu temperatury na odcinkach sieci, Z14 v2; odesłania w 4.8 i 4.9). v0.8 (2026-10-30: zalacznik C wlaczony do rozdz. 3 jako 3.6-3.12, numeracja rysunkow 3.1-3.7 i Tab. 3.2; TOC bez hiperlaczy). v0.7 (zalacznik C - metodyka i narzedzia przygotowania danych; wzmianki w 3.4 i 6.2). v0.6 (2026-10-30: uwagi autora 1-8 z 30.10 - skrocony wywod o modulach, rozliczenie harmonogramu karty, rozbudowany rozdz. 3 z trzema diagramami, zapowiedz rozdz. 6.3; rejestr uwag: raport_PWS-1063_uwagi_autora.md). v0.5 (2026-10-25: współczynniki sezonowe → obserwacja; zakres korekty krzywizn; noce/odcinki objaśnione). v0.4 (2026-10-24: wyniki P049 — test równoważności, LAMB, rysunki PL; v0.3: źródła wzoru — KWRNPP-2001 [2], rozporządzenia [4], [5]; renumeracja cytowań). v0.2 (Cowork DOKTORAT, 2026-10-23, noc): rozdziały 1–9 (pełny szkic); otwarte miejsca po P049 (test równoważności, LAMB) i D7 (sezon). v0.1 — rozdz. 1–3.
Cytowania [6]–[11] przejęte z publikacja_1 v5.3 i potwierdzone wyszukiwaniem 2026-10-23 ([9] — wynik BazTech; [6], [7], [11], [8] — strony wydawców / TRID / FHWA).
Szkielet: raport_PWS-1063_szkielet.md (v0.2). Plan: 00_PLAN_PRAC_2026Q4.md.
Źródła liczb podano w komentarzach HTML przy akapitach (nie trafiają do wersji finalnej).
Klon SQL_TSD_FWD: commit a2440fe (2026-10-21).
Znaczniki: [DO UZUPEŁNIENIA] — dane od autora; [TUTAJ POTRZEBNE ŹRÓDŁO — …] — cytowanie do weryfikacji.

[C02] L66 | pod: ### 1.2. Korekta temperaturowa i sezonowa ugięć w praktyce krajowej
źródło: monografie/PUB-E §1; wartości f_s: III 1,00; IV 1,04; V 1,08; VI 1,12; VII 1,15; VIII 1,17; IX 1,20; X 1,22; XI 1,25; XII 1,28

[C03] L69 | pod: ### 1.2. Korekta temperaturowa i sezonowa ugięć w praktyce krajowej
Decyzja Jacka 2026-11-09: źródła Janowski i in. 2000 (sprawozdanie DOT) i Janowski 2006 (prezentacja) niedostępne — zdanie ogólne, bez cytowania.

[C04] L70 | pod: ### 1.2. Korekta temperaturowa i sezonowa ugięć w praktyce krajowej
źródło: W113

[C05] L111 | pod: ### 2.1. Stanowiska pomiarowe TN i Podkowa
źródło: PUB-E §2; publikacja_1 §2

[C06] L131 | pod: ### 2.1. Stanowiska pomiarowe TN i Podkowa
źródło: publikacja_1 §2 (Pt100 kl. A, Qulon-RTS); pamięć projektu (terminologia, korekta 2026-09-03)

[C07] L136 | pod: ### 2.1. Stanowiska pomiarowe TN i Podkowa
źródło: pamięć projektu (doktorat-terminologia-dane): 52 560 wierszy, braki 0,13–0,17 %, DST 12 wierszy

[C08] L139 | pod: ### 2.1. Stanowiska pomiarowe TN i Podkowa
źródło: raport_metodyka_baza_TSD_FWD.md rozdz. 11; wpisy 46–47; W42

[C09] L148 | pod: ### 2.1. Stanowiska pomiarowe TN i Podkowa
źródło: wpis 47; raport_metodyka rozdz. 11 (593 wizyty)

[C10] L157 | pod: ### 2.2. Pomiary ugięć FWD na stanowiskach
źródło: PUB-E §2, §3; wpisy 117–121

[C11] L162 | pod: ### 2.2. Pomiary ugięć FWD na stanowiskach
źródło: PUB-E §2; W115 (mróz: D0 82–88 µm; roztopy II–III: 134–196 µm)

[C12] L172 | pod: ### 2.3. Pomiar temperatury: czujniki stałe a sonda w otworach
źródło: W102; PUB-E §4.1; wpisy 119, 120, 124

[C13] L175 | pod: ### 2.3. Pomiar temperatury: czujniki stałe a sonda w otworach
źródło: W106

[C14] L182 | pod: ### 2.3. Pomiar temperatury: czujniki stałe a sonda w otworach
źródło: PUB-E §4.1; wpis 124

[C15] L197 | pod: ### 2.4. Odcinki terenowe — serie nocne FWD i TSD
źródło: raport_metodyka_baza_TSD_FWD.md rozdz. 10.1

[C16] L206 | pod: ### 2.4. Odcinki terenowe — serie nocne FWD i TSD
źródło: PUB-E §2, §8a; raport_metodyka rozdz. 10.1

[C17] L209 | pod: ### 2.4. Odcinki terenowe — serie nocne FWD i TSD
źródło: PUB-E §4.7 (estymator: T10, punkt × miesiąc, 5 ≤ T10 < 30 °C); postep_prac.md W1

[C18] L224 | pod: ### 3.1. Cel i zasady
źródło: raport_techniczny_baza_TSD_FWD.md rozdz. 0

[C19] L238 | pod: ### 3.2. Zbiory danych i ich rola w Etapie II
źródło: raport_techniczny rozdz. 0 (tabela zbiorów, liczby z baz), rozdz. 13 (podział na cztery bazy)

[C20] L254 | pod: ### 3.3. Model danych
źródło: raport_techniczny rozdz. 4.1 i 4.2

[C21] L269 | pod: ### 3.4. Potok przetwarzania
źródło: raport_techniczny rozdz. 0, 5, 14, 16

[C22] L280 | pod: ### 3.5. Warstwy danych, wydania i dostęp
źródło: raport_techniczny rozdz. 13, 15.1, 15.2, 17

[C23] L304 | pod: ### 3.6. Detekcja wspólnych odcinków pomiarowych
źródło: raport_metodyka rozdz. 4.2, tabela 2

[C24] L307 | pod: ### 3.6. Detekcja wspólnych odcinków pomiarowych
źródło: raport_metodyka rozdz. 4.3

[C25] L320 | pod: ### 3.7. Weryfikacja odcinek po odcinku
źródło: raport_metodyka rozdz. 6.1, 6.2

[C26] L336 | pod: ### 3.8. Dopasowanie punktowe i jego granice
źródło: SQL P071 (wpis 254, commit ffd2e85): tabele/e2bR9_lustro_warianty.csv (5511 par, 36 sesji, main_after; r_within_session: W5 0,403 — zerowe 0,155 / 0,135 / 0,096; W10 0,511 — 0,150 / 0,153 / 0,087; X_b1510 0,508 — 0,149 / 0,163 / 0,076; C_raw 0,615 — 0,565 / 0,557 / 0,559; X_nom 0,405; median_ratio X_nom 0,523, C_raw 1,063, W5 1,615; pearson_r łącznie X_nom 0,257, X_b1510 0,750), e2bR9_lustro_kalibracja.csv (W5 mnożnik k02: MAE w próbie 27,68 µm, poza próbą 27,74 µm; C_X afiniczna 22,89 / 23,71 µm), e2bR9_lustro_warunki.csv (r Pearsona logarytmów, wszystkie pary warstwy łącznie, bez przedziałów). Sesje 225–227 = fwd_sessions baza_odcinki_v4 (2026-05-18…20; km 43–46 i 6–9,4) — odcinki tsd_2_xml. Sprostowanie DOKTORAT do wpisu 254: udział „artefaktu wygładzania” (ok. 40 %) liczony tam na korelacji łącznej; w obrębie sesji zysk z okna ±10 m jest w całości prawdziwy. Pilotaż GoF: pomysy_idee_plany/etap2_koncepcja_dopasowania.md, rozdz. 2 (wpis 26).

[C27] L337 | pod: ### 3.8. Dopasowanie punktowe i jego granice
źródło: metodyka_zlotych_par.md; W169, W170

[C28] L348 | pod: ### 3.9. Kontrola jakości położenia, czasu i temperatury
źródło: raport_metodyka rozdz. 9.1–9.4, raport_techniczny rozdz. 14, 16.2; W167

[C29] L353 | pod: ### 3.9. Kontrola jakości położenia, czasu i temperatury
źródło: W16, W17, W18; W168

[C30] L360 | pod: ### 3.10. Przedziały kalibracji i przeliczenie ugięć TSD
v1.11 (uwaga Jacka 2026-11-12): eksport nominalny TSD ma kolumny D-450…D1500 — usunięto twierdzenie, że TSD „nie daje D300”. Źródło W91 (rejestr_wnioskow: F1 Lorentz D900/D1500 +106/+197 %, F2 rozciągnięta wykładnicza −51/−78 %; wpisy 105–106), W92 (miary TSD do analiz temperaturowych).

[C31] L370 | pod: ### 3.10. Przedziały kalibracji i przeliczenie ugięć TSD
źródło (v1.11): kod SQL bak/e2a2b_beta.py (CHANNELS_9 bez 1,51 m; dense_integral, INTSTEP 1 mm, P0 / T [e2a_autc_1b.autc_front, slope(0)=0] / PX [od x_max]), bak/e2b2_values.py (sieć: P0 w każdym wierszu, mediana całek w oknie), bak/e2a4b_qa.py i e2a4_dbeta.py (mikroodcinki: p0_a031/a0361/a6191 ↔ SCI300/BDI/BCI), bak/e2aR7_tsd_indices_from_slopes.py i e2bR8_kontrola_E3.py (T). Porównanie z eksportem — obliczenie DOKTORAT 2026-11-12 (tylko odczyt) z bazy bazy/baza_analizy_e2a.db, tabela e2a2_points (d0_b1510off − d300_b1510off, fwd_sci300) i tabele/e2a2_autc_var.csv (p0/t/px_a031), złączenie po odcinek × noc × punkt; ilorazy: eksport/P0 1,247 [1,036; 1,795] n 1253, T/P0 0,904, PX/P0 1,033, FWD/P0 1,131; korelacje log: eksport–P0 0,83, P0–FWD 0,79, eksport–FWD 0,82; niedodatnie: P0 55/1308, T 35/1308, PX 8/1244, eksport 0/1308. Wrażliwości: tabele/e2a2_beta_m8.csv i e2a2_beta_pairs_m8.csv (P029, wpis 114; M8 quasi-Poisson, efekt stały punktu; przedziały różnic 2,5–97,5 percentyl): sci300_fwd 3,694; p0_a031 2,842 (diff [−1,455; +0,058]); px_a031 2,671 ([−1,570; −0,144]); autc_a031 = T 2,623 ([−1,613; −0,230]); sci300_prod_tsd 2,204 ([−1,828; −0,929]). Eksport nominalny: tabele/basin_1510off.csv (d0_export / d0_prod_1510off: mediana 1,258, n 1241). Do potwierdzenia przez SQL przy najbliższym zleceniu.

[C32] L371 | pod: ### 3.10. Przedziały kalibracji i przeliczenie ugięć TSD
źródło: plan_badan_etapy.md (K-dane, wpisy 85–106); W80–W92; raport_techniczny rozdz. 16.1, 20.5

[C33] L380 | pod: ### 3.11. Organizacja pracy i odtwarzalność
źródło: raport_techniczny rozdz. 0, 2, 6, 7, 15.3, 19

[C34] L402 | pod: ### 3.12. Niepewność wyników i jej odporność na metodę wyznaczania
źródło: Z16 (DOKTORAT 5dec2b7, temp_model/output/z16/raport_Z16.md; E3-T59 bootstrap stacjonarny, długość bloku Politis–White 336–440 rekordów; E3-T60 test DM: HAC Bartlett/Andrews na szeregu 10-min i średnie dobowe z poprawką HLN); P068 (SQL 16b93cd, wpis 246: tabele/e2x_niepewnosc_metody.csv, e2x_niepewnosc_werdykty.csv, kontrolne/e2x_synthetic_coverage.csv; M1 = dziki bootstrap klastrowy, wagi Webba, 9999 replik; M2 = CR2 z poprawką Bella–McCaffreya). Jedyny wynik graniczny: Z16, profil stacjonarny TN, test po 7 foldach p = 0,05 (inne warianty p < 0,0001).

[C35] L415 | pod: ## 4. Model temperatury warstw asfaltowych na podstawie danych stacji TN i Podkowa
Źródło całego rozdziału: publikacja_1 v5.3 (załącznik A) §2–4. Liczby jak w załączniku A, tj. na wspólnym
wsparciu czasowym wszystkich modeli (Z8; n = 26 490 TN / 28 348 Podkowa). UWAGA dla Jacka: rozdz07 §7.6 i pamięć projektu
podają starsze wartości headline (np. hybryda B 1,24/0,77, fizyka 1,46/1,06 — TN/Podkowa) liczone bez wspólnego
wsparcia; w raporcie stosujemy wartości z artykułu zgłoszonego do RMPD, żeby raport i załącznik A były zgodne.

[C36] L438 | pod: ### 4.2. Dane
Usunięte z v1.0: „Zgodność obu podstaw czasu sprawdzono korelacją z przesunięciem temperatury powietrza w zakresie ±3 h, osobno dla lata i zimy; optimum wypadło przy przesunięciu zerowym w obu sezonach.” — test wykonano na pobraniu z błędnymi etykietami zimowymi, a mimo to dał zero zimą; do wyjaśnienia (Jacek), nie cytować.

[C37] L529 | pod: ### 4.7. Wyniki
źródło: Z15b (DOKTORAT d5602cd, wymiana/wyniki/raport_PWS/liczby_rozdz4.md): temp_model/output/_omfix_check/E3-T06 + E3-T20 (fold), łańcuch E3 po poprawce etykiet czasu Open-Meteo (Z14d cz. B). Przed poprawką (= publikacja_1 Table 2, zał. A): ML TN 2,44; fizyka TN 1,49; hybryda A TN 1,41; hybryda B 1,26 [1,08; 1,44] / 0,74 [0,62; 0,87]; przewodnictwo TN 0,95 [0,79; 1,11].

[C38] L549 | pod: ### 4.7. Wyniki
źródło: Z15b, temp_model/output/z14lite/z14d/Z15b_T41_robust.csv (z _omfix_check/E3-T07, IV–X, snow=exclude, własna stacja). BELLS3, BELLS3_O, ML (xgb_op, xgb_op_lag): łańcuch nie zapisuje predykcji — brak miar odpornych.

[C39] L555 | pod: ### 4.7. Wyniki
źródło: _omfix_check/E3-T06 (survey, monthly): BELLS3 TN 3,861 / bias −2,871; Podkowa 2,000 / −0,415; BELLS3_O 3,750 / −2,664; 1,567 / −0,082. Ustalenie z Z14-lite (2026-10-31): BELLS3_O nic nie wnosi — odniesieniem jest BELLS3.

[C40] L562 | pod: ### 4.7. Wyniki
źródło: Z16 (DOKTORAT 5dec2b7), temp_model/output/z16/Z16_T1_lato_noc.csv [E3-T58], Z16_T1b_lato_noc_ci.csv (różnica B − fizyka, bootstrap z losowaniem dób: lato TN −0,37 [−0,48; −0,27], Podkowa −0,36 [−0,45; −0,28]; noc TN −0,20 [−0,30; −0,10], Podkowa −0,28 [−0,39; −0,17]; wieczór −0,23 / −0,39; dzień −0,32 / −0,45 — wszystkie istotne). Czas lokalny stanowiska. Liczby publikacji_1 (latem 1,27/1,64 i 0,71/1,04; w nocy 1,05/1,67 i 0,81/1,27) bez zapisanej definicji; Z15b: najbliżej odtwarza je noc 0–6 h z całego roku (TN fizyka 1,64).

[C41] L573 | pod: ### 4.7. Wyniki
źródło: Z15b, _omfix_check/E3-T06 (split = seasonal); przed poprawką: 2,44/1,83 → 3,46/2,61; 1,41/0,87 → 1,96/1,60; 1,49/1,12 → 1,58/1,14; 1,26/0,74 → 1,33/0,82.

[C42] L607 | pod: ### 4.9. Znaczenie dla korekty ugięć
źródło: publikacja_1 §4.4 (tam ilustracyjnie k = 0,02, tj. 2 %/°C); tutaj β D0 = 1,60 %/°C z W136; obliczenie (po poprawce czasu, Z15b): 1,22×1,6 = 1,95; 0,72×1,6 = 1,15; 1,48×1,6 = 2,37; 1,12×1,6 = 1,79; BELLS3: 3,86×1,6 = 6,18; 2,00×1,6 = 3,20; σ = 1,37 % — e2a3_repeatability_v3

[C43] L611 | pod: ### 4.10. Sprawdzenie na odcinkach sieci — temperatura zmierzona sondą
Źródło: DOKTORAT temp_model, Z14-lite → Z14d (raporty `output/z14lite/**/raport_*.md`); liczby z Z14d (E3-T46..T55),
po poprawce etykiet czasu reanalizy. Tabele i rysunki do wygenerowania w wersji PL (E3-F29, E3-F31).

[C44] L639 | pod: ### 4.10. Sprawdzenie na odcinkach sieci — temperatura zmierzona sondą
źródło: E3-T46/T47 (Z14d); mediana i P90: Z15b, temp_model/output/z14lite/z14d/Z15b_T42_robust.csv (bootstrap po sesjach, 2000 replik); kontrola STOP RMSE/MAE/obciążenie zgodne z E3-T46 do 0,001 °C.

[C45] L665 | pod: ### 4.10. Sprawdzenie na odcinkach sieci — temperatura zmierzona sondą
źródło: E3-T53 (Z14d, C v2) — RMSE i przedziały; MAE, mediana, P90: Z15b, temp_model/output/z14lite/z14d/Z15b_T43_robust.csv (kontrola RMSE zgodna z E3-T53 do 0,01 °C). Na stanowiskach modele stanowiskowe z podziału z wyłączonym miesiącem wizyty. Pogrubienie — najlepsza wartość w danym przypadku.

[C46] L672 | pod: ### 4.10. Sprawdzenie na odcinkach sieci — temperatura zmierzona sondą
źródło: E3-T48 (Z14d), wariant wykładniczy β = 0,016.

[C47] L681 | pod: ### 4.10. Sprawdzenie na odcinkach sieci — temperatura zmierzona sondą
Rozstrzygnięte (Jacek 2026-11-06 i 2026-11-09): Tab. 4.1 i liczby 4.7–4.9 po poprawce czasu reanalizy, z przypisem pod Tab. 4.1 (Z15b); liczby „latem/w nocy” — przeliczenie Z16. Liczby publikacji_1 poprawiamy przy odpowiedzi na recenzję.

[C48] L687 | pod: ## 5. Zależność ugięć FWD od temperatury — współczynniki temperaturowe
Źródło rozdziału: materiał publikacja_2 = zrodla/sql_fwd_tsd/monografie/PUB-E_normalizacja_FWD_stacje.md (stan a2440fe);
estymator referencyjny P040 (wpisy 143–145); liczby W102–W140.

[C49] L729 | pod: ### 5.2. Ugięcie D0 i weryfikacja współczynnika k = 0,02
źródło: W136, W137; wpisy 144, 145; tabele e2a3_final_k_profile, e2a3_final_norm_test

[C50] L748 | pod: ### 5.3. Współczynniki temperaturowe wzdłuż czaszy ugięć
źródło: tabele/e2a3_final_k_profile.csv (k_guide), commit a2440fe; Podkowa D900–D1800: przedziały obejmują 0

[C51] L749 | pod: ### 5.3. Współczynniki temperaturowe wzdłuż czaszy ugięć
źródło: W136, wpis 144; e2a3_final_k_profile. Przedziały ufności i wartości osobno dla stanowisk — załącznik C. Współczynniki wskaźników krzywizny (k_guide SCI300/BDI/BCI w e2a3_final_k_profile) usunięte w v1.8 — decyzja Jacka 2026-11-12: najpierw korekta na czujnikach, potem wskaźniki.

[C52] L759 | pod: ### 5.3. Współczynniki temperaturowe wzdłuż czaszy ugięć
źródło: W137; wpis 144; e2a3_final_norm_test (łącznie, cv_month, trend_resid; średnia 9 czujników D0–D1800: i_k02 0,0423 / −1,089; ii_beta_D0 0,0331 / −0,679; iii_beta_own 0,0191 / −0,002; D900–D1800: i_k02 0,0490–0,0526, iii_beta_own 0,0152–0,0189); SCI300 z ugięć skorygowanych: e2aR4_indices_norm (łącznie, R1 0,0939 / +0,430; CB 0,0756 / +0,0068). v1.8: zamiast średniej 12 wielkości, w której wskaźniki korygowano własnym współczynnikiem wskaźnika — jak publikacja_2 §3.3.

[C53] L770 | pod: ### 5.4. Zakres stosowalności korekty
źródło: W115; wpisy 126, 127; e2a3_nonlin

[C54] L773 | pod: ### 5.4. Zakres stosowalności korekty
źródło: e2aR2_rules_bands_R4.csv (D0, R4, łącznie, no_thaw): 0–5 i 5–10 °C n_with_ref 0, 10–15 °C n_with_ref 18 (< 20 — próg pasma); od 15–20 °C n ≥ 108.

[C55] L804 | pod: ### 5.4. Zakres stosowalności korekty
źródło: wiersze „postać liniowa”: e2aR_equivalence.csv (form = guideline, dopasowane k; boot_day) i e2aR4_indices_bands.csv (SCI300 CB guideline, log). Ugięcia D0…D900: tabele/e2aR_equivalence.csv (P049, commit 1c0ccb8; errata — wpis 192), postać wykładnicza, boot_day, band_wide; SCI300/BDI/BCI z ugięć skorygowanych (wariant CB, przyjęty do publikacji_2 — wpis 202): tabele/e2aR4_indices_bands.csv (P052, wpis 201, commity 4618ceb, 55a1871), error_def = log, postać wykładnicza; SCI300 CB 30–35 °C: n = 24 (1 wizyta z SCI300₂₀ ≤ 0 wyłączona; wariant ilorazowy na wszystkich wizytach −12,1 %). Pasmo 30–35 °C: D200 −0,58 [−3,12; +1,20], D600 +0,45 [−2,00; +2,39], D900 +0,95 [−1,44; +2,76]. Mikroodcinki, pasmo 30–35 °C: brak danych. Wyciąg Cowork 2026-11-07. Wiersze „SCI300, własny współczynnik” usunięte w v1.8 (decyzja Jacka 2026-11-12).

[C56] L813 | pod: ### 5.4. Zakres stosowalności korekty
źródło: SQL P070 (wpis 252, commit 66d64b1): tabele/e2bR8_sci_wzmocnienie.csv (25_30_CB łącznie: n 49, A mediana 4,86 — TN 4,97, Podkowa 4,22; średnia e_SCI −6,77, rozkład liczony dla każdej obserwacji w skali log −7,08, R² 0,99; w wersji z A z odniesienia grupy tożsamość dokładna); tabele/e2bR8_ksztalt_czaszy_T.csv (stacje, ln_D300_D0, punkt × miesiąc, węzeł 25 °C, bootstrap po dniach: 5–25 °C −0,46 [−0,58; −0,35], ≥ 25 °C +0,10 [−0,03; +0,32] %/°C; mikroodcinki — kierunek przeciwny, ale grupowanie tylko po odcinku, bez oddzielenia sezonu — nie przyjęto); tabele/e2bR8_mikro_zmiennosc_sci.csv (119 grup odcinek × noc: CV FWD D0 0,108, D300 0,105, SCI300 0,174, korelacja D0–D300 0,958; między nocami po korekcie, 8 odcinków: D0 0,066, SCI300 0,130); C2 i R4 jak w v1.9 (e2aR7_sci_noise_decomp, e2aR7_bands_minn5).

[C57] L816 | pod: ### 5.4. Zakres stosowalności korekty
źródło: e2aR2_rules_bands.csv (P050, commit 7cfe5d1; łącznie, no_thaw, R1 = k 0,02 na każdym czujniku, R2 = k 0,01; przedziały 90 %, bootstrap po dniach): D0 15–20 +0,44 [0,09; 0,76], 20–25 −0,44 [−0,76; −0,08], 25–30 −3,96 [−5,02; −2,87], 30–35 −9,00 [−12,60; −6,11]; D300 15–20 +1,23 [0,61; 1,64], 20–25 −1,20 [−1,55; −0,63], 25–30 −5,83 [−6,85; −4,83], 30–35 −11,39 [−12,60; −9,92]; D900 15–20 +2,99 [1,91; 3,64], 20–25 −2,94 [−3,51; −1,91], 25–30 −11,18 [−12,35; −9,73], 30–35 −20,17 [−22,15; −18,01]; R2 D0 25–30 +3,28 [2,20; 4,17]. Zgodne z publikacją_2 v2.8 Tabela 3.

[C58] L819 | pod: ### 5.4. Zakres stosowalności korekty
źródło: SQL P069 część A (wpis 250, 7c80b5a): tabele/e2aR7_bands_minn5.csv (scope lacznie, band 10_15, n_with_ref 18, n_days 6, n_groups 8; R1: D0 +3,23 [0,96; 4,28], D300 +5,55 [2,30; 6,74], D900 +9,61 [5,67; 11,34], SCI300 −6,71 [−9,63; −2,88]; exp_beta525: D0 +1,81 [−0,20; 2,91], D300 +1,63 [−0,76; 2,69], D900 +0,66 [−1,35; 1,72] — RÓWNOWAŻNE w ±3 %). TN 2, Podkowa 16 obserwacji z odniesieniem.

[C59] L822 | pod: ### 5.4. Zakres stosowalności korekty
źródło: e2aR4_indices_bands.csv (R1 = k 0,02 na każdym czujniku, łącznie, error_def log, przedziały 95 %: SCI300 15–20 −2,69 [−3,99; −1,12], 20–25 +2,64 [1,08; 3,67]; BDI 15–20 −1,99 [−2,77; −1,09], 20–25 +1,95 [1,13; 2,60]); e2a3_final_norm_test.csv (łącznie, SCI300, i_k02, trend_resid +0,430 µm/°C, 5–30 °C); e2aR2_rules_bands_R4.csv (P068b b2fd5ee; R4 / R3a_z_ugiec, SCI300, przedziały 90 %: 15–20 −0,68 [−1,62; +0,40] / −0,64 [−1,55; +0,38]; 20–25 +0,67 [−0,42; +1,48] / +0,63 [−0,40; +1,44]). SCI300 R1 25–30 +3,01 [−2,08; +7,92] (90 %, e2aR4_indices_bands). Zgodne z publikacją_2 v2.8 §3.4 i wnioskiem 3.

[C60] L827 | pod: ### 5.4. Zakres stosowalności korekty
źródło: W122, W132; wpisy 128, 130–133, 191–192; e2a3_range30_v2, e2a3_range30_micro_v2, e2a3_repeatability_v3, e2aR_equivalence; postep_prac.md W2

[C61] L830 | pod: ### 5.4. Zakres stosowalności korekty
źródło: W123; cowork_e2a3_okno_pomiarowe.csv

[C62] L837 | pod: ### 5.5. Sesje poranne i popołudniowe, czas odpowiedzi ugięcia
źródło: W111; wpisy 122–124

[C63] L844 | pod: ### 5.5. Sesje poranne i popołudniowe, czas odpowiedzi ugięcia
źródło: W112; PUB-E §4.6, §5 (plan S vs D)

[C64] L859 | pod: ### 5.6. Wpływ grubości pakietu asfaltowego
W134: nie przypisywać przyczyny wartości α = 0,01 dla autostrad (decyzja Jacka)

[C65] L861 | pod: ### 5.6. Wpływ grubości pakietu asfaltowego
źródło: W121, W130, W131, W134; wpisy 139, 140; e2a3_station_vs_h_harm, e2a3_beta_bands

[C66] L873 | pod: ### 5.6. Wpływ grubości pakietu asfaltowego
źródło: tabele/e2aR_lamb_k_profile.csv, wariant (a) sonda (P049); wpisy 191–193; W173, W174. Wariant z czujnikiem MET-1 (TN) odrzucony — inne warunki termiczne niż w LAMB (sonda LAMB chłodniejsza o 2,7 °C rano i 5,6 °C po południu). Zestawienie z innym wariantem linii (efekt punktu, wszystkie T): 0,19 ± 0,31 %/°C przy 8 cm — LAMB w paśmie; z wariantem 5–30 °C: 0,77 ± 0,37 — LAMB poniżej; nie rozstrzyga (wpis 192).

[C67] L890 | pod: ### 5.7. Stałość współczynnika w ciągu roku i przebieg ugięć skorygowanych
źródło: e2a3_final_seasonal.csv (łącznie, D0, 5_30, iii_beta_own; XI 1,0549 → 1,05 — w v1.0 było 1,06 za monografie/PUB-E §4.5); kwiecień: SQL P067 (wpis 244, commit 8a103be), tabele/kontrolne/e2a3_final_seasonal_april.csv; wiersze f_s jak w publikacji_2 v2.6 Tabela 4 (DSN zał. A tab. 1.2; Graczyk 2008).

[C68] L899 | pod: ### 5.7. Stałość współczynnika w ciągu roku i przebieg ugięć skorygowanych
źródło: W138, W139; wpisy 144, 145; e2a3_final_seasonal, e2a3_final_beta_seasonal*

[C69] L916 | pod: ### 5.8. Głębokość pomiaru temperatury i pomiar na dwóch głębokościach
źródło: publikacja_2 v2.7 §3.6; SQL P053 (e2aR5_depth_dcv) i P054/P054b (wpisy 207–209): tabele/e2aR6_depth_oos.csv (łącznie, Tmid_g, ΔCV poza próbą [%] i przedział 95 %: D300 −13,98 [−32,09; −6,06], D600 −23,86 [−38,84; −15,50], D900 −17,90 [−29,49; −6,64], BCI −24,06 [−29,38; −5,06], D0 −7,40 [−13,58; +16,22], SCI300 +1,74 [−15,83; +8,18]; 20 ziaren: D600 −28,7 … −22,7); tabele/e2aR6_depth_time_split.csv; tabele/e2aR6_depth_probe_oos.csv (TN: D300 −12,8, D900 −14,9, SCI300 −23,0 [−32,8; −1,9]; łącznie D300 −6,0 [−25,0; −3,4]; Podkowa |ΔCV| D0–D900 ≤ 2,9). Przedziały: bootstrap po dniach na wartościach poza próbą, bez ponownego dopasowania.

[C70] L940 | pod: ### 6.1. Wrażliwość temperaturowa ugięć TSD na tle FWD
źródło: SQL P069 część E1 (wpis 250, commit 7c80b5a): tabele/e2aR7_dbeta_slopes.csv (metoda M0 i M1_WCU, kolumny dbeta_lo90/hi90; n, n_nights = 14); β_FWD nachyleń — log e2aR7_tsd_indices_from_slopes.log; kontrola E0: Δβ d0 −0,102 odtworzone z e2a4b_dbeta. Zbiór R1+R6 bez R4 (różnica wobec e2a4b, opisana w wpisie 250). v1.9: zamiast odpowiedników SCI300/BDI/BCI (e2a4b_dbeta: −0,53 / −0,35 / +0,10 %/°C).

[C71] L961 | pod: ### 6.1. Wrażliwość temperaturowa ugięć TSD na tle FWD
źródło: d0 — tabele/e2aR_equivalence.csv (P049, wpis 192) i e2x_tab62_male_klastry.csv (P068b, M1/M2; M3 dla d0: 5 / 10 %); nachylenia — tabele/e2aR7_dbeta_slopes.csv (P069 E2, M0, M1_WCU, M2_CR2). Kanał 0,91 m: werdykt M0 poprawiony w P070 (tabele/e2aR7_dbeta_slopes_v2.csv: brakujący przedział 95 % w M0; teraz ROZNE dla wszystkich δ, zgodnie z M1/M2); kanały 0,11–0,61 m bez zmian. Wariant z losowaniem odcinków pominięty (decyzja Jacka 2026-10-25).

[C72] L964 | pod: ### 6.1. Wrażliwość temperaturowa ugięć TSD na tle FWD
źródło: SQL P068b część A (wpis 248, b2fd5ee), tabele/e2x_tab62_male_klastry.csv: d0 e30 przedziały 90 % M1 [−3,71; +1,74], M2 [−3,45; +1,48], M3 [−4,48; +2,60] → min. δ = 5 we wszystkich; e5 M1 [−2,55; +5,93], M2 [−2,18; +5,41] → δ = 7; M3 WCU [−3,89; +7,03] → δ = 10.

[C73] L967 | pod: ### 6.1. Wrażliwość temperaturowa ugięć TSD na tle FWD
źródło: W146

[C74] L970 | pod: ### 6.1. Wrażliwość temperaturowa ugięć TSD na tle FWD
źródło: W100

[C75] L983 | pod: ### 6.2. Pary pomiarów TSD–FWD na sieci dróg
źródło: SQL P071 (wpis 254, commit ffd2e85): tabele/e2bR9_lustro_warianty.csv (5511 par, 36 sesji, main_after; r_within_session: W5 0,403 — zerowe 0,155 / 0,135 / 0,096; W10 0,511 — 0,150 / 0,153 / 0,087; X_b1510 0,508 — 0,149 / 0,163 / 0,076; C_raw 0,615 — 0,565 / 0,557 / 0,559; X_nom 0,405; median_ratio X_nom 0,523, C_raw 1,063, W5 1,615; pearson_r łącznie X_nom 0,257, X_b1510 0,750), e2bR9_lustro_kalibracja.csv (W5 mnożnik k02: MAE w próbie 27,68 µm, poza próbą 27,74 µm; C_X afiniczna 22,89 / 23,71 µm), e2bR9_lustro_warunki.csv (r Pearsona logarytmów, wszystkie pary warstwy łącznie, bez przedziałów). Sesje 225–227 = fwd_sessions baza_odcinki_v4 (2026-05-18…20; km 43–46 i 6–9,4) — odcinki tsd_2_xml. Sprostowanie DOKTORAT do wpisu 254: udział „artefaktu wygładzania” (ok. 40 %) liczony tam na korelacji łącznej; w obrębie sesji zysk z okna ±10 m jest w całości prawdziwy. Pilotaż GoF: pomysy_idee_plany/etap2_koncepcja_dopasowania.md, rozdz. 2 (wpis 26).

[C76] L986 | pod: ### 6.2. Pary pomiarów TSD–FWD na sieci dróg
źródło: W161, W162, W163, W167, W169, W170; wpisy 176–189

[C77] L990 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: SQL_TSD_FWD P065 (wpis 240, commit e5d6791): tabele/z15_korekta_TSD_FWD_{main,groups,deming,q1q3,conversion}.csv, rysunki plots/e2b/z15_*.png; temperatura T12: DOKTORAT Z15 (E3-T57, temp_model/output/z15/raport_Z15.md, D007), model z rozdz. 4.10 (Z14 v2). Mikroodcinki: obliczenie Cowork 2026-11-07 (tylko odczyt, bez nowego modelu) z tabele/e2a4b_qa_section_night.csv i e2a4b_qa_section.csv (P042 faza A, wpis 155): mediana ilorazu median_fwd_d0 / median_tsd_d0 po 119 kombinacjach odcinek × noc; definicje wielkości sprawdzone w kodzie (FWD D·50/F w p027_e2a2_build / e2b2_values; TSD d0 B_1510off, okno ±5 m). Pearson liczony na logarytmach (e2b2_agreement.point_stats).

[C78] L1026 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: z15_korekta_TSD_FWD_main.csv, wiersze main_before / main_after; mad_log_ratio = 1,4826·MAD. Kolumna „przed” identyczna z e2b2_agreement.csv (rozdz. 6.2). Współczynnika CCC nie podano: mierzy zgodność z linią 1:1, a nie jakość przeliczenia (po korekcie spada 0,42 → 0,35, bo iloraz oddala się od 1).

[C79] L1052 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: z15_korekta_TSD_FWD_groups.csv (device_group: hwd_2024, hwd_2026, old_2024, old_2025, unconfirmed_2026; „old” = 8002-367, „unconfirmed” = 8002-369 wg plik_wymiany_informacji.md: 8082-119/hwd, 8002-367/old, 8002-369/unconfirmed); Q2: z15_korekta_TSD_FWD_q1q3.csv. Rozstęp median w skali log: ln(1,633/0,981) = 0,510 → ln(1,773/1,310) = 0,303.

[C80] L1067 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: z15_korekta_TSD_FWD_main.csv, wiersze *_after (main, bells3, linear, strict_calib, operator_fresh). Wiersz operator_fresh_before w CSV to kopia main_before (n = 5511), nie podzbiór 33 par — nie cytować.

[C81] L1070 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: SQL P066 (wpis 242, commit 3b92044), tabele/z15_krzywizna_TSD_FWD_poziomy.csv, metric = d0, L2/L3, main_after (λ jak na L1; bootstrap po sesjach).

[C82] L1085 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
v1.10: P070 (wpis 252) nie rozstrzygnął wpływu korekty kanał po kanale na iloraz krzywizny: w wariancie kanałowym (c_channel) wielkością FWD jest całka nachyleń FWD (autc_front), a w wariantach bez korekty i metodą §6.3 — D0 − D300, więc rozkład 1,28 → 0,95 miesza zmianę korekty ze zmianą definicji wielkości FWD. Mikroodcinki, ta sama noc: metoda §6.3 1,10, bez korekty 1,09 (mediana ilorazów par, 742 pary, całkowanie trapezowe). Nachylenie Deminga poniżej 1 we wszystkich wariantach skorygowanych. Decyzja: §6.3 bez zmian liczb; dopisana notka o odstępstwie.

[C83] L1113 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: SQL P066 (wpis 242, commity 3b92044, efca1ec): tabele/z15_krzywizna_TSD_FWD_poziomy.csv (main_after), z15_krzywizna_TSD_FWD_q.csv (Q1–Q4). n — pary lub przedziały z dodatnimi wartościami po obu stronach; kolumna „TSD ≤ 0” = share_nonpos_tsd na danym poziomie. Kontrole STOP P066 (d0 jak P065; krzywizny bez korekty jak e2b2_agreement) przeszły.

[C84] L1120 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: P066, tabele/z15_krzywizna_TSD_FWD_mikro.csv; różnica metodyczna (poprawione v1.11 po sprawdzeniu kodu): oba zbiory P0 (PCHIP, dense_integral) — mikroodcinki p0_a031 z e2a2_autc_var przez e2a4b_qa (całka z median nachyleń w oknie), sieć e2b2_values (mediana całek z rekordów); wcześniejszy zapis „mikroodcinki — autc_front” był błędny.

[C85] L1123 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: e2a3_repeatability_v3.csv (SCI300 TN 2,389 %, Podkowa 14,61 %; D0 1,369 / 4,633 %); e2b2_lambda.csv (sigma_tsd a031 0,593, d0 0,296).

[C86] L1130 | pod: ### 6.3. Przeliczanie ugięć TSD na ugięcia FWD
źródło: P066, z15_krzywizna_TSD_FWD_poziomy.csv, sci300 main_after: L1 median 2,2384 [1,99; 2,53]; Deming log-log L1: wyraz wolny 1,96 [1,80; 2,20], nachylenie 0,57 [0,45; 0,63] → exp(1,96) = 7,1; mad_log_ratio 0,80 (1,4826·MAD) → połowa par w ×/÷ exp(0,674·0,80) = 1,72; share_nonpos_tsd L1 po korekcie 0,37; L2 2,29; L3 2,75; mikro 1,28 (inna procedura całkowania). Decyzja Jacka 2026-11-09: przelicznik SCI podać, nawet z dużym błędem.

[C87] L1145 | pod: ### 7.1. Korekta temperaturowa ugięć
źródło: SQL P068b część B (wpis 248, commit b2fd5ee): tabele/e2aR2_rules_bands_R4.csv — reguła R4 = postać liniowa ze stałymi k_guide z e2a3_final_k_profile (D0 0,01611; D300 0,01234; D600 0,00703; D900 0,00329), łącznie, bez roztopów, referencja 15–25 °C w grupie punkt × miesiąc, bootstrap po dniach, przedziały 90 %: D0 15–20 −0,22 [−0,49; +0,09], 20–25 +0,22 [−0,10; +0,49], 25–30 −1,06 [−2,07; −0,05], 30–35 −3,76 [−6,83; −1,20]; D300 15–20/20–25 ±0,09; SCI300 z ugięć 15–20 −0,68 [−1,62; +0,40], 20–25 +0,67 [−0,42; +1,48], 25–30 −6,02 [−12,26; −0,37]. Wariant B ze stałymi β (R3a, e2aR2_rules_bands.csv, no_thaw): D0 25–30 −0,31 [−1,39; +0,63], 30–35 −1,77 [−4,74; +0,76]; SCI300 z ugięć (R3a_z_ugiec, e2aR2_rules_bands_R4.csv) 25–30 −4,13 [−10,30; +1,42].

[C88] L1166 | pod: ### 7.1. Korekta temperaturowa ugięć
źródło: tabele/e2a3_final_k_profile.csv, scope = łącznie (k_guide, beta_pct); jak Tab. 5.1. Na Podkowie k dla D900–D1800 bliskie zeru (przedziały obejmują 0) — wartości łączne dla dalekich czujników mają charakter orientacyjny. Współczynników wskaźników krzywizny nie podaje się (v1.8, rozdz. 5.3): wskaźniki liczy się z ugięć skorygowanych.

[C89] L1168 | pod: ### 7.1. Korekta temperaturowa ugięć
Błędy obu wariantów w paśmie 25–30 °C — z testu zakresu (rozdz. 5.4, Tab. 5.2): współczynniki dopasowane na wizytach 5–25 °C, odniesienie 15–25 °C w grupie punkt × miesiąc (e2aR_equivalence guideline/exponential; e2aR4_indices_bands CB). Tab. 7.1 — współczynniki z dopasowania 5–30 °C (Tab. 5.1); w teście zakresu postać liniowa miała k dopasowane na 5–25 °C (łącznie 0,0175, e2a3_range30_v2), a nie stałe 0,016 — wynik dla stałych k z Tab. 7.1 (wariant A dosłownie, reguła R4): P068b część B, opisany w akapicie wariantu A.

[C90] L1215 | pod: ### 7.3. Przetwarzanie pomiarów TSD na sieci
źródło p. 7: C:\WORK\DOKTORAT\tsd_2_xml (README_workflow.md, tsd_pipeline.py, calibrate_conversion.py, compare_tsd_fwd.py; stan 2026-07-01): czasza „D Tkor” z pliku 1 m — BELLS3_BT + k = 0,02 (informacja Jacka 2026-11-13), Hampel na D0 + średnia ±10 m, konwersja afiniczna DK50 a 0,849 b +24,35, S8 a 0,473 b +41,72; dopasowanie „value ±5 m” w compare_tsd_fwd.py.

[C91] L1249 | pod: ## 9. Podsumowanie i wnioski
Rejestr językowy: wnioski „ludzkim” językiem (pamięć projektu: preferences) — czytelnik to inżynier drogowy.

[C92] L1270 | pod: ## Literatura
strona 44 wg publikacji_2 v2.6, poz. [1]; atrybucja wzoru do KWRNPP-2001 wg sprawozdania IBDiM TD-67/2004, 2006.

[C93] L1283 | pod: ## Literatura
[5] (dawniej [3]): rok 2024 potwierdzony przez autora 2026-11-09 (data publikacji 2024-03-30). W publikacji_1 v5.3 podano 2023 — do poprawy przy najbliższej wersji; w publikacji_2 poprawione w v2.7 (2026-11-11).

[C94] L1300 | pod: ## Literatura
[18]–[25]: Webb [24] potwierdzony 2026-11-09 (vLex/EconBiz); pozostałe — opisy standardowe, do sprawdzenia DOI przed wersją końcową (skill naukowa-publikacja). Numeracja [18]–[25] po [17], choć w tekście (rozdz. 3.12) cytowane wcześniej — przy redakcji końcowej przenumerować w kolejności cytowania.

[C95] L1320 | pod: ## Literatura
v1.5 (2026-11-09): numeracja w kolejności pierwszego cytowania (wcześniej [14]–[25] poza kolejnością; komentarze z historią wersji w nagłówku i przy akapitach zachowują dawne numery). Opisy [9]–[16] (dawne [18]–[25]) zweryfikowane 2026-11-09: Politis–Romano — Crossref; Politis–White, Patton–Politis–White, Harvey i in., Cameron i in. — RePEc/IDEAS/EconPapers; Diebold–Mariano — Scilit; Webb — vLex/EconBiz; Bell–McCaffrey — katalog StatCan 12-001-X20020029058.
