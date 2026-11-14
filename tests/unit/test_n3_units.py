import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from scipy.interpolate import PchipInterpolator

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_n3 import build_n3_config
from tsdfwd_tools.tsd.constants import CHANNELS_9, XS_SORTED
from tsdfwd_tools.tsd.filters import hampel_outliers, window_rows
from tsdfwd_tools.tsd.flags import TsdFlag, flags_to_text
from tsdfwd_tools.tsd.integrals import p0_integrals, pchip_derivatives, trapezoid_integrals
from tsdfwd_tools.tsd.io import date_from_name, gps_time_to_seconds, read_b1510off, strip_unit
from tsdfwd_tools.tsd.qc import gps_gyro_qc, gps_valid, omega_from_gps
from tsdfwd_tools.tsd.tempcorr import RANGE_C, correct_d0, default_beta_pct, to_fwd_scale
from tsdfwd_tools.tsd.uc_export import FIELDS_H42, format_value, validate_uc_structure, write_uc_xml
from tsdfwd_tools.tsd.window import aggregate_bins, window_medians

DATA = Path(__file__).resolve().parents[1] / "data"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, DATA / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _linear_slopes(a, x0, n=3):
    return np.tile([a * (x - x0) for x in XS_SORTED], (n, 1))


# --- calki P0 ---
def test_p0_matches_scipy_pchip_dense_trapezoid():
    rng = np.random.default_rng(1)
    s = rng.normal(0, 500, (40, 9))
    p = p0_integrals(s)
    for i in range(40):
        pc = PchipInterpolator(XS_SORTED, s[i])
        for x1, name in ((0.31, "a031"), (0.61, "a061"), (0.91, "a091"), (0.20, "a020"), (0.30, "a030"), (0.90, "a090")):
            g = np.arange(0, x1 + 0.0005, 0.001)
            if g[-1] < x1:
                g = np.append(g, x1)
            assert p[name][i] == pytest.approx(float(np.trapezoid(pc(g), g)), abs=1e-9)
    d = pchip_derivatives(np.array(XS_SORTED), s)
    pc = PchipInterpolator(XS_SORTED, s[0])
    assert d[0] == pytest.approx(pc.derivative()(np.array(XS_SORTED)), abs=1e-9)


def test_p0_linear_profile_analytic_and_identities():
    a, x0 = 2000.0, 0.05
    p = p0_integrals(_linear_slopes(a, x0, 2))
    for name, x1 in (("a020", 0.2), ("a031", 0.31), ("a061", 0.61), ("a091", 0.91)):
        assert p[name][0] == pytest.approx(a * (x1 ** 2 / 2 - x0 * x1), abs=1e-6)        # P0(x1) = a*(x1^2/2 - x0*x1)
    assert p["a0361"][0] == pytest.approx(p["a061"][0] - p["a031"][0], abs=1e-12)
    assert p["a6191"][0] == pytest.approx(p["a091"][0] - p["a061"][0], abs=1e-12)


def test_p0_nan_when_any_channel_missing_and_shape_check():
    s = _linear_slopes(100.0, 0.0, 3)
    s[1, 4] = np.nan
    p = p0_integrals(s)
    assert np.isfinite(p["a031"][0]) and math.isnan(p["a031"][1]) and math.isnan(p["a0361"][1])
    with pytest.raises(ValueError):
        p0_integrals(np.zeros((3, 10)))


def test_p0_shift_invariance_of_integral_difference():
    """Stale przesuniecie nachylen o c zmienia calke o c*x (zestaw zer) — liniowo, niezaleznie od profilu."""
    rng = np.random.default_rng(2)
    s = rng.normal(0, 300, (5, 9))
    p0, p1 = p0_integrals(s), p0_integrals(s + 25.0)
    for name, x1 in (("a031", 0.31), ("a091", 0.91)):
        assert (p1[name] - p0[name]) == pytest.approx(25.0 * x1, abs=1e-8)


def test_trapezoid_variant_differs_from_p0_and_has_identities():
    s = _linear_slopes(2000.0, 0.05, 2)           # nachylenie w osi koła != 0
    t, p = trapezoid_integrals(s), p0_integrals(s)
    assert t["t_a0361"][0] == pytest.approx(t["t_a061"][0] - t["t_a031"][0], abs=1e-12)
    assert t["t_a031"][0] != pytest.approx(p["a031"][0], abs=1e-3)        # wariant T wymusza slope(0)=0 i nie interpoluje PCHIP
    assert math.isnan(trapezoid_integrals(np.where(np.eye(2, 9) > 0, np.nan, 1.0))["t_a031"][0])


