"""N4 tryb geometry: potok end-to-end na danych syntetycznych (TSD wzdluz poludnika 19 E, stacje FWD w sesjach)."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from tsdfwd_tools.cli.main import main
from tsdfwd_tools.common.config import ConfigError
from tsdfwd_tools.common.config_n4 import build_n4_config


def _write_inputs(tmp_path, n_sessions=6, per_session=10, tsd_date="2025-07-20", fwd_date="2025-07-01", with_second_run=False):
    n = 2600
    chain = np.arange(n, dtype=float)
    lat = 50.0 + chain / 111200.0
    d0_profile = lambda pos: 100.0 + 10.0 * np.sin(pos / 300.0)           # noqa: E731  zmienny wzdluz drogi (brak stalych wejsc)
    rows = pd.DataFrame(dict(chainage_m=chain, lat=lat, lon=19.0, d0=d0_profile(chain), gof=0.9, t12_c=20.0, speed_kmh=72.0))
    rows_path = tmp_path / "T4202507200001_rows.csv"
    rows.to_csv(rows_path, index=False)
    paths = [rows_path]
    if with_second_run:
        rows2 = rows.copy()
        rows2["d0"] = 1.1 * rows["d0"]
        p2 = tmp_path / "T4202507210002_rows.csv"
        rows2.to_csv(p2, index=False)
        paths.append(p2)
    recs = []
    rng = np.random.default_rng(3)
    sid = 0
    for k in range(n_sessions):
        for i in range(per_session):
            pos = 300.0 + 10.0 * k + 200.0 * i            # polozenie plyty wzdluz drogi [m]
            sid += 1
            # antena HWD 1 m przed plyta: stacja zapisana z GPS = plyta + 1 m wzdluz jazdy
            ant = pos + 1.0
            recs.append(dict(station_id=sid, session_id=k + 1, station_m=(pos - 300.0) / 1000.0, latitude=50.0 + ant / 111200.0,
                             longitude=19.0, measured_at=f"{fwd_date}T10:{i:02d}:00", device="8082-119", date=fwd_date,
                             D0=2.0 * d0_profile(pos) * (1 + rng.normal(0, 0.02)), t_mid_c=20.0))
    stations = pd.DataFrame(recs)
    st_path = tmp_path / "stations.csv"
    stations.to_csv(st_path, index=False)
    return paths, st_path


def _cfg(tmp_path, paths, st_path, **over):
    cfg = {"tool": "tsd_fwd_compare", "mode": "geometry",
           "geometry": {"tsd_rows": [str(p) for p in paths], "fwd_stations_csv": str(st_path), "date_override": None},
           "measures": {"n_boot": 50}, "uncertainty": {"replicates": 99},
           "null_checks": {"n_boot": 50},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    for k, v in over.items():
        cfg[k] = {**cfg.get(k, {}), **v}
    p = tmp_path / "n4g.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_geometry_mode_end_to_end(tmp_path):
    paths, st_path = _write_inputs(tmp_path)
    cfg = _cfg(tmp_path, paths, st_path)
    assert main(["tsd_fwd_compare", "--config", str(cfg)]) == 0
    out = tmp_path / "out"
    for name in ("agreement.csv", "geometry_pairs.csv", "fwd_plate_positions.csv", "tsd_passes.csv", "corridors.csv",
                 "geometry_null_pairs.csv", "pairs_corrected.csv", "meta.json", "report.html", "null_checks.csv"):
        assert (out / name).is_file(), name
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["mode"] == "geometry" and meta["geometry"]["axis"]["source"] == "tsd_runs" and meta["geometry"]["lag_m"] == -4.8
    assert meta["geometry"]["n_pairs"] == 60 and meta["n_valid_pairs"] == 60 and meta["n_sessions"] == 6
    agr = pd.read_csv(out / "agreement.csv").set_index("variant")
    assert agr.loc["none", "median_ratio"] == pytest.approx(2.0, rel=0.03)               # FWD / TSD = 200 / 100
    gp = pd.read_csv(out / "geometry_pairs.csv")
    assert (gp["layer"] == "A").all() and (gp["win5_n"] >= 9).all() and (gp["same_year"] == 1).all()
    plate = pd.read_csv(out / "fwd_plate_positions.csv")
    assert (plate["pos_source"] == "dmi").all() and (plate["era"] == "hwd").all()
    nulls = pd.read_csv(out / "null_checks.csv")
    assert {"real", "shift_minus200", "shift_plus200"} <= set(nulls["pair_kind"])


def test_geometry_mode_filters_year_and_layers(tmp_path):
    paths, st_path = _write_inputs(tmp_path, tsd_date="2025-07-20", fwd_date="2024-06-01")
    cfg = _cfg(tmp_path, paths, st_path, geometry={"same_year_only": True})
    with pytest.raises(ConfigError, match="po filtrach"):
        from tsdfwd_tools.common.config_n4 import load_n4_config
        from tsdfwd_tools.compare.pipeline import run_n4
        run_n4(load_n4_config(cfg), dry_run=True)
    cfg2 = _cfg(tmp_path, paths, st_path, geometry={"same_year_only": False})
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    res = run_n4(load_n4_config(cfg2), dry_run=True)
    assert res["meta"]["geometry"]["n_pairs"] == 60                                       # +-1 rok dopuszczony i oznaczony
    assert (res["geo_pairs"]["same_year"] == 0).all()


def test_geometry_mode_two_runs_dates_from_names_and_calib(tmp_path):
    paths, st_path = _write_inputs(tmp_path, with_second_run=True)
    cfg = _cfg(tmp_path, paths, st_path)
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    res = run_n4(load_n4_config(cfg), dry_run=True)
    gp = res["geo_pairs"]
    assert set(gp["dt_days"]) == {19.0, 20.0} and set(gp["calib_interval"]) == {"K2025-05-27"}
    assert len(res["geo_passes"]) == 2 and res["meta"]["geometry"]["n_pairs"] == 120


def test_geometry_config_errors(tmp_path):
    with pytest.raises(ConfigError, match="tsd_rows"):
        build_n4_config({"mode": "geometry"})
    with pytest.raises(ConfigError, match="fwd_stations_csv"):
        build_n4_config({"mode": "geometry", "geometry": {"tsd_rows": ["a.csv"]}})
    with pytest.raises(ConfigError, match="eps_variant"):
        build_n4_config({"mode": "geometry", "geometry": {"tsd_rows": ["a.csv"], "fwd_stations_csv": "b.csv", "eps_variant": "x"}})
    paths, st_path = _write_inputs(tmp_path)
    df = pd.read_csv(paths[0])
    df["chainage_m"] = df["chainage_m"].iloc[::-1].to_numpy()                             # pikietaz malejacy
    df.to_csv(paths[0], index=False)
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    with pytest.raises(ConfigError, match="niemalejacy"):
        run_n4(load_n4_config(_cfg(tmp_path, paths, st_path)), dry_run=True)


def test_geometry_missing_date_is_an_error(tmp_path):
    paths, st_path = _write_inputs(tmp_path)
    new = paths[0].with_name("przejazd_bez_daty_rows.csv")
    paths[0].rename(new)
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    with pytest.raises(ConfigError, match="brak daty"):
        run_n4(load_n4_config(_cfg(tmp_path, [new], st_path)), dry_run=True)


def test_geometry_sections_detected_reported_and_used_as_filter(tmp_path):
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    paths, st_path = _write_inputs(tmp_path)
    assert main(["tsd_fwd_compare", "--config", str(_cfg(tmp_path, paths, st_path))]) == 0
    out = tmp_path / "out"
    sec = pd.read_csv(out / "sections.csv")
    assert len(sec) == 6 and (sec["lane_class"] == "same").all() and (sec["review_status"] == "unreviewed").all()
    html = (out / "section_review.html").read_text(encoding="utf-8")
    assert html.count("<svg") == 18 and "odcinek 6" in html
    gp = pd.read_csv(out / "geometry_pairs.csv")
    assert (gp["in_section"] == 1).all() and gp["section_id"].notna().all()
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["geometry"]["sections"]["n_sections"] == 6 and meta["geometry"]["sections"]["pairs_in_section"] == 60

    # decyzje przegladu: odrzucenie jednej sesji + require_section -> jej pary znikaja z porownania
    review = tmp_path / "review.csv"
    pd.DataFrame([dict(session_id=3, run_id="T4202507200001", status="rejected")]).to_csv(review, index=False)
    cfg = _cfg(tmp_path, paths, st_path, geometry={"sections": {"review_csv": str(review), "require_section": True}})
    res = run_n4(load_n4_config(cfg), dry_run=True)
    assert res["meta"]["geometry"]["n_pairs"] == 50 and 3 not in set(res["pairs"]["session"])
    assert set(res["geo_sections"]["review_status"]) == {"unreviewed", "rejected"}
    cfg_off = _cfg(tmp_path, paths, st_path, geometry={"sections": {"enabled": False}})
    res_off = run_n4(load_n4_config(cfg_off), dry_run=True)
    assert res_off["meta"]["geometry"]["n_pairs"] == 60 and "in_section" not in res_off["geo_pairs"]


def test_geometry_mode_aligns_passes_with_profile(tmp_path):
    """Dwa przejazdy tej samej drogi z identycznym GPS; profil drugiego przesuniety o 3 m: wyrownanie ustawia wspolny s_ref."""
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    n, shift = 5000, 3
    rng = np.random.default_rng(11)
    walk = np.cumsum(rng.normal(size=n + 60))
    chain = np.arange(n, dtype=float)
    lat = 50.0 + chain / 111200.0
    paths = []
    for name, off, noise in (("T4202507200001_rows.csv", 0, 0.1), ("T4202507200002_rows.csv", shift, 0.1)):
        prof = walk[30 - off + np.arange(n)] + rng.normal(0, noise, n)               # profil drugiego przejazdu przesuniety o `shift` m
        pd.DataFrame(dict(chainage_m=chain, lat=lat, lon=19.0, d0=100.0, gof=0.9, t12_c=20.0, profile=prof)).to_csv(tmp_path / name, index=False)
        paths.append(tmp_path / name)
    pos = np.arange(300.0, 4600.0, 200.0)
    pd.DataFrame(dict(station_id=np.arange(len(pos)), session_id=1, station_m=(pos - 300.0) / 1000.0, latitude=50.0 + (pos + 1.0) / 111200.0,
                      longitude=19.0, measured_at="2025-07-01T10:00:00", device="8082-119", date="2025-07-01", D0=200.0,
                      t_mid_c=20.0)).to_csv(tmp_path / "st.csv", index=False)
    cfg = {"tool": "tsd_fwd_compare", "mode": "geometry",
           "geometry": {"tsd_rows": [str(p) for p in paths], "fwd_stations_csv": str(tmp_path / "st.csv"), "sections": {"enabled": False}},
           "measures": {"n_boot": 20}, "uncertainty": {"replicates": 29}, "null_checks": {"n_boot": 20},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    res = run_n4(load_n4_config(p), dry_run=True)
    tp = res["geo_passes"].set_index("pass_id")
    assert res["meta"]["geometry"]["align"]["enabled"] and res["meta"]["geometry"]["align"]["aligned"] == 2
    assert set(tp["align_ref"]) == {"reference", "profile_ref"} and (tp["align_note"].isna()).all()
    assert abs(tp["delta_med"].iloc[0] - tp["delta_med"].iloc[1]) == pytest.approx(shift, abs=0.25)
    assert res["geo_align_blocks"]["used"].sum() >= 4 and "wyrownanie profilem" in res["meta"]["geometry"]["note"]
    # bez kolumny profilu: tryb auto nie wyrownuje; geometry.align: true wymaga profilu
    for pth in paths:
        pd.read_csv(pth).drop(columns="profile").to_csv(pth, index=False)
    res2 = run_n4(load_n4_config(p), dry_run=True)
    assert not res2["meta"]["geometry"]["align"]["enabled"] and "align_ref" not in res2["geo_passes"]
    cfg["geometry"]["align"] = "true"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(ConfigError, match="profilu"):
        run_n4(load_n4_config(p), dry_run=True)


def test_geometry_mode_merges_duplicate_lane_and_uses_only_own_lane_rows(tmp_path):
    from tsdfwd_tools.common.config_n4 import load_n4_config
    from tsdfwd_tools.compare.pipeline import run_n4
    n = 3000
    chain = np.arange(n, dtype=float)
    lat = 50.0 + chain / 111200.0
    pd.DataFrame(dict(chainage_m=chain, lat=lat, lon=19.0, d0=100.0, gof=0.9, t12_c=20.0)).to_csv(tmp_path / "T4202507200001_rows.csv", index=False)
    c2 = np.arange(1000.0, 1600.0)                                              # krotki duplikat pasa 2,2 m obok (na wschod)
    pd.DataFrame(dict(chainage_m=c2, lat=50.0 + c2 / 111200.0, lon=19.0 + 2.2 / (111200.0 * np.cos(np.radians(50.0))), d0=110.0, gof=0.9,
                      t12_c=20.0)).to_csv(tmp_path / "T4202507200002_rows.csv", index=False)
    rng = np.random.default_rng(1)
    recs, sid = [], 0
    for k in range(3):
        for i, pos in enumerate((400.0, 800.0, 1200.0, 1400.0, 2000.0, 2400.0)):
            sid += 1
            recs.append(dict(station_id=sid, session_id=k + 1, station_m=(pos - 400.0) / 1000.0, latitude=50.0 + (pos + 1.0) / 111200.0, longitude=19.0,
                             measured_at=f"2025-07-01T10:{i:02d}:00", device="8082-119", date="2025-07-01",
                             D0=200.0 * (1 + rng.normal(0, 0.03)), t_mid_c=20.0))
    pd.DataFrame(recs).to_csv(tmp_path / "st.csv", index=False)
    cfg = {"tool": "tsd_fwd_compare", "mode": "geometry",
           "geometry": {"tsd_rows": [str(tmp_path / "T4202507200001_rows.csv"), str(tmp_path / "T4202507200002_rows.csv")],
                        "fwd_stations_csv": str(tmp_path / "st.csv"), "sections": {"enabled": False}},
           "measures": {"n_boot": 20}, "uncertainty": {"replicates": 29}, "null_checks": {"n_boot": 20},
           "output": {"dir": str(tmp_path / "out"), "overwrite": True}}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    res = run_n4(load_n4_config(p), dry_run=False)
    mg = res["geo_merges"]
    assert len(mg) == 1 and res["meta"]["geometry"]["axis"]["n_dissolved"] == 1 and res["meta"]["geometry"]["axis"]["merged_lanes"]
    ps = res["geo_passes"].set_index("file_id")
    assert ps.loc["T4202507200002", "wide_share"] > 0.7 and ps.loc["T4202507200001", "wide_share"] == 0.0
    assert set(res["geo_pairs"]["file_id"]) == {"T4202507200001"}                  # pary tylko z wierszami pasa wlasnego
    assert (tmp_path / "out" / "corridor_merges.csv").is_file()
    cfg["geometry"]["merge_lanes"] = False
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    res2 = run_n4(load_n4_config(p), dry_run=True)
    assert res2["geo_merges"] is None and len(res2["geo_corridors"]) == 2 and len(res["geo_corridors"]) == 1       # bez scalania: dwa korytarze
