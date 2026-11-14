import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.common.constants import GEOPHONES
from tsdfwd_tools.common.flags import Flag, flags_to_text
from tsdfwd_tools.fwd.indices import curvature_indices
from tsdfwd_tools.fwd.normalize import geophone_columns, is_standard_layout, normalize_load, select_drops, to_geophones
from tsdfwd_tools.fwd.quality import assess_temperature, classify_session, placeholder_runs
from tsdfwd_tools.fwd.tempcorr import correct_deflections


def _d(d0=200.0, d300=150.0, d600=100.0, d900=60.0, n=1):
    base = {"D0": d0, "D200": d0 * 0.9, "D300": d300, "D450": d300 * 0.85, "D600": d600, "D900": d900,
            "D1200": d900 * 0.8, "D1500": d900 * 0.65, "D1800": d900 * 0.55}
    return pd.DataFrame([base] * n)


# T-N1-04: wskazniki z ugiec skorygowanych; przyklad D0=200, D300=150, T=10
def test_indices_example_variant_a_and_b():
    a = correct_deflections(_d(), 10.0, variant="A", coefficient_set="tab71")
    b = correct_deflections(_d(), 10.0, variant="B", coefficient_set="tab71")
    assert a.indices["SCI300_20"].iloc[0] == pytest.approx(64.000, abs=1e-3)
    assert b.indices["SCI300_20"].iloc[0] == pytest.approx(65.239, abs=1e-3)


def test_indices_are_differences_of_corrected_deflections_not_own_coefficients():
    res = correct_deflections(_d(), 12.0, variant="B")
    d20 = res.d20.iloc[0]
    assert res.indices["SCI300_20"].iloc[0] == pytest.approx(d20["D0_20"] - d20["D300_20"], abs=1e-12)
    assert res.indices["BDI_20"].iloc[0] == pytest.approx(d20["D300_20"] - d20["D600_20"], abs=1e-12)
    assert res.indices["BCI_20"].iloc[0] == pytest.approx(d20["D600_20"] - d20["D900_20"], abs=1e-12)
    df = pd.DataFrame({f"{g}_20": [1.0] for g in GEOPHONES})
    assert list(curvature_indices(df).columns) == ["SCI300_20", "BDI_20", "BCI_20"]


def test_range_flags_variant_a_and_b():
    temps = np.array([np.nan, 3.0, 5.0, 25.0, 27.0, 30.0, 31.0])
    a = correct_deflections(_d(n=7), temps, variant="A")
    b = correct_deflections(_d(n=7), temps, variant="B")
    fa = a.flag_mask.to_numpy()
    fb = b.flag_mask.to_numpy()
    assert fa[0] & Flag.T_MISSING and fb[0] & Flag.T_MISSING
    assert fa[1] & Flag.T_BELOW_5C and np.isnan(a.d20["D0_20"].iloc[1])      # korekta bez zastosowania < 5 C
    assert fa[2] == 0 and fb[2] == 0                                          # 5 C wlaczone do zakresu
    assert fa[3] == 0                                                         # 25 C wlaczone (zakres A domkniety)
    assert fa[4] & Flag.T_ABOVE_RANGE and not (fb[4] & Flag.T_ABOVE_RANGE)    # A: 27 C poza zakresem, B: w zakresie
    assert not (fb[5] & Flag.T_ABOVE_RANGE) and (fb[6] & Flag.T_ABOVE_RANGE)  # B: 30 C ok, 31 C poza
    assert np.isfinite(a.d20["D0_20"].iloc[4])                                # powyzej zakresu: oznaczone, nie usuniete


def test_index_flags_above_25c_and_nonpositive():
    res = correct_deflections(_d(n=3), np.array([20.0, 26.0, 29.0]), variant="B")
    f = res.flag_mask.to_numpy()
    assert f[0] == 0 and (f[1] & Flag.INDEX_ABOVE_RANGE) and (f[2] & Flag.INDEX_ABOVE_RANGE)
    bad = correct_deflections(_d(d0=100, d300=120, n=1), 20.0, variant="B")
    assert bad.flag_mask.iloc[0] & Flag.INDEX_NONPOSITIVE


def test_legacy_modes():
    pub = correct_deflections(_d(), 10.0, variant="legacy", road_type="public")
    hwy = correct_deflections(_d(), 10.0, variant="legacy", road_type="highway")
    assert pub.d20["D0_20"].iloc[0] == pytest.approx(200 * 1.2, abs=1e-9)
    assert hwy.d20["D0_20"].iloc[0] == pytest.approx(200 * 1.1, abs=1e-9)
    assert pub.flag_mask.iloc[0] & Flag.LEGACY_RULE


def test_unknown_variant_raises():
    with pytest.raises(ValueError):
        correct_deflections(_d(), 10.0, variant="C")


# T-N1-05: normalizacja i regula zrzutu
def test_normalize_load():
    assert normalize_load(100.0, 50.0) == pytest.approx(100.0)
    assert normalize_load([100.0, 200.0], [40.0, 62.5]) == pytest.approx([125.0, 160.0])