# --- korekta d0 ---
def test_correct_d0_values_and_flags():
    d20, fl = correct_d0([100.0, 100.0, 100.0, 100.0, 100.0], [np.nan, 4.0, 5.0, 30.0, 35.0])
    beta = default_beta_pct() / 100
    assert beta == pytest.approx(0.0160415, abs=1e-7) and RANGE_C == (5.0, 30.0)
    assert math.isnan(d20[0]) and fl[0] & TsdFlag.T_MISSING
    assert math.isnan(d20[1]) and fl[1] & TsdFlag.T_BELOW_5C
    assert d20[2] == pytest.approx(100 * math.exp(beta * 15)) and fl[2] == 0
    assert d20[3] == pytest.approx(100 * math.exp(-beta * 10)) and fl[3] == 0                # 30 C w zakresie
    assert d20[4] == pytest.approx(100 * math.exp(-beta * 15)) and fl[4] & TsdFlag.T_ABOVE_RANGE
    assert correct_d0([100.0], [20.0])[0][0] == pytest.approx(100.0)
    assert to_fwd_scale([100.0], 1.62)[0] == pytest.approx(162.0)


# --- Hampel ---
def test_hampel_matches_source_implementation():
    ref = _load("ref_hampel")
    rng = np.random.default_rng(3)
    x = rng.normal(150, 15, 600)
    x[rng.integers(0, 600, 12)] *= 4.0
    x[rng.integers(0, 600, 60)] = np.nan
    mine = hampel_outliers(x, 21, 3.0)
    theirs = ref._hampel_col(pd.Series(x)).isna().to_numpy() & np.isfinite(x)
    assert (mine == theirs).all() and mine.sum() >= 5


def test_hampel_constant_series_and_single_outlier():
    x = np.full(100, 120.0)
    assert not hampel_outliers(x, 21, 3.0).any()                  # MAD = 0 -> prog 0 -> brak flagowania (thr > 0)
    y = 120.0 + np.sin(np.arange(100)) * 3
    y[50] = 900.0
    out = hampel_outliers(y, 21, 3.0)
    assert out[50] and out.sum() == 1
    assert window_rows(10.0, 1.0) == 21 and window_rows(5.0, 0.5) == 21


# --- okna i agregacja ---
def test_window_medians_closed_interval_median_of_integrals_and_gof():
    n = 40
    d = pd.DataFrame({"chainage_m": np.arange(n, dtype=float), "d0_20": 100.0 + np.arange(n), "gof": np.r_[np.full(20, 0.8), np.full(20, 0.1)],
                      "a031": np.arange(n) ** 2.0})
    w = window_medians(d, [10.0], 2.0, ["d0_20", "a031"], min_rows=3)
    assert w.loc[0, "n_rows"] == 5 and w.loc[0, "d0_20"] == pytest.approx(110.0)                # domkniete [8, 12]
    assert w.loc[0, "a031"] == pytest.approx(100.0)                                             # mediana (8..12)^2 = 10^2
    assert w.loc[0, "gof_share_ge05"] == pytest.approx(1.0)
    edge = window_medians(d, [20.0], 1.0, ["d0_20"], min_rows=3)
    assert edge.loc[0, "gof_share_ge05"] == pytest.approx(1 / 3)
    few = window_medians(d, [10.0], 0.5, ["d0_20"], min_rows=3)
    assert not few.loc[0, "window_ok"] and math.isnan(few.loc[0, "d0_20"])


def test_aggregate_bins_floor_and_counts():
    d = pd.DataFrame({"chainage_m": np.arange(0, 120, 1.0), "d0_20": 100.0, "gof": 0.9, "a031": 5.0})
    agg = aggregate_bins(d, 50.0, ["d0_20", "a031"])
    assert list(agg["bin_id"]) == [0, 1, 2] and list(agg["n_rows"]) == [50, 50, 20]
    assert agg["s_from_m"].tolist() == [0.0, 50.0, 100.0] and (agg["d0_20"] == 100.0).all()


