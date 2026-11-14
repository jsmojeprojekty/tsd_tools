"""Eksport XML w formacie DSN `UC` (zalacznik H, p. 4.2: ugiecia - pomiar mobilny TSD) oraz kontrola struktury pliku.

Profil `dsn_h42` (21 pol, kolejnosc jak w zalaczniku): KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1,
PREDKOSC, STRAIN_GAUGE, T_DROGI, T_POW, SCI_200, SCI_300, SCI_SUB, D_0, D_200, D_300. Atrybuty korzenia: KOD_ODDZ, ROK,
xsi:noNamespaceSchemaLocation (UC_Schema.xsd). Pola typu 'decimal-or-empty': brak wartosci = pusty element `<TAG></TAG>`
(nigdy 'nan'). Uklad pliku jak w produkcji (tsd_to_xml.py): UTF-8 bez BOM, LF, wciecia 4/8 spacji, atrybuty korzenia w osobnych
liniach; precyzje: KM 3, DYSTANS 0, LAT/LON 6, IRI/PROFIL/PREDKOSC 6, STRAIN_GAUGE 3, T_* 1, SCI_*/D_* 3.
zrodlo ukladu: C:\\WORK\\DOKTORAT\\tsd_2_xml\\tsd_to_xml.py (stan 2026-07-01); definicja pol: inne\\DSN_Zal.H.pdf p. 4.2."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

FIELDS_H42 = ("KM", "DYSTANS", "DROGA", "JEZDNIA", "PAS", "LAT", "LON", "DATA", "GODZ", "IRI_1", "PROFIL_1", "PREDKOSC",
              "STRAIN_GAUGE", "T_DROGI", "T_POW", "SCI_200", "SCI_300", "SCI_SUB", "D_0", "D_200", "D_300")
DECIMALS = {"KM": 3, "LAT": 6, "LON": 6, "IRI_1": 6, "PROFIL_1": 6, "PREDKOSC": 6, "STRAIN_GAUGE": 3, "T_DROGI": 1,
            "T_POW": 1, "SCI_200": 3, "SCI_300": 3, "SCI_SUB": 3, "D_0": 3, "D_200": 3, "D_300": 3}
INTEGER_FIELDS = ("DYSTANS", "JEZDNIA", "PAS")
TEXT_FIELDS = ("DROGA", "DATA", "GODZ")
ALWAYS_EMPTY_OK = ("IRI_1", "PROFIL_1")
DECIMAL_GROUP = ("SCI_200", "SCI_300", "SCI_SUB", "D_0", "D_200", "D_300")
_NUM_RE = {
    "KM": r"-?\d+\.\d{3}", "LAT": r"-?\d+\.\d{6}", "LON": r"-?\d+\.\d{6}", "IRI_1": r"-?\d+\.\d{6}", "PROFIL_1": r"-?\d+\.\d{6}",
    "PREDKOSC": r"-?\d+\.\d{6}", "STRAIN_GAUGE": r"-?\d+\.\d{3}", "T_DROGI": r"-?\d+\.\d", "T_POW": r"-?\d+\.\d",
    "SCI_200": r"-?\d+\.\d{3}", "SCI_300": r"-?\d+\.\d{3}", "SCI_SUB": r"-?\d+\.\d{3}", "D_0": r"-?\d+\.\d{3}",
    "D_200": r"-?\d+\.\d{3}", "D_300": r"-?\d+\.\d{3}", "DYSTANS": r"-?\d+", "JEZDNIA": r"\d+", "PAS": r"\d+",
}


def format_value(tag: str, value) -> str:
    """Wartosc pola jako tekst o stalej precyzji; None/NaN -> pusty napis."""
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    if isinstance(value, (np.floating,)) and not np.isfinite(value):
        return ""
    if tag in TEXT_FIELDS:
        return str(value)
    if tag in INTEGER_FIELDS:
        try:
            return str(int(round(float(value))))
        except (TypeError, ValueError):
            return ""
    if tag in DECIMALS:
        return f"{float(value):.{DECIMALS[tag]}f}"
    return str(value)


def write_uc_xml(path, records: pd.DataFrame, kod_oddz: str, rok, schema_location: str = "UC_Schema.xsd",
                 fields=FIELDS_H42) -> int:
    """Zapisuje plik UC; records: DataFrame z kolumnami o nazwach pol (brakujace kolumny = puste elementy). Zwraca liczbe rekordow."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<UC xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
             f'    KOD_ODDZ="{escape(str(kod_oddz), {chr(34): "&quot;"})}"',
             f'    ROK="{escape(str(rok), {chr(34): "&quot;"})}"',
             f'    xsi:noNamespaceSchemaLocation="{escape(schema_location, {chr(34): "&quot;"})}">']
    for row in records.to_dict("records"):
        lines.append("    <DANE>")
        for tag in fields:
            lines.append(f"        <{tag}>{escape(format_value(tag, row.get(tag)))}</{tag}>")
        lines.append("    </DANE>")
    lines.append("</UC>")
    Path(path).write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return len(records)


