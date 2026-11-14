"""Flagi jakosci N3 (rejestr oznaczen zamiast usuwania rekordow)."""

from __future__ import annotations

import enum


class TsdFlag(enum.IntFlag):
    NONE = 0
    T_MISSING = 1 << 0               # brak temperatury warstwy: d0 bez korekty
    T_BELOW_5C = 1 << 1              # T12 < 5 C: korekta nie ma zastosowania
    T_ABOVE_RANGE = 1 << 2           # T12 > 30 C: korekta wykonana, wynik oznaczony
    D0_INVALID = 1 << 3              # brak d0 lub d0 <= 0
    D0_HAMPEL_REJECTED = 1 << 4      # outlier d0 (filtr Hampela): odrzucona cala czasza
    SLOPE_MISSING = 1 << 5           # brak co najmniej jednego z 9 nachylen (calki puste)
    P0_UNCORRECTED = 1 << 6          # calki P0 bez korekty temperaturowej (raport 6.1)
    INTEGRAL_NONPOSITIVE = 1 << 7    # calka P0 <= 0 (SCI/BDI/BCI TSD <= 0)
    WINDOW_FEW_ROWS = 1 << 8         # w oknie mniej niz min_rows wierszy z waznym d0
    LOW_GOF_SHARE = 1 << 9           # udzial czasz GoF >= 0,5 w oknie < 50 %
    GPS_INVALID = 1 << 10            # brak/zerowa pozycja GPS
    FILE_NOT_RECALIBRATED = 1 << 11  # pusty 'Re-calibrationfile' (nie jest to eksport B_1510off)
    FILE_MISSING_CHANNEL = 1 << 12   # brak kanalu nachylen
    FILE_SCALE_SUSPECT = 1 << 13     # krok pikietazu odbiega od 1 m (blad skali pikietazu)
    FILE_YEAR_OUT_OF_RANGE = 1 << 14 # rok przejazdu przed 2024 (B_1510off dotyczy 2024-2026)
    GYRO_GPS_NOT_OK = 1 << 15        # test zyroskop-GPS: przesuniecie lub brak rozstrzygniecia
    SCALE_FWD_UNVERIFIED = 1 << 16   # wartosc przeliczona mnoznikiem na skale FWD (dla D_200, D_300 niezweryfikowane)


def flags_to_text(mask: int) -> str:
    mask = int(mask)
    return ";".join(f.name for f in TsdFlag if f.name != "NONE" and mask & f.value)
