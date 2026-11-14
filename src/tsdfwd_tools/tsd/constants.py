"""Stale narzedzia N3 (TSD, eksport B_1510off).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a2b_beta.py (CHANNELS_9, X_POS, XS_SORTED, STAGES, INTSTEP),
w2_euler.py (SLOPE_COL, D_COLS), e2a_autc_1b.py (GOF_MIN), stan c67f7fe / 2026-10-13."""

from __future__ import annotations

# 9 kanalow nachylen BEZ czujnika 1,51 m; kolejnosc = polozenie rosnaco [m] od osi kola (znak: tyl ujemne)
CHANNELS_9 = ("m450", "m300", "m200", "0110", "0210", "0310", "0460", "0610", "0910")
XS_SORTED = (-0.450, -0.300, -0.200, 0.110, 0.210, 0.310, 0.460, 0.610, 0.910)
CHANNEL_X = dict(zip(CHANNELS_9, XS_SORTED))

# kolumny eksportu B_1510off (po zdjeciu jednostek)
SLOPE_COL = {
    "1510": "Slope 1.510", "0910": "Slope 0.910", "0610": "Slope 0.610", "0460": "Slope 0.460", "0310": "Slope 0.310",
    "0210": "Slope 0.210", "0110": "Slope 0.110", "m200": "Slope -0.200", "m300": "Slope -0.300", "m450": "Slope -0.450",
}
D_COLS = ("D-450", "D-300", "D-200", "D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500")

INTSTEP_M = 0.001                       # krok siatki calkowania (1 mm)
GOF_MIN = 0.5                           # prog GoF dla atrybutu okna (udzial czasz GoF >= 0,5)
HAMPEL_WINDOW_ROWS_DEFAULT = 21         # okno Hampela: 21 wierszy = +-10 m przy kroku 1 m
HAMPEL_K = 3.0
MAD_SCALE = 1.4826

# punkty, do ktorych calkowane jest nachylenie od osi kola [m]
# 0,31 / 0,61 / 0,91 = polozenia czujnikow TSD (SCI300_TSD, BDI_TSD, BCI_TSD); 0,20 / 0,30 / 0,90 = odleglosci D_200, D_300, D_900
INTEGRAL_TARGETS_M = (0.20, 0.30, 0.31, 0.61, 0.90, 0.91)
INTEGRAL_NAMES = {0.20: "a020", 0.30: "a030", 0.31: "a031", 0.61: "a061", 0.90: "a090", 0.91: "a091"}

MIN_YEAR_B1510OFF = 2024                # B_1510off dotyczy przejazdow 2024-2026 (wczesniejsze lata: invalid_scale, itd.)
