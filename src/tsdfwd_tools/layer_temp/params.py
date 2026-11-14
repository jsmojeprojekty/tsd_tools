"""Parametry zamrozone N2 (plik JSON z hashem zrodla) — zmiana parametrow zmienia hash i wyniki (test dryfu)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

import numpy as np

from .constants import A_HI, A_LO

# SHA-256 sekcji "parameters" wbudowanego params_TN.json (kanoniczny JSON, klucze posortowane). Zmiana parametrow zmienia wyniki:
# test dryfu (tests/unit/test_n2_units.py) pada, dopoki wartosc nie zostanie swiadomie zaktualizowana wraz z wpisem w DZIENNIK.md.
EXPECTED_BUILTIN_HASH = "36780ba8771c504f8d5aa40419f68a3c08d99a15e859f76396a68aa5613f4d04"


@dataclass(frozen=True)
class FrozenParams:
    name: str
    alpha: float
    eb: dict
    beta50: np.ndarray
    beta_ir: np.ndarray
    a_bounds: tuple
    hash: str
    meta: dict = field(default_factory=dict)

    @property
    def a_default(self) -> float:
        return float(self.eb["a_sw"])


def _hash_parameters(parameters: dict) -> str:
    canon = json.dumps(parameters, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def load_params(path=None) -> FrozenParams:
    """Wczytuje parametry zamrozone (domyslnie wbudowane `params_TN.json`)."""
    if path is None or str(path) == "builtin:params_TN.json":
        raw = resources.files("tsdfwd_tools.data").joinpath("params_TN.json").read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    doc = json.loads(raw)
    p = doc["parameters"]
    for key in ("alpha_m2_s", "eb", "beta50", "beta_ir"):
        if key not in p:
            raise ValueError(f"params: brak klucza {key!r}")
    eb = dict(p["eb"])
    for key in ("a_sw", "h0", "h1", "c_vol", "svf"):
        if key not in eb:
            raise ValueError(f"params: brak parametru EB {key!r}")
    bounds = doc.get("bounds", {}).get("a_sw", [A_LO, A_HI])
    return FrozenParams(
        name=doc.get("name", "params"), alpha=float(p["alpha_m2_s"]), eb=eb,
        beta50=np.asarray(p["beta50"], float), beta_ir=np.asarray(p["beta_ir"], float),
        a_bounds=(float(bounds[0]), float(bounds[1])), hash=_hash_parameters(p),
        meta={"description": doc.get("description"), "source": doc.get("source")})
