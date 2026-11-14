import importlib.util
from pathlib import Path

import numpy as np
import pytest

from tsdfwd_tools.common.coefficients import legacy_table, load_coefficients
from tsdfwd_tools.common.constants import GEOPHONES
from tsdfwd_tools.common.rules import CorrectionForm, apply_correction, factor

REF = Path(__file__).resolve().parents[1] / "data" / "ref_apply_rule.py"


def _load_ref():
    spec = importlib.util.spec_from_file_location("ref_apply_rule", REF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# T-N1-02: wzory analitycznie (wspolczynniki Tab. 7.1: D0 k=0,016 / beta=1,60 %/C; D300 k=0,012 / 1,22 %/C)
@pytest.mark.parametrize("temp, a_exp, b_exp", [
    (5.0, 248.000, 254.250), (10.0, 232.000, 234.702), (25.0, 184.000, 184.623), (30.0, 168.000, 170.429)])
def test_d0_values_variant_a_and_b(temp, a_exp, b_exp):
    a = apply_correction(200.0, temp, CorrectionForm.LINEAR, 0.016)
    b = apply_correction(200.0, temp, CorrectionForm.EXPONENTIAL, 0.016)
    assert a == pytest.approx(a_exp, abs=1e-3)
    assert b == pytest.approx(b_exp, abs=1e-3)


def test_d300_values():
    assert apply_correction(150.0, 10.0, CorrectionForm.LINEAR, 0.012) == pytest.approx(168.000, abs=1e-3)
    assert apply_correction(150.0, 10.0, CorrectionForm.EXPONENTIAL, 0.0122) == pytest.approx(169.463, abs=1e-3)
    assert apply_correction(150.0, 30.0, CorrectionForm.LINEAR, 0.012) == pytest.approx(132.000, abs=1e-3)
    assert apply_correction(150.0, 30.0, CorrectionForm.EXPONENTIAL, 0.0122) == pytest.approx(132.772, abs=1e-3)


@pytest.mark.parametrize("form", [CorrectionForm.LINEAR, CorrectionForm.EXPONENTIAL])
def test_identity_at_reference_temperature_and_round_trip(form):
    y = np.array([50.0, 123.4, 400.0])
    assert apply_correction(y, 20.0, form, 0.0161) == pytest.approx(y, abs=1e-12)
    t = np.array([7.0, 12.5, 24.0])
    back = apply_correction(apply_correction(y, t, form, 0.0161), t, form, -0.0161) if form is CorrectionForm.LINEAR \
        else apply_correction(apply_correction(y, t, form, 0.0161), t, form, -0.0161)
    # exp: f(beta)*f(-beta) = 1; liniowo: odwracalnosc przez 1/f
    if form is CorrectionForm.EXPONENTIAL:
        assert back == pytest.approx(y, abs=1e-9)
    corrected = apply_correction(y, t, form, 0.0161)
    assert corrected / factor(t, form, 0.0161) == pytest.approx(y, abs=1e-9)


def test_unknown_form_raises():
    with pytest.raises(ValueError):
        factor(10.0, "guideline", 0.02)  # w zrodle: ciche przejscie na postac wykladnicza
    assert CorrectionForm.parse("EXPONENTIAL") is CorrectionForm.EXPONENTIAL


# T-N1-03: zgodnosc z apply_rule z projektu bazy (kopia kodu zrodlowego) do 1e-9
@pytest.mark.parametrize("param", [0.0161092, 0.0123428, 0.00328817, 0.02, 0.01])
def test_matches_source_apply_rule(param):
    ref = _load_ref()
    rng = np.random.default_rng(20261114)
    y = rng.uniform(20, 600, 200)
    t = rng.uniform(-5, 38, 200)
    assert apply_correction(y, t, CorrectionForm.LINEAR, param) == pytest.approx(
        ref.apply_rule(y, t, "guideline", param), abs=1e-9, rel=0)
    assert apply_correction(y, t, CorrectionForm.EXPONENTIAL, param) == pytest.approx(
        ref.apply_rule(y, t, "exponential", param), abs=1e-9, rel=0)


# T-N1-01: wspolczynniki scope lacznie z e2a3_final_k_profile.csv (dane pakietu)
E2A3_LACZNIE = {
    "D0": (0.0161092, 1.60415), "D200": (0.0140162, 1.38103), "D300": (0.0123428, 1.21602),
    "D450": (0.00958895, 0.954185), "D600": (0.00702971, 0.70652), "D900": (0.00328817, 0.333874),
    "D1200": (0.00214063, 0.216493), "D1500": (0.00215554, 0.215758), "D1800": (0.00271306, 0.269251),
}


@pytest.mark.parametrize("name", GEOPHONES)
def test_e2a3_full_coefficients(name):
    k, beta_pct = E2A3_LACZNIE[name]
    table = load_coefficients("e2a3_full")
    assert table.k(name) == pytest.approx(k, abs=1e-9, rel=0)
    assert table.beta(name) == pytest.approx(beta_pct / 100.0, abs=1e-9, rel=0)


def test_e2a3_full_meta_and_indices_in_file():
    table = load_coefficients("e2a3_full")
    assert table.meta["scope"] == "lacznie" and table.meta["n_visits"] == 414
    # wskazniki w pliku (nie uzywane do korekty) — kontrola odczytu
    assert table.k("SCI300") == pytest.approx(0.0301423, abs=1e-9)
    assert table.beta("BCI") == pytest.approx(0.0192233, abs=1e-9)


def test_tab71_is_rounded_set():
    t = load_coefficients("tab71")
    assert t.k("D0") == 0.016 and t.beta("D0") == pytest.approx(0.0160)
    assert t.k("D450") == 0.010 and t.k("D900") == 0.003 and t.beta("D1800") == pytest.approx(0.0027)


def test_legacy_tables_and_errors():
    assert all(legacy_table("public").k(g) == 0.02 for g in GEOPHONES)
    assert all(legacy_table("highway").k(g) == 0.01 for g in GEOPHONES)
    with pytest.raises(ValueError):
        legacy_table("gravel")
    with pytest.raises(ValueError):
        load_coefficients("nieznany")
