"""tsd_dsn: katalog przejazdow B_1510off -> N2 (probki z pliku TSD, meteo z cache) -> N3 -> XML DSN w skali FWD."""

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_dsn import build_dsn_config
from tsdfwd_tools.dsn.pipeline import build_survey, find_files, read_trips
from tsdfwd_tools.tsd.io import read_b1510off

UNIT = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, UNIT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


N2H = _load("test_n2_units")                 # make_om, write_cache (syntetyczne meteo)
N3H = _load("test_n3_units")                 # _txt_to_sheet (arkusz o ukladzie eksportu XLS)

TRIP_HEADER = "plik,kod_oddz,rok,droga,jezdnia,pas,km_start,km_direction,chainage_start_m,date_override\n"


def _trips(tmp_path, lines, header=TRIP_HEADER):
    p = tmp_path / "przejazdy.csv"
    p.write_text(header + "".join(lines), encoding="utf-8")
    return p


def _t(**over):
    from tsdfwd_tools.common.config_dsn import DsnTemperature
    return DsnTemperature(**{"meteo_cache_dir": "x", **over})


# --- tabela przejazdow ---
def test_read_trips_parses_types_and_optional_columns(tmp_path):
    p = _trips(tmp_path, ["T4202504230012.raw.sup.txt,ZZ,2025,TEST,1,2,\"40,5\",decreasing,10,2025-04-23\n", "t4202504230013,WA,2025,50,1,1,0,,,\n"])
    t = read_trips(p)
    a = t["t4202504230012"]
    assert a == {"kod_oddz": "ZZ", "rok": 2025, "droga": "TEST", "jezdnia": 1, "pas": 2, "km_start": 40.5, "km_direction": "decreasing",
                 "chainage_start_m": 10.0, "date_override": "2025-04-23"}
    assert t["t4202504230013"] == {"kod_oddz": "WA", "rok": 2025, "droga": "50", "jezdnia": 1, "pas": 1, "km_start": 0.0}


@pytest.mark.parametrize("lines, header, msg", [
    (["a,ZZ,2025,T,1,1,0,,,\n"], "plik,kod_oddz,rok\n", "brak kolumn"),
    (["a,ZZ,2025,T,1,1,0,,,\n", "A.raw.sup.txt,ZZ,2025,T,1,1,0,,,\n"], TRIP_HEADER, "wiecej niz raz"),
    (["a,ZZ,2025,,1,1,0,,,\n"], TRIP_HEADER, "puste pola"),
    (["a,ZZ,rok,T,1,1,0,,,\n"], TRIP_HEADER, "niepoprawna"),
])
def test_read_trips_errors(tmp_path, lines, header, msg):
    with pytest.raises(ConfigError, match=msg):
        read_trips(_trips(tmp_path, lines, header))


def test_read_trips_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_trips(tmp_path / "brak.csv")


# --- probki temperatury z pliku TSD ---
def test_survey_samples_ends_and_utc_to_local(make_tsd):
    run = read_b1510off(make_tsd(n=250))                       # 250 m, GPS 10:16:40 + i s (UTC), 23.04.2025 = czas letni (+2 h)
    s = build_survey(run, _t(sample_m=100.0, window_m=5.0))
    assert s.chainage_m.tolist() == [0.0, 100.0, 200.0, 249.0]               # koniec przejazdu zawsze jest probka
    assert s.measured_at_local.iloc[0].startswith("2025-04-23 12:16:")        # 10:16:40 UTC -> 12:16 lokalnie
    assert s.t_surface.eq(30.0).all() and s.t_air.eq(20.0).all()
    assert s.latitude.between(51.99, 52.01).all()
    loc = build_survey(run, _t(gps_time_basis="local"))
    assert loc.measured_at_local.iloc[0].startswith("2025-04-23 10:16:")      # bez zamiany


def test_survey_winter_time_is_plus_one_hour(make_tsd):
    run = read_b1510off(make_tsd(name="T4202501150001.raw.sup.txt", n=60))
    assert build_survey(run, _t()).measured_at_local.iloc[0].startswith("2025-01-15 11:16:")


def test_survey_unwraps_midnight_and_needs_date_and_gps_time(make_tsd):
    run = read_b1510off(make_tsd(n=100))
    run.data["gps_time_s"] = (np.arange(100) * 1.0 + 86400 - 50) % 86400                  # 23:59:10 ... 00:00:48
    s = build_survey(run, _t(sample_m=60.0, gps_time_basis="local"))
    stamps = pd.to_datetime(s.measured_at_local)
    assert stamps.is_monotonic_increasing and stamps.iloc[-1].day == 24
    run.data["gps_time_s"] = np.nan
    with pytest.raises(ConfigError, match="GPS time"):
        build_survey(run, _t())
    run2 = read_b1510off(make_tsd(name="plik_bez_daty.raw.sup.txt", n=30))
    with pytest.raises(ConfigError, match="daty"):
        build_survey(run2, _t())
    assert build_survey(run2, _t(), "2025-05-01").measured_at_local.iloc[0].startswith("2025-05-01")


