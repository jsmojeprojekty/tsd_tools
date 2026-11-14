"""Katalog flag jakosci (rejestr oznaczen zamiast usuwania rekordow).

Flagi sa maska bitowa (IntFlag) i tekstem rozdzielonym srednikami ('flags_text')."""

from __future__ import annotations

import enum

import numpy as np


class Flag(enum.IntFlag):
    NONE = 0
    T_MISSING = 1 << 0           # brak temperatury
    T_BELOW_5C = 1 << 1          # T < 5 C: korekta nie ma zastosowania (stan podloza), ugiecia skorygowane puste
    T_ABOVE_RANGE = 1 << 2       # T powyzej zakresu waznosci wariantu (korekta wykonana, wynik oznaczony)
    T_CARRIED = 1 << 3           # temperatura przeniesiona z wczesniejszej stacji (nie swiezy wpis)
    T_ENTRY_POSSIBLE = 1 << 4    # niepewny wpis (duzy odstep czasu bez zmiany wartosci)
    T_PLACEHOLDER = 1 << 5       # wartosc zastepcza aparatu (np. 20,4 C)
    T_STALE = 1 << 6             # wpis starszy niz dopuszczalny wiek
    T_SENTINEL = 1 << 7          # wypelniacz eksportu (np. -3,4e38) potraktowany jako brak
    INDEX_ABOVE_RANGE = 1 << 8   # SCI300/BDI/BCI przy T powyzej limitu wskaznikow
    INDEX_NONPOSITIVE = 1 << 9   # wskaznik po korekcie <= 0
    FORCE_OFF_NOMINAL = 1 << 10  # sila zrzutu poza tolerancja wzgledem 50 kN
    NO_NONSEATING_DROP = 1 << 11 # brak zrzutu nieosadczego (dane zrzutu puste)
    THICKNESS_OUT_OF_RANGE = 1 << 12  # grubosc pakietu poza 15-30 cm (zakres wazny dla wspolczynnikow)
    LEGACY_RULE = 1 << 13        # wynik wzoru dotychczasowego (tryb porownawczy)
    GEOPHONE_MISSING = 1 << 14   # brak co najmniej jednego czujnika w ukladzie sesji


def flags_to_text(mask: int) -> str:
    """Maska -> tekst 'A;B;C' (kolejnosc wg numeru bitu); pusty dla 0."""
    mask = int(mask)
    names = [f.name for f in Flag if f.name != "NONE" and mask & f.value]
    return ";".join(names)


def flags_series_to_text(masks) -> list[str]:
    return [flags_to_text(m) for m in np.asarray(masks, dtype=np.int64)]
