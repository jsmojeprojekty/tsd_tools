"""Flagi jakosci N2 (rejestr oznaczen zamiast usuwania rekordow)."""

from __future__ import annotations

import enum


class LayerFlag(enum.IntFlag):
    NONE = 0
    NIGHT = 1 << 0                   # SW_ma6 < 5 W/m2: kalibracja do pirometru nie dziala (brak sygnalu slonecznego)
    OUT_OF_SEASON = 1 << 1           # miesiac poza sezonem walidacji (IV-X)
    SNOW = 1 << 2                    # pokrywa sniegu wg reanalizy > prog
    METEO_GAP = 1 << 3               # luka w danych meteo w oknie symulacji lub brak danych: wynik niepewny albo NaN
    TAIL_EXTRAPOLATED = 1 << 4       # chwila pomiaru za ostatnia godzina pobranych danych (stala ekstrapolacja)
    CALIB_GATE = 1 << 5              # kalibracja nieidentyfikowalna (|Ts(a=1) - Ts(a=0,03)| < 1 C): a_sw domyslne
    CALIB_BOUND_HI = 1 << 6          # a_sw na gornej granicy (1,0): pirometr cieplejszy niz model
    CALIB_BOUND_LO = 1 << 7          # a_sw na dolnej granicy (0,03)
    CALIB_NOSIM = 1 << 8             # brak symulacji (dane meteo niewystarczajace): wynik NaN
    IR_MISSING = 1 << 9              # brak odczytu pirometru: wartosc z fizyki bez kalibracji
    CALIB_OFF = 1 << 10              # kalibracja wylaczona w konfiguracji (calibration: none)
    DEPTH_NOT_VALIDATED = 1 << 11    # glebokosc inna niz zwalidowane 10 i 12 cm
    DEPTH_OUT_OF_RANGE = 1 << 12     # glebokosc poza 0-50 cm: wynik NaN
    SHADED_SITE_SUSPECTED = 1 << 13  # zarezerwowane (Q-N2-7): zacienienie nie jest wykrywane, model TN ma tam bias +3..+5 C
    POSITION_OUT_OF_POLAND = 1 << 14 # pozycja poza obszarem Polski (model kalibrowany dla klimatu Polski)


def flags_to_text(mask: int) -> str:
    mask = int(mask)
    return ";".join(f.name for f in LayerFlag if f.name != "NONE" and mask & f.value)
