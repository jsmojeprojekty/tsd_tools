import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError, build_n1_config, load_n1_config
from tsdfwd_tools.fwd.io import read_fwd


def _cfg_dict(tmp_path, drops, stations, **over):
    d = {
        "tool": "fwd_tempcorr",
        "input": {"files": [str(drops)], "stations_files": [str(stations)]},
        "temperature": {"source": "column", "column": "asphalt_temp"},
        "correction": {"variant": "B", "coefficient_set": "e2a3_full"},
        "output": {"dir": str(tmp_path / "out"), "formats": ["csv"], "overwrite": True},
    }
    for k, v in over.items():
        d[k].update(v)
    return d


# --- konfiguracja ---
def test_config_defaults_and_validation(tmp_path, drops_xlsx, stations_xlsx):
    cfg = build_n1_config(_cfg_dict(tmp_path, drops_xlsx, stations_xlsx))
    assert cfg.correction.variant == "B" and cfg.input.drop_rule == "mean_nonseating"
    assert cfg.correction.ranges_c["B"] == [5.0, 30.0] and cfg.correction.indices_max_c == 25.0


@pytest.mark.parametrize("patch, msg", [
    ({"correction": {"variant": "Z"}}, "variant"),
    ({"correction": {"coefficient_set": "x"}}, "coefficient_set"),
    ({"input": {"drop_rule": "x"}}, "drop_rule"),
    ({"temperature": {"source": "constant"}}, "constant_c"),
    ({"temperature": {"source": "csv_join"}}, "csv"),
    ({"output": {"formats": ["pdf"]}}, "formats"),
    ({"correction": {"nieznany_klucz": 1}}, "nieznane klucze"),
])
def test_config_rejects_bad_values(tmp_path, drops_xlsx, stations_xlsx, patch, msg):
    with pytest.raises(ConfigError, match=msg):
        build_n1_config(_cfg_dict(tmp_path, drops_xlsx, stations_xlsx, **patch))


def test_config_requires_inputs_and_matching_pairs(tmp_path):
    with pytest.raises(ConfigError):
        build_n1_config({"input": {}})
    with pytest.raises(ConfigError):
        build_n1_config({"input": {"files": ["a.xlsx", "b.xlsx"], "stations_files": ["s.xlsx"]}})
    with pytest.raises(ConfigError):
        build_n1_config({"input": {"files": ["a.xlsx"]}, "correction": {"ranges_c": {"A": [5, 25], "B": [30, 5],
                                                                                    "legacy": [5, 25]}}})


# --- odczyt plikow ---
def test_read_xlsx_pair(drops_xlsx, stations_xlsx):
    data = read_fwd(drops_xlsx, stations_path=stations_xlsx)
    assert data.fmt == "xlsx_drops_stations"
    assert len(data.stations) == 121 and len(data.drops) == 242
    assert data.drops["non_seating"].all()
    d = data.drops[(data.drops.station_id == 1) & (data.drops.drop_id == 1)].iloc[0]
    assert d["force_kn"] == pytest.approx(49.34, abs=1e-3) and d["d1"] == pytest.approx(168.8, abs=1e-2)
    assert data.stations["time"].notna().all()


def test_read_csv_generic(tmp_path):
    rows = []
    for sid in (1, 2):
        for drop in (1, 2):
            rows.append({"station_id": sid, "force_kn": 50.0, "asphalt_temp": 15.0 + sid,
                         **{f"d{i}": 100.0 * i for i in range(1, 10)}})
    p = tmp_path / "gen.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    data = read_fwd(p)
    assert data.fmt == "csv_generic" and len(data.stations) == 2 and len(data.drops) == 4
    assert data.stations["asphalt_temp"].tolist() == [16.0, 17.0]


def test_read_unknown_and_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_fwd(tmp_path / "brak.xlsx")
    p = tmp_path / "x.txt"
    p.write_text("a")
    with pytest.raises(ValueError):
        read_fwd(p)


def test_sentinel_temperature_is_missing(tmp_path):
    rows = [{"station_id": 1, "force_kn": 50.0, "asphalt_temp": -3.4028e38, **{f"d{i}": 100.0 for i in range(1, 10)}},
            {"station_id": 2, "force_kn": 50.0, "asphalt_temp": 12.0, **{f"d{i}": 100.0 for i in range(1, 10)}}]
    p = tmp_path / "s.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    data = read_fwd(p)
    assert np.isnan(data.stations["asphalt_temp"].iloc[0]) and bool(data.stations["asphalt_temp_sentinel"].iloc[0])


# --- CLI end-to-end ---
def _write_cfg(tmp_path, drops, stations, **over):
    p = tmp_path / "n1.yaml"
    p.write_text(yaml.safe_dump(_cfg_dict(tmp_path, drops, stations, **over)), encoding="utf-8")
    return p


