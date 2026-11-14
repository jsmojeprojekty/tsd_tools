"""Tabele wspolczynnikow korekty temperaturowej (k wariantu A, beta wariantu B) dla czujnikow FWD."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from importlib import resources

from .constants import GEOPHONES, LEGACY_K

COEFFICIENT_SETS = ("e2a3_full", "tab71")


@dataclass(frozen=True)
class CoefficientTable:
    """Wspolczynniki indeksowane nazwa czujnika (D0..D1800); k w [1/C], beta w [1/C] (beta_pct/100)."""

    name: str
    _k: dict
    _beta: dict
    meta: dict = field(default_factory=dict)

    def k(self, indicator: str) -> float:
        return self._lookup(self._k, indicator)

    def beta(self, indicator: str) -> float:
        return self._lookup(self._beta, indicator)

    def _lookup(self, table: dict, indicator: str) -> float:
        if indicator not in table:
            raise KeyError(f"brak wspolczynnika dla {indicator!r} w zestawie {self.name!r}")
        return table[indicator]

    def indicators(self) -> tuple:
        return tuple(self._k)


def _read_csv(filename: str) -> list[dict]:
    with resources.files("tsdfwd_tools.data").joinpath(filename).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_coefficients(set_name: str = "e2a3_full", scope: str = "lacznie") -> CoefficientTable:
    """Wczytuje zestaw wspolczynnikow z danych pakietu.

    e2a3_full: pelna precyzja z e2a3_final_k_profile.csv (dopasowanie 5 <= T < 30 C, T_mid z czujnikow), zbior `scope`.
    tab71: Tab. 7.1 raportu (wartosci zaokraglone)."""
    if set_name == "e2a3_full":
        rows = [r for r in _read_csv("e2a3_final_k_profile.csv") if r["scope"] == scope]
        k = {r["indicator"]: float(r["k_guide"]) for r in rows}
        beta = {r["indicator"]: float(r["beta_pct"]) / 100.0 for r in rows}
        n = {int(r["n"]) for r in rows}
        meta = {
            "set": set_name,
            "scope": scope,
            "fit_range_c": "5 <= T < 30",
            "n_visits": sorted(n)[0] if len(n) == 1 else sorted(n),
            "source": "sql_tsd_fwd/tabele/e2a3_final_k_profile.csv (P040)",
        }
    elif set_name == "tab71":
        rows = _read_csv("tab71.csv")
        k = {r["indicator"]: float(r["k"]) for r in rows}
        beta = {r["indicator"]: float(r["beta_pct"]) / 100.0 for r in rows}
        meta = {"set": set_name, "source": "raport PW.S-1063 v1.12, Tab. 7.1 (wartosci zaokraglone)"}
    else:
        raise ValueError(f"nieznany zestaw wspolczynnikow: {set_name!r} (dozwolone: {', '.join(COEFFICIENT_SETS)})")
    missing = [g for g in GEOPHONES if g not in k]
    if missing:
        raise ValueError(f"zestaw {set_name!r} nie zawiera czujnikow: {missing}")
    return CoefficientTable(name=set_name, _k=k, _beta=beta, meta=meta)


def legacy_table(road_type: str) -> CoefficientTable:
    """Dotychczasowy wzor krajowy: jeden wspolczynnik k na kazdym czujniku (0,02 droga publiczna, 0,01 autostrada)."""
    if road_type not in LEGACY_K:
        raise ValueError(f"nieznany typ drogi: {road_type!r} (dozwolone: {', '.join(LEGACY_K)})")
    k = {g: LEGACY_K[road_type] for g in GEOPHONES}
    meta = {
        "set": f"legacy_{road_type}",
        "source": "tryb porownawczy; k=0,02 (droga publiczna) / k=0,01 (autostrada) wg kodu TSDLayerIQ, "
                  "brzmienie przepisu niezweryfikowane",
    }
    return CoefficientTable(name=f"legacy_{road_type}", _k=k, _beta={g: 0.0 for g in GEOPHONES}, meta=meta)