def validate_uc_structure(path, fields=FIELDS_H42, step_m: int | None = 10) -> list:
    """Kontrola struktury pliku UC (niezalezna od wartosci). Zwraca liste bledow (pusta = zgodny)."""
    errors = []
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("plik zaczyna sie od BOM")
    if b"\r\n" in raw:
        errors.append("konce linii CRLF (oczekiwano LF)")
    if not raw.endswith(b"\n"):
        errors.append("brak konca linii na koncu pliku")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return errors + [f"plik nie jest poprawnym XML: {exc}"]
    if root.tag != "UC":
        errors.append(f"element glowny {root.tag!r} zamiast 'UC'")
    for attr in ("KOD_ODDZ", "ROK"):
        if attr not in root.attrib:
            errors.append(f"brak atrybutu korzenia {attr}")
    if not any(k.endswith("noNamespaceSchemaLocation") for k in root.attrib):
        errors.append("brak xsi:noNamespaceSchemaLocation")
    dystans, km = [], []
    for i, dane in enumerate(root):
        if dane.tag != "DANE":
            errors.append(f"rekord {i}: element {dane.tag!r} zamiast 'DANE'")
            continue
        tags = [c.tag for c in dane]
        if tags != list(fields):
            errors.append(f"rekord {i}: zla kolejnosc lub zestaw pol: {tags}")
            continue
        vals = {c.tag: (c.text or "") for c in dane}
        if any("nan" in v.lower() or "inf" in v.lower() for v in vals.values()):
            errors.append(f"rekord {i}: wartosc nan/inf w tekscie")
        for tag, v in vals.items():
            if v == "":
                if tag in DECIMALS or tag in ("DYSTANS", "JEZDNIA", "PAS"):
                    continue          # pola 'decimal-or-empty'/'integer-or-empty'
                if tag in ("DROGA", "DATA", "GODZ"):
                    errors.append(f"rekord {i}: puste pole obowiazkowe {tag}")
                continue
            if tag in _NUM_RE and not re.fullmatch(_NUM_RE[tag], v):
                errors.append(f"rekord {i}: {tag}={v!r} nie pasuje do formatu")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", vals["DATA"]):
            errors.append(f"rekord {i}: DATA={vals['DATA']!r}")
        if not re.fullmatch(r"\d{2}:\d{2}:\d{2}", vals["GODZ"]):
            errors.append(f"rekord {i}: GODZ={vals['GODZ']!r}")
        if vals["DYSTANS"]:
            dystans.append(int(vals["DYSTANS"]))
        if vals["KM"]:
            km.append(float(vals["KM"]))
    if step_m and len(dystans) > 1:
        d = np.diff(dystans)
        if not (d > 0).all():
            errors.append("DYSTANS nie jest rosnacy")
        elif not (d == step_m).all():
            errors.append(f"DYSTANS: krok rozny od {step_m} m")
    if len(km) > 2:
        dk = np.diff(km)
        if not (np.all(dk > 0) or np.all(dk < 0)):
            errors.append("KM nie jest monotoniczne")
    return errors