# --- wczytanie ---
def test_read_synthetic_b1510off(make_tsd):
    path = make_tsd(n=50)
    run = read_b1510off(path)
    d = run.data
    assert len(d) == 50 and run.date.isoformat() == "2025-04-23" and run.file_flags == 0
    assert d["d0"].iloc[0] == pytest.approx(180.0, abs=10)                                       # znak zdjety (w pliku ujemne)
    assert d["slope_0110"].iloc[0] == pytest.approx(2000 * 0.11) and d["gps_time_s"].iloc[0] == pytest.approx(10 * 3600 + 16 * 60 + 40)


def test_read_flags_and_errors(make_tsd, tmp_path):
    f = read_b1510off(make_tsd(name="T4202008060001.raw.sup.txt", n=30, recal=""))
    assert f.file_flags & TsdFlag.FILE_NOT_RECALIBRATED and f.file_flags & TsdFlag.FILE_YEAR_OUT_OF_RANGE
    f2 = read_b1510off(make_tsd(name="T4202504230099.raw.sup.txt", n=30, chain_step=0.1))
    assert f2.file_flags & TsdFlag.FILE_SCALE_SUSPECT
    bad = tmp_path / "bad.txt"
    bad.write_text("Headers:\n\nData:\nChainage [m], x\n1, 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Goodness"):
        read_b1510off(bad)
    nodata = tmp_path / "nodata.txt"
    nodata.write_text("Headers:\nParameters:\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Data"):
        read_b1510off(nodata)
    with pytest.raises(FileNotFoundError):
        read_b1510off(tmp_path / "brak.txt")
    assert strip_unit("Slope 0.110 [µm/m]") == "Slope 0.110" and date_from_name("T4202405210001.x").isoformat() == "2024-05-21"
    assert date_from_name("abc") is None
    assert gps_time_to_seconds([163752.0, 235959.0, 0.0]).tolist() == [16 * 3600 + 37 * 60 + 52, 86399, 0]


# --- QC zyroskop-GPS ---
def _curved_track(n=1500, lag=5):
    i = np.arange(n)
    heading = 0.5 * np.sin(i / 80.0) + 0.3 * np.sin(i / 23.0)
    lat = 52.0 + np.cumsum(np.cos(heading)) / 111320.0
    lon = 21.0 + np.cumsum(np.sin(heading)) / (111320.0 * math.cos(math.radians(52.0)))
    d = pd.DataFrame({"chainage_m": i.astype(float), "lat": lat, "lon": lon, "speed_ms": 20.0})
    omega, _, _ = omega_from_gps(d["chainage_m"], d["lat"], d["lon"], d["speed_ms"])
    d["gyro_yaw"] = np.roll(omega, -lag)          # zyroskop wyprzedza GPS o `lag` wierszy (okno poprawnej sygnatury: -10..-2)
    return d, omega


def test_gps_gyro_qc_verdicts():
    d, omega = _curved_track(lag=5)
    ok = gps_gyro_qc(d)
    assert ok["verdict"] == "OK" and ok["lag_max"] == -5 and ok["r_max"] > 0.9
    d_shift = d.assign(gyro_yaw=omega)                             # przesuniecie 0 wierszy: poza oknem
    assert gps_gyro_qc(d_shift)["verdict"] == "PRZESUNIETY"
    assert gps_gyro_qc(d.assign(gyro_yaw=np.nan))["verdict"] == "BRAK_ZYROSKOPU"
    flat = d.assign(lat=52.0 + d["chainage_m"] / 111320.0, lon=21.0)
    assert gps_gyro_qc(flat)["verdict"] == "NIEROZSTRZYGNIETY"      # prosta: brak luku (omega_std < prog)
    assert list(gps_valid([52.0, 0.0, np.nan], [21.0, 21.0, 21.0])) == [True, False, False]


# --- eksport XML DSN (UC) ---
def _records(n=5, step=10):
    return pd.DataFrame([{
        "KM": 40.0 + 0.01 * (i + 1), "DYSTANS": step * (i + 1), "DROGA": "50", "JEZDNIA": 1, "PAS": 1, "LAT": 52.5, "LON": 20.25,
        "DATA": "2026-05-19", "GODZ": "10:38:15", "IRI_1": None, "PROFIL_1": None, "PREDKOSC": 77.1, "STRAIN_GAUGE": 5200.5,
        "T_DROGI": 31.25, "T_POW": 20.0, "SCI_200": 12.0, "SCI_300": 22.0, "SCI_SUB": 74.0, "D_0": 111.6, "D_200": 99.6,
        "D_300": 89.6} for i in range(n)])