# --- konfiguracja ---
def _cfg_dict(tmp_path, **over):
    d = {"input": {"tsd_dir": str(tmp_path / "tsd"), "trips_csv": str(tmp_path / "przejazdy.csv")},
         "temperature": {"meteo_cache_dir": str(tmp_path / "cache"), "meteo_offline": True},
         "fwd_scale": {"to_fwd_multiplier": 1.6}, "qc": {"gps_gyro": False},
         "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    for k, v in over.items():
        d[k] = {**d.get(k, {}), **v} if isinstance(v, dict) else v
    return d


def test_dsn_config_validation(tmp_path):
    assert build_dsn_config(_cfg_dict(tmp_path)).temperature.sample_m == 100.0
    for patch, msg in [({"input": {"tsd_dir": None}}, "dokladnie jedno"), ({"input": {"trips_csv": None}}, "trips_csv"),
                       ({"input": {"tsd_files": ["a"]}}, "dokladnie jedno"), ({"temperature": {"gps_time_basis": "x"}}, "gps_time_basis"),
                       ({"temperature": {"sample_m": 0}}, "dodatnie"), ({"temperature": {"meteo_cache_dir": None}}, "meteo_cache_dir"),
                       ({"fwd_scale": {"to_fwd_multiplier": None}}, "przelicznik"),
                       ({"fwd_scale": {"to_fwd_conversion_csv": "c.csv"}}, "nie oba"), ({"nieznany": 1}, "nieznane")]:
        with pytest.raises(ConfigError, match=msg):
            build_dsn_config(_cfg_dict(tmp_path, **patch))
    ok = build_dsn_config(_cfg_dict(tmp_path, fwd_scale={"to_fwd_multiplier": None}, xml={"scale": "tsd"}))     # skala TSD bez przelicznika
    assert ok.xml["scale"] == "tsd"


def test_find_files_patterns_and_duplicates(tmp_path, make_tsd):
    d = tmp_path / "tsd"
    d.mkdir()
    for n in ("T4202504230012.raw.sup.txt", "T4202504230013.raw.sup.txt"):
        (d / n).write_text("x", encoding="utf-8")
    (d / "~$T4202504230099.raw.sup.xlsx").write_text("x", encoding="utf-8")
    (d / "inny.csv").write_text("x", encoding="utf-8")
    cfg = build_dsn_config(_cfg_dict(tmp_path))
    assert [f.name for f in find_files(cfg)] == ["T4202504230012.raw.sup.txt", "T4202504230013.raw.sup.txt"]
    (d / "T4202504230012.raw.sup.xls").write_text("x", encoding="utf-8")
    with pytest.raises(ConfigError, match="kilku plikach"):
        find_files(cfg)
    empty = tmp_path / "pusty"
    empty.mkdir()
    with pytest.raises(ConfigError, match="zadnych plikow"):
        find_files(build_dsn_config(_cfg_dict(tmp_path, input={"tsd_dir": str(empty)})))


# --- potok end-to-end (meteo z cache, bez sieci) ---
@pytest.fixture
def setup(tmp_path, make_tsd):
    (tmp_path / "tsd").mkdir()
    make_tsd(name="tsd/T4202504230012.raw.sup.txt", n=250)                                   # poprawny B_1510off (.txt)
    txt = make_tsd(name="T4202504230013.raw.sup.txt", n=250)
    N3H._txt_to_sheet(txt, tmp_path / "tsd" / "T4202504230013.raw.sup.xlsx")                   # ten sam uklad jako arkusz
    txt.unlink()
    N2H.write_cache(tmp_path / "cache", N2H.make_om("2025-03-01", "2025-05-31"), lat=52.0, lon=21.0, start="2025-03-01", end="2025-05-31")
    return tmp_path


def _write_cfg(tmp_path, **over):
    p = tmp_path / "dsn.yaml"
    p.write_text(yaml.safe_dump(_cfg_dict(tmp_path, **over)), encoding="utf-8")
    return p


def _first_record(path):
    return {c.tag: c.text for c in ET.parse(path).getroot()[1]}


def test_dsn_end_to_end_two_trips_txt_and_xlsx(setup):
    tmp = setup
    _trips(tmp, ["T4202504230012,ZZ,2025,TEST,1,1,40.0,,,\n", "T4202504230013,ZZ,2025,TEST,1,2,41.0,,,\n"])
    cfg = _write_cfg(tmp)
    assert main(["tsd_dsn", "--config", str(cfg), "--dry-run"]) == 0
    assert not (tmp / "out").exists()
    assert main(["tsd_dsn", "--config", str(cfg)]) == 0
    out = tmp / "out"
    s = pd.read_csv(out / "batch_summary.csv")
    assert s.status.tolist() == ["ok", "ok"] and s.n_xml_records.gt(0).all() and s.n2_samples.tolist() == [4, 4]
    assert s.n2_valid_t12.tolist() == [4, 4] and s.fwd_factor.eq(1.6).all() and s.fwd_source.eq("config:to_fwd_multiplier").all()
    meta = json.loads((out / "batch_meta.json").read_text(encoding="utf-8"))
    assert meta["n_ok"] == 2 and meta["n_error"] == 0 and meta["temperature"]["gps_time_basis"] == "utc"
    n2 = json.loads((out / "T4202504230012" / "n2" / "layer_temp_meta.json").read_text(encoding="utf-8"))
    assert n2["meteo"]["n_requests_made"] == 0 and n2["n_valid_t_layer"] == 4
    r1 = _first_record(out / "T4202504230012" / "n3" / "UC_T4202504230012.xml")
    r2 = _first_record(out / "T4202504230013" / "n3" / "UC_T4202504230013.xml")
    assert r1["DROGA"] == "TEST" and r1["PAS"] == "1" and r2["PAS"] == "2" and r1["DATA"] == "2025-04-23"
    assert r1["D_0"] == r2["D_0"] and float(r1["D_0"]) > 250                                   # skala FWD (1,6 x d0 ok. 180 po korekcie)
    assert float(r1["KM"]) == pytest.approx(40.02, abs=1e-6) and float(r2["KM"]) == pytest.approx(41.02, abs=1e-6)       # 2. rekord: 20 m
    x = json.loads((out / "T4202504230012" / "n3" / "T4202504230012_n3_meta.json").read_text(encoding="utf-8"))
    assert x["xml_uc"]["scale"] == "fwd" and x["xml_uc"]["fwd_scale"]["factor"] == 1.6


def test_dsn_one_bad_trip_does_not_stop_the_rest(setup, make_tsd, capsys):
    tmp = setup
    make_tsd(name="tsd/T4202504230014.raw.sup.txt", n=60, recal="")                          # eksport nominalny
    make_tsd(name="tsd/T4202504230015.raw.sup.txt", n=60)                                    # brak wpisu w tabeli przejazdow
    _trips(tmp, ["T4202504230012,ZZ,2025,TEST,1,1,40.0,,,\n", "T4202504230013,ZZ,2025,TEST,1,2,41.0,,,\n",
                 "T4202504230014,ZZ,2025,TEST,1,1,42.0,,,\n"])
    assert main(["tsd_dsn", "--config", str(_write_cfg(tmp))]) == 1                            # kod 1, ale wyniki dobrych sa
    err = capsys.readouterr().err
    assert "T4202504230014" in err and "nominalny" in err and "T4202504230015" in err and "brak wpisu" in err
    s = pd.read_csv(tmp / "out" / "batch_summary.csv").set_index("file")
    assert s.loc["T4202504230012.raw.sup.txt", "status"] == "ok" and s.loc["T4202504230013.raw.sup.xlsx", "status"] == "ok"
    assert s.loc["T4202504230014.raw.sup.txt", "status"] == s.loc["T4202504230015.raw.sup.txt", "status"] == "error"
    assert not (tmp / "out" / "T4202504230014").exists()                                       # nominalny: bez N2 i bez XML
    assert (tmp / "out" / "T4202504230012" / "n3" / "UC_T4202504230012.xml").is_file()


def test_dsn_without_meteo_gives_error_row_not_crash(setup):
    tmp = setup
    _trips(tmp, ["T4202504230012,ZZ,2025,TEST,1,1,40.0,,,\n", "T4202504230013,ZZ,2025,TEST,1,2,41.0,,,\n"])
    import shutil
    shutil.rmtree(tmp / "cache")
    (tmp / "cache").mkdir()
    assert main(["tsd_dsn", "--config", str(_write_cfg(tmp))]) == 1
    s = pd.read_csv(tmp / "out" / "batch_summary.csv")
    assert s.status.eq("error").all() and s.message.str.len().gt(10).all()


def test_dsn_overwrite_protection(setup):
    tmp = setup
    _trips(tmp, ["T4202504230012,ZZ,2025,TEST,1,1,40.0,,,\n", "T4202504230013,ZZ,2025,TEST,1,2,41.0,,,\n"])
    cfg = _write_cfg(tmp, output={"overwrite": False})
    assert main(["tsd_dsn", "--config", str(cfg)]) == 0
    assert main(["tsd_dsn", "--config", str(cfg)]) == 1                                         # batch_summary.csv istnieje
    assert main(["tsd_dsn", "--config", str(_write_cfg(tmp, output={"overwrite": True}))]) == 0