def _drops():
    rows = []
    # stacja 1: zrzut 1 osadczy (nie liczony), zrzuty 2 i 3 nieosadcze
    base = [100.0] * 9
    rows.append(dict(station_id=1, drop_id=1, non_seating=False, force_kn=40.0, stress_kpa=0.0, **{f"d{i}": 999.0 for i in range(1, 10)}))
    rows.append(dict(station_id=1, drop_id=2, non_seating=True, force_kn=50.0, stress_kpa=0.0, **{f"d{i}": 100.0 for i in range(1, 10)}))
    rows.append(dict(station_id=1, drop_id=3, non_seating=True, force_kn=40.0, stress_kpa=0.0, **{f"d{i}": 80.0 for i in range(1, 10)}))
    rows.append(dict(station_id=2, drop_id=1, non_seating=False, force_kn=50.0, stress_kpa=0.0, **{f"d{i}": 100.0 for i in range(1, 10)}))
    return pd.DataFrame(rows)


def test_select_drops_rules():
    drops = _drops()
    mean = select_drops(drops, "mean_nonseating")
    assert mean.loc[1, "d1"] == pytest.approx((100.0 * 50 / 50 + 80.0 * 50 / 40) / 2)   # srednia znormalizowanych
    assert mean.loc[1, "n_drops"] == 2 and mean.loc[1, "force_kn"] == pytest.approx(45.0)
    assert mean.loc[2, "flag_mask"] & Flag.NO_NONSEATING_DROP and np.isnan(mean.loc[2, "d1"])
    last = select_drops(drops, "last_nonseating")
    assert last.loc[1, "d1"] == pytest.approx(100.0)
    second = select_drops(drops, "second_drop")
    assert second.loc[1, "d1"] == pytest.approx(100.0)
    with pytest.raises(ValueError):
        select_drops(drops, "nieznana")


def test_geophone_mapping_standard_and_by_x():
    std = (0.0, 200.0, 300.0, 450.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0)
    assert is_standard_layout(std) and not is_standard_layout(None)
    assert geophone_columns(None) == dict(zip(GEOPHONES, [f"d{i}" for i in range(1, 10)]))
    custom = (0.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0, 2100.0, 2400.0)
    m = geophone_columns(custom, "by_x")
    assert m["D300"] == "d2" and m["D600"] == "d3" and m["D1800"] == "d7" and "D200" not in m and "D450" not in m
    norm = pd.DataFrame({f"d{i}": [float(i)] for i in range(1, 10)}, index=pd.Index([1], name="station_id"))
    geo = to_geophones(norm, pd.Series([5], index=[1]), {5: {"x_mm": custom}}, "by_x")
    assert geo.loc[1, "D300"] == 2.0 and np.isnan(geo.loc[1, "D200"])
    assert geo.loc[1, "flag_mask"] & Flag.GEOPHONE_MISSING


# T-N1-06: klasyfikacja temperatury operatora i wartosci zastepcze
def test_classify_session_statuses():
    values = np.array([18.0, 18.0, 18.0, 19.0, 19.0, np.nan, 19.0])
    t = np.arange(7, dtype=float) * 60.0
    res = classify_session(values, t)
    assert res["status"] == ["entry_first", "carried", "carried", "entry_change", "carried", "missing", "carried"]
    assert res["age_s"][2] == pytest.approx(120.0) and res["age_s"][4] == pytest.approx(60.0)


def test_entry_possible_after_long_gap():
    values = np.array([18.0] * 12)
    t = np.arange(12, dtype=float) * 60.0
    t[11] += 3600.0   # duzy odstep przy wartosci bez zmiany
    res = classify_session(values, t)
    assert res["status"][11] == "entry_possible" and res["status"][5] == "carried"


def test_placeholder_runs_and_flags():
    n = 80
    values = np.full(n, 20.4)
    values[10] = np.nan
    t = np.arange(n, dtype=float) * 60.0   # 79 minut > 1 h
    runs = placeholder_runs(values, t)
    assert len(runs) == 1 and runs[0][3] > 1.0 and runs[0][4] == 1
    st = pd.DataFrame({
        "session_id": 1,
        "time": pd.Timestamp("2026-05-19 10:00:00") + pd.to_timedelta(t, unit="s"),
        "asphalt_temp": values,
    })
    q = assess_temperature(st, "asphalt_temp", (20.4,), 60.0)
    assert q["flag_mask"].iloc[0] & Flag.T_PLACEHOLDER
    assert q["flag_mask"].iloc[10] & Flag.T_MISSING
    assert q["t_status"].iloc[0] == "entry_first" and q["t_status"].iloc[3] == "carried"


def test_flags_to_text():
    assert flags_to_text(0) == ""
    assert flags_to_text(int(Flag.T_CARRIED | Flag.T_STALE)) == "T_CARRIED;T_STALE"