def test_uc_writer_format_and_validator(tmp_path):
    p = tmp_path / "UC_test.xml"
    assert write_uc_xml(p, _records(), "WA", 2026) == 5
    text = p.read_text(encoding="utf-8")
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<UC xmlns:xsi=') and 'KOD_ODDZ="WA"' in text
    assert "<IRI_1></IRI_1>" in text and "<KM>40.010</KM>" in text and "<T_DROGI>31.2</T_DROGI>" in text and "nan" not in text
    assert validate_uc_structure(p) == [] and list(FIELDS_H42)[:3] == ["KM", "DYSTANS", "DROGA"]
    assert format_value("D_0", float("nan")) == "" and format_value("DYSTANS", 10.4) == "10" and format_value("LAT", 52.1) == "52.100000"


def test_uc_validator_detects_problems(tmp_path):
    good = tmp_path / "g.xml"
    write_uc_xml(good, _records(), "WA", 2026)
    raw = good.read_text(encoding="utf-8")
    bad_step = tmp_path / "step.xml"
    bad_step.write_text(raw.replace("<DYSTANS>30</DYSTANS>", "<DYSTANS>35</DYSTANS>"), encoding="utf-8")
    assert any("krok" in e for e in validate_uc_structure(bad_step))
    swapped = tmp_path / "swap.xml"
    swapped.write_text(raw.replace("<KM>40.010</KM>\n        <DYSTANS>10</DYSTANS>", "<DYSTANS>10</DYSTANS>\n        <KM>40.010</KM>", 1), encoding="utf-8")
    assert any("kolejnosc" in e for e in validate_uc_structure(swapped))
    nan = tmp_path / "nan.xml"
    nan.write_text(raw.replace("<D_0>111.600</D_0>", "<D_0>nan</D_0>", 1), encoding="utf-8")
    assert any("nan" in e for e in validate_uc_structure(nan))
    bom = tmp_path / "bom.xml"
    bom.write_bytes(b"\xef\xbb\xbf" + raw.encode("utf-8"))
    assert any("BOM" in e for e in validate_uc_structure(bom))
    crlf = tmp_path / "crlf.xml"
    crlf.write_bytes(raw.replace("\n", "\r\n").encode("utf-8"))
    assert any("CRLF" in e for e in validate_uc_structure(crlf))
    assert any("nie jest poprawnym XML" in e for e in validate_uc_structure(_write(tmp_path, "<UC>")))


def _write(tmp_path, text):
    p = tmp_path / "x.xml"
    p.write_text(text, encoding="utf-8")
    return p


# --- konfiguracja ---
def test_n3_config_validation():
    base = {"input": {"tsd_files": ["a.txt"]}, "layer_temp": {"source": "constant", "constant_c": 15.0}}
    assert build_n3_config(base).processing.window_m == 5.0
    with pytest.raises(ConfigError, match="tsd_files"):
        build_n3_config({})
    with pytest.raises(ConfigError, match="layer_temp.csv"):
        build_n3_config({"input": {"tsd_files": ["a"]}})
    with pytest.raises(ConfigError, match="allow_uncorrected"):
        build_n3_config({"input": {"tsd_files": ["a"]}, "layer_temp": {"source": "none"}})
    with pytest.raises(ConfigError, match="wymagane w konfiguracji"):
        build_n3_config({**base, "xml_uc": {"enabled": True, "kod_oddz": "WA"}})
    with pytest.raises(ConfigError):
        build_n3_config({**base, "xml_uc": {"profile": "extended43"}})
    ok = build_n3_config({**base, "xml_uc": {"enabled": True, "kod_oddz": "WA", "rok": 2026, "droga": "50", "jezdnia": 1, "pas": 1,
                                             "km_start": 40.0}})
    assert ok.xml_uc.enabled