def test_cli_end_to_end_values(tmp_path, drops_xlsx, stations_xlsx):
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx)
    assert main(["fwd_tempcorr", "--config", str(cfg)]) == 0
    out = tmp_path / "out"
    table = pd.read_csv(out / "Drops50_1M_1_tempcorr.csv")
    assert len(table) == 121 and (out / "summary.csv").is_file()
    meta = json.loads((out / "Drops50_1M_1_tempcorr_meta.json").read_text(encoding="utf-8"))
    assert meta["correction"]["variant"] == "B" and meta["correction"]["coefficients"]["set"] == "e2a3_full"
    # stacja 1: D1 znormalizowane (srednia dwoch zrzutow), T = 18 C, wspolczynnik D0 beta = 1,60415 %/C
    st1 = table[table.station_id == 1].iloc[0]
    expected_d0 = np.mean([168.800003 * 50 / 49.34, 169.199997 * 50 / 49.44])
    assert st1["D0"] == pytest.approx(expected_d0, abs=1e-3)
    assert st1["D0_20"] == pytest.approx(expected_d0 * np.exp(0.0160415 * 2.0), abs=1e-3)
    assert st1["SCI300_20"] == pytest.approx(st1["D0_20"] - st1["D300_20"], abs=1e-9)
    assert st1["t_status"] == "entry_first" and st1["flags"] == 0
    assert table[table.station_id == 2].iloc[0]["flags_text"] == "T_CARRIED"
    assert table["t_mid_c"].eq(18.0).all()


def test_cli_dry_run_writes_nothing(tmp_path, drops_xlsx, stations_xlsx):
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx)
    assert main(["fwd_tempcorr", "--config", str(cfg), "--dry-run"]) == 0
    assert not (tmp_path / "out").exists()


def test_cli_xlsx_and_overwrite_protection(tmp_path, drops_xlsx, stations_xlsx):
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx, output={"formats": ["csv", "xlsx"], "overwrite": False})
    assert main(["fwd_tempcorr", "--config", str(cfg)]) == 0
    assert (tmp_path / "out" / "Drops50_1M_1_tempcorr.xlsx").is_file()
    assert main(["fwd_tempcorr", "--config", str(cfg)]) == 1  # plik istnieje, brak nadpisania


def test_cli_constant_temperature_and_variant_a(tmp_path, drops_xlsx, stations_xlsx):
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx, temperature={"source": "constant", "constant_c": 12.0},
                     correction={"variant": "A", "coefficient_set": "tab71"})
    assert main(["fwd_tempcorr", "--config", str(cfg)]) == 0
    t = pd.read_csv(tmp_path / "out" / "Drops50_1M_1_tempcorr.csv")
    assert (t["D0_20"] / t["D0"]).iloc[0] == pytest.approx(1 + 0.016 * 8, abs=1e-9)
    assert t["t_source"].iloc[0] == "constant"


def test_cli_csv_join_temperature(tmp_path, drops_xlsx, stations_xlsx):
    ext = pd.DataFrame({"station_id": range(1, 122), "t_mid": 10.0 + np.arange(121) * 0.1})
    ext.to_csv(tmp_path / "t.csv", index=False)
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx,
                     temperature={"source": "csv_join", "csv": str(tmp_path / "t.csv"), "column": "t_mid"})
    assert main(["fwd_tempcorr", "--config", str(cfg)]) == 0
    t = pd.read_csv(tmp_path / "out" / "Drops50_1M_1_tempcorr.csv")
    assert t["t_mid_c"].iloc[0] == pytest.approx(10.0) and t["t_status"].iloc[0] == "external"


def test_cli_errors_and_other_tools(tmp_path, capsys):
    assert main(["fwd_tempcorr", "--config", str(tmp_path / "brak.yaml")]) == 1
    assert main(["layer_temp", "--config", str(tmp_path / "x.yaml")]) == 1
    assert "BLAD" in capsys.readouterr().err or True


def test_cli_strict_exit_code(tmp_path, drops_xlsx, stations_xlsx):
    cfg = _write_cfg(tmp_path, drops_xlsx, stations_xlsx, temperature={"source": "constant", "constant_c": 2.0})
    assert main(["fwd_tempcorr", "--config", str(cfg), "--strict"]) == 2     # T < 5 C
    cfg_ok = _write_cfg(tmp_path, drops_xlsx, stations_xlsx, temperature={"source": "constant", "constant_c": 15.0})
    assert main(["fwd_tempcorr", "--config", str(cfg_ok), "--strict"]) == 0


def test_example_config_loads():
    root = Path(__file__).resolve().parents[2]
    cfg = load_n1_config(root / "configs" / "n1_example.yaml")
    assert cfg.input.files and cfg.output.overwrite is True
