"""Stale modelu temperatury warstwy asfaltowej N2 (fizyka 1D + kalibracja jednorazowa do pirometru).

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src: energy_balance_bc.py (EPS_SURF, SIGMA, KELVIN, PARAM_SPEC), calibrate_alpha.py
(DT_S, DZ, NZ), operational_bc.py (SPINUP_OP), z14lite_validate.py (HIST_DAYS, SIM_LEAD_DAYS, GRID_DEG), z14b_single_shot.py
(GATE_C, XTOL, A_LO, A_HI), stan 2026-11-13."""

from __future__ import annotations

import pandas as pd

PROTOCOL_VERSION = "z14d_H_v2_single_shot_masa"

# siatka numeryczna i krok czasowy
DZ_M = 0.01
NZ = 51                          # wezly 0-50 cm co 1 cm
DEPTH_MAX_M = 0.50
DT_S = 600.0                     # krok 10 min
STEP = pd.Timedelta(minutes=10)
SPINUP_STEPS = 288               # rozbieg 2 doby (wyniki NaN)
LEAD_DAYS = 3                    # start symulacji przed dniem pomiaru
HIST_DAYS = 35                   # historia meteo (MA30 + zapas)
GRID_DEG = 0.05                  # zaokraglenie wspolrzednych zapytania do komorki reanalizy

# fizyka
EPS_SURF = 0.95
SIGMA = 5.67e-8
KELVIN = 273.15
SNOW_MAX_M = 0.005

# kalibracja jednorazowa a_sw do pirometru
A_LO, A_HI = 0.03, 1.0
GATE_C = 1.0                     # bramka identyfikowalnosci [C]: |Ts(a=1) - Ts(a=0,03)| < 1 C -> a_sw domyslne
XTOL = 1e-3

# Open-Meteo (jedyne dopuszczalne polaczenie sieciowe)
OM_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OM_HOURLY = ("temperature_2m", "dew_point_2m", "wind_speed_10m", "cloud_cover", "shortwave_radiation", "snow_depth")
OM_TIMEZONE_QUERY = "UTC"        # OBOWIAZKOWO: timezone=Europe/Warsaw przesuwa etykiety o ~1 h (erratum 2026-11-04)
LOCAL_TZ = "Europe/Warsaw"
SLEEP_S = 2.0
MAX_RETRY = 5
RETRY_WAIT_S = 60.0
MERGE_GAP_DAYS = 10

# niepewnosc: u95 = +-2*RMSE wg pory (zbior H v2), nie mniej niz dolna granica metody pomiaru
RMSE_BY_HOUR_BIN = {(0, 6): 2.167, (6, 12): 1.378, (12, 18): 1.889, (18, 24): 2.167}
U95_MIN_C = 2.2