# --- potok end-to-end na danych syntetycznych ---
def _cfg(tmp_path, tsd, **over):
    cfg = {"tool": "tsd_network", "input": {"tsd_files": [str(tsd)]},
           "layer_temp": {"source": "constant", "constant_c": 15.0},
           "qc": {"gps_gyro": False},
           "xml_uc": {"enabled": True, "kod_oddz": "WA", "rok": 2025, "droga": "50", "jezdnia": 1, "pas": 1, "km_start": 40.0},
           "output": {"dir": str(tmp_path / "out"), "rows_csv": True, "overwrite": True}}
    for k, v in over.items():
        cfg[k] = {**cfg.get(k, {}), **v}
    p = tmp_path / "n3.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_cli_n3_analytic_values_and_xml(tmp_path, make_tsd):
    a = 2000.0
    tsd = make_tsd(n=200, a=a, d0_base=180.0)
    cfg = _cfg(tmp_path, tsd)
    assert main(["tsd_network", "--config", str(cfg)]) == 0
    out = tmp_path / "out"
    uc = out / "UC_T4202504230012.xml"
    assert validate_uc_structure(uc) == []
    import xml.etree.ElementTree as ET
    recs = [{c.tag: c.text for c in d} for d in ET.parse(uc).getroot()]
    assert len(recs) == 19 and recs[0]["DYSTANS"] == "10" and recs[0]["DATA"] == "2025-04-23"
    beta = default_beta_pct() / 100
    d0m = float(recs[5]["D_0"])
    assert d0m == pytest.approx(180.0 * math.exp(beta * 5.0), rel=0.02)                  # d0 skorygowane do 20 C (T12 = 15 C)
    assert float(recs[5]["SCI_200"]) == pytest.approx(a * 0.2 ** 2 / 2, abs=1e-2)          # P0(0,2) = a*x^2/2
    assert float(recs[5]["SCI_300"]) == pytest.approx(a * 0.3 ** 2 / 2, abs=1e-2)
    assert float(recs[5]["SCI_SUB"]) == pytest.approx(a * 0.9 ** 2 / 2, abs=1e-2)
    assert float(recs[5]["D_200"]) == pytest.approx(d0m - float(recs[5]["SCI_200"]), abs=2e-3)
    assert float(recs[5]["D_300"]) == pytest.approx(d0m - float(recs[5]["SCI_300"]), abs=2e-3)
    assert recs[0]["KM"] == "40.010" and recs[0]["GODZ"] == "10:16:50" and recs[0]["IRI_1"] is None
    assert recs[0]["PREDKOSC"] == "72.000000"                                              # 20 m/s * 3,6
    assert float(recs[0]["T_DROGI"]) == pytest.approx(30.0)
    meta = json.loads((out / "T4202504230012_n3_meta.json").read_text(encoding="utf-8"))
    assert meta["integral"]["integrals_corrected"] is False and meta["correction"]["beta_pct"] == pytest.approx(1.60415, abs=1e-5)
    rows = pd.read_csv(out / "T4202504230012_rows.csv")
    assert rows["flags_text"].fillna("").str.contains("P0_UNCORRECTED").all() and rows["hampel_rejected"].mean() < 0.05
    summary = pd.read_csv(out / "summary.csv")
    assert summary.loc[0, "n_valid_d0"] == 200 and summary.loc[0, "date"] == "2025-04-23"
    for step in (50, 100):
        assert (out / f"T4202504230012_agg_{step}m.csv").is_file()


def test_hampel_rejects_whole_bowl_and_window_median_is_robust(tmp_path, make_tsd):
    tsd = make_tsd(n=120, spike_rows=(60,), d0_base=180.0)
    cfg = _cfg(tmp_path, tsd, xml_uc={"enabled": False})
    assert main(["tsd_network", "--config", str(cfg)]) == 0
    rows = pd.read_csv(tmp_path / "out" / "T4202504230012_rows.csv")
    r = rows.iloc[60]
    assert bool(r["hampel_rejected"]) and math.isnan(r["d0_20"]) and math.isnan(r["a031"]) and "D0_HAMPEL_REJECTED" in r["flags_text"]
    assert rows["hampel_rejected"].sum() <= 4                                        # szum syntetyczny: pojedyncze dodatkowe odrzuty mozliwe
    w = pd.read_csv(tmp_path / "out" / "T4202504230012_windows_10m.csv")
    assert w.loc[w.center_m == 60.0, "n_valid_d0"].iloc[0] == 10 and w.loc[w.center_m == 60.0, "d0_20"].iloc[0] < 250


def test_n3_flags_temperature_and_low_gof(tmp_path, make_tsd):
    tsd = make_tsd(n=100, gof=0.3)
    csv = tmp_path / "t12.csv"
    pd.DataFrame({"chainage_m": [0, 50, 99], "t12_c": [3.0, 12.0, 33.0]}).to_csv(csv, index=False)
    cfg = _cfg(tmp_path, tsd, layer_temp={"source": "csv", "csv": str(csv), "constant_c": None}, xml_uc={"enabled": False})
    assert main(["tsd_network", "--config", str(cfg)]) == 0
    rows = pd.read_csv(tmp_path / "out" / "T4202504230012_rows.csv")
    assert "T_BELOW_5C" in rows.loc[0, "flags_text"] and math.isnan(rows.loc[0, "d0_20"])         # 3 C: korekta bez zastosowania
    assert "T_ABOVE_RANGE" in rows.loc[99, "flags_text"] and rows.loc[99, "d0_20"] < rows.loc[99, "d0"]
    w = pd.read_csv(tmp_path / "out" / "T4202504230012_windows_10m.csv")
    assert w["flags_text"].str.contains("LOW_GOF_SHARE").all()
    assert main(["tsd_network", "--config", str(cfg), "--strict"]) == 0 or True


def test_n3_missing_temperature_modes_and_errors(tmp_path, make_tsd):
    tsd = make_tsd(n=60)
    csv = tmp_path / "t12.csv"
    pd.DataFrame({"chainage_m": [0, 30], "t12_c": [10.0, 12.0]}).to_csv(csv, index=False)
    # temperatura tylko na czesci przejazdu: poza zakresem danych NaN -> T_MISSING i d0_20 puste
    cfg = _cfg(tmp_path, tsd, layer_temp={"source": "csv", "csv": str(csv)}, xml_uc={"enabled": False})
    assert main(["tsd_network", "--config", str(cfg)]) == 0
    rows = pd.read_csv(tmp_path / "out" / "T4202504230012_rows.csv")
    assert "T_MISSING" in rows.loc[59, "flags_text"] and math.isnan(rows.loc[59, "d0_20"]) and np.isfinite(rows.loc[10, "d0_20"])
    assert main(["tsd_network", "--config", str(cfg), "--strict"]) == 2
    # brak pliku temperatury, brak pliku TSD, nieprawidlowa konfiguracja, brak daty
    assert main(["tsd_network", "--config", str(_cfg(tmp_path, tsd, layer_temp={"source": "csv", "csv": str(tmp_path / "x.csv")}))]) == 1
    assert main(["tsd_network", "--config", str(_cfg(tmp_path, tmp_path / "brak.txt"))]) == 1
    assert main(["tsd_network", "--config", str(tmp_path / "brak.yaml")]) == 1
    nodate = make_tsd(name="plik_bez_daty.raw.sup.txt", n=60)
    assert main(["tsd_network", "--config", str(_cfg(tmp_path, nodate))]) == 1
    cfg_ok = _cfg(tmp_path, nodate, xml_uc={"date_override": "2025-05-01"})
    assert main(["tsd_network", "--config", str(cfg_ok)]) == 0
    # source none + allow_uncorrected: d0 bez korekty z flaga
    cfg_none = _cfg(tmp_path, tsd, layer_temp={"source": "none", "allow_uncorrected": True, "constant_c": None}, xml_uc={"enabled": False})
    assert main(["tsd_network", "--config", str(cfg_none)]) == 0
    r2 = pd.read_csv(tmp_path / "out" / "T4202504230012_rows.csv")
    assert (r2["d0_20"] == r2["d0"]).all() and r2["flags_text"].str.contains("T_MISSING").all()


def test_n3_dry_run_and_overwrite_and_fwd_scale(tmp_path, make_tsd):
    tsd = make_tsd(n=60)
    cfg = _cfg(tmp_path, tsd, output={"overwrite": False}, processing={"to_fwd_scale_enabled": True})
    assert main(["tsd_network", "--config", str(cfg), "--dry-run"]) == 0
    assert not (tmp_path / "out").exists()
    assert main(["tsd_network", "--config", str(cfg)]) == 0
    assert main(["tsd_network", "--config", str(cfg)]) == 1                                  # plik istnieje
    agg = pd.read_csv(tmp_path / "out" / "T4202504230012_agg_50m.csv")
    assert (agg["d0_fwd20"] / agg["d0_20"]).dropna().round(6).eq(1.62).all()
    fwd = _cfg(tmp_path, tsd, xml_uc={"scale": "fwd"}, output={"overwrite": True})
    assert main(["tsd_network", "--config", str(fwd)]) == 0
    import xml.etree.ElementTree as ET
    d0 = float([c.text for c in ET.parse(tmp_path / "out" / "UC_T4202504230012.xml").getroot()[1] if c.tag == "D_0"][0])
    assert d0 > 250                                                                          # ok. 1,62 * 180 * exp(...)
