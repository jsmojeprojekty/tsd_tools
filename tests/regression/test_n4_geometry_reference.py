"""Testy regresji N4 (tryb geometry): polozenie plyty FWD, przypisanie wierszy TSD do korytarzy, pary kandydackie i pary zerowe
wzgledem tabel referencyjnych projektu bazy (tylko odczyt, SQLite mode=ro).

Tabele: baza_analizy_e2b.db (fwd_plate_position_e2b, golden_pair_candidates, e1... e2b1_null_map), baza_produkty_v1.db
(ref_corridor_points, tsd_passes, tsd_pass_calib, tsd_sref), baza_odcinki_v4.db (stacje FWD, GoF wierszy TSD)."""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.compare import fwd_position as FP
from tsdfwd_tools.compare import geo as G
from tsdfwd_tools.compare import pairing as PA

pytestmark = pytest.mark.reference

MAX_CORRIDOR = 29            # prefiks korytarzy 0..29 = pair_id 1..5632 (kolejnosc pair_id wazna dla rng par zerowych)
TSD_FILES = (25, 40, 77)     # pliki z korytarzy 0-3 (kontrola przypisania wierszy TSD)


@pytest.fixture(scope="module")
def dbs(sql_root):
    base = sql_root / "bazy"
    names = {"prod": "baza_produkty_v1.db", "e2b": "baza_analizy_e2b.db", "v4": "baza_odcinki_v4.db"}
    for n in names.values():
        if not (base / n).is_file():
            pytest.skip(f"brak {base / n}")

    def ro(n):
        return sqlite3.connect(f"file:{(base / n).as_posix()}?mode=ro", uri=True)

    conns = {k: ro(v) for k, v in names.items()}
    yield conns
    for c in conns.values():
        c.close()


@pytest.fixture(scope="module")
def corridors(dbs):
    pts = pd.read_sql("SELECT corridor_id, s, x_2180, y_2180, heading_deg FROM ref_corridor_points ORDER BY corridor_id, s",
                      dbs["prod"])
    out = []
    for cid, g in pts.groupby("corridor_id"):
        c = G.Corridor(int(cid), g.x_2180.to_numpy(), g.y_2180.to_numpy(), [])
        c.set_geom(g.x_2180.to_numpy(), g.y_2180.to_numpy(), hd=g.heading_deg.to_numpy())
        out.append(c)
    return out


@pytest.fixture(scope="module")
def plate(dbs, corridors):
    ref_ids = pd.read_sql("SELECT station_id FROM fwd_plate_position_e2b WHERE dataset = 'odcinki'", dbs["e2b"])
    st = pd.read_sql(
        "SELECT st.station_id, st.session_pk AS session_id, st.station_m, st.latitude AS lat, st.longitude AS lon, "
        "st.heading_deg, st.time, se.date_start AS date, ff.trailer AS device, st.in_concrete_zone "
        "FROM fwd_stations st JOIN fwd_sessions se ON se.session_pk = st.session_pk JOIN fwd_files ff ON ff.file_id = st.file_id "
        "ORDER BY st.session_pk, st.time, st.station_id", dbs["v4"])
    st = st[st.station_id.isin(ref_ids.station_id)]
    return FP.fwd_plate_positions(corridors, st)[0]


def test_fwd_plate_position_matches_e2b1_geometry(dbs, plate):
    """T-N4-13: wszystkie 46826 stacji zbioru `odcinki`: K1-K4 (rzut anteny, kierunek, plyta, dystansomierz, sigma_long)."""
    ref = pd.read_sql("SELECT * FROM fwd_plate_position_e2b WHERE dataset = 'odcinki'", dbs["e2b"])
    m = plate.merge(ref, on="station_id", suffixes=("", "_ref"))
    assert len(m) == len(ref) == len(plate)
    for col in ("lane_match", "era", "pos_source", "direction"):
        assert (m[col].astype(str) == m[col + "_ref"].astype(str)).all(), col
    assert ((m["corridor_id"] == m["corridor_id_ref"].fillna(-1).astype(int))).all()
    assert (m["run_id"].fillna(-1).astype(int) == m["run_id_ref"].fillna(-1).astype(int)).all()
    for col, tol in (("s_ant", 1e-6), ("lat_ant", 1e-6), ("s_plate_gps", 1e-6), ("s_dmi", 1e-6), ("s_fwd", 1e-6),
                     ("residual_gps_m", 1e-6), ("sigma_a", 1e-6), ("sigma_long", 1e-4), ("sigma_long_hwd_b", 1e-4)):
        a, b = m[col].to_numpy(float), m[col + "_ref"].to_numpy(float)
        assert (np.isfinite(a) == np.isfinite(b)).all(), col
        both = np.isfinite(a)
        assert np.abs(a[both] - b[both]).max() < tol, col


def test_tsd_rows_assignment_matches_tsd_sref(dbs, corridors):
    """T-N4-15: prepare_run + assign_run na referencyjnych korytarzach odtwarza korytarz i s_ref_gps z tabeli tsd_sref
    (tolerancja: wspolrzedne korytarzy w bazie zapisane z dokladnoscia ~mm)."""
    for fid in TSD_FILES:
        rows = pd.read_sql(f"SELECT tsd_id, chainage_m, latitude, longitude FROM tsd_measurements WHERE file_id = {fid} "
                           "ORDER BY tsd_id", dbs["v4"])
        ref = pd.read_sql(f"SELECT tsd_id, corridor_id, s_ref_gps, lateral_m, lane_fit FROM tsd_sref WHERE file_id = {fid} "
                          "ORDER BY tsd_id", dbs["prod"]).set_index("tsd_id").reindex(rows.tsd_id)
        run = G.prepare_run(rows.chainage_m.to_numpy(float), rows.latitude.to_numpy(float), rows.longitude.to_numpy(float))
        cid, s, lat, _ = G.assign_run(corridors, run, True)
        lane = (ref.lane_fit == "lane").to_numpy()
        rc = ref.corridor_id.fillna(-1).astype(int).to_numpy()
        assert (cid[lane] == rc[lane]).mean() > 0.9995
        both = lane & (cid >= 0) & (cid == rc)
        assert np.nanmax(np.abs(s[both] - ref.s_ref_gps.to_numpy(float)[both])) < 0.02
        assert np.nanmax(np.abs(lat[both] - ref.lateral_m.to_numpy(float)[both])) < 0.003


@pytest.fixture(scope="module")
def tsd_pass_data(dbs):
    prod = dbs["prod"]
    passes = pd.read_sql(
        "SELECT p.pass_id, p.file_id, p.corridor_id, p.file_date AS date, p.v_med, p.recorder_group, c.calib_interval, "
        "c.calib_interval_uncertain, c.data_tier FROM tsd_passes p LEFT JOIN tsd_pass_calib c ON c.pass_id = p.pass_id "
        f"WHERE p.corridor_id IS NOT NULL AND p.corridor_id <= {MAX_CORRIDOR}", prod)
    v4_path = dbs["v4"].execute("PRAGMA database_list").fetchone()[2]
    prod.execute(f"ATTACH DATABASE 'file:{v4_path.replace(chr(92), '/')}?mode=ro' AS v4")
    try:
        rows = pd.read_sql(
            "SELECT s.pass_id, s.tsd_id, s.s_ref, s.lateral_m, m.goodness_of_fit AS gof FROM tsd_sref s "
            "JOIN v4.tsd_measurements m ON m.tsd_id = s.tsd_id WHERE s.lane_fit = 'lane' AND s.s_ref IS NOT NULL "
            f"AND s.pass_id IS NOT NULL AND s.corridor_id <= {MAX_CORRIDOR}", prod)
    finally:
        prod.execute("DETACH DATABASE v4")
    pass_rows = {}
    for pid, g in rows.groupby("pass_id"):
        g = g.sort_values("s_ref", kind="stable")
        pass_rows[int(pid)] = dict(s=g.s_ref.to_numpy(float), tsd_id=g.tsd_id.to_numpy(np.int64),
                                   lat=g.lateral_m.to_numpy(float), gof=g.gof.to_numpy(float))
    return passes, pass_rows


def test_window_values_match_z15_pairs(sql_root, local_paths, dbs, plate, tsd_pass_data):
    """T-N4-16: mediana d0 (B_1510off) w oknie W5 po s_ref odtwarza `d0_tsd` z Z15 dla par korytarzy 0..29. Okno wartosci
    jest tu zdefiniowane po s_ref (S-N4-4, decyzja E0), a zrodlo uzywalo zakresu tsd_id min..max — pojedyncze pary, w ktorych
    zakres obejmuje wiersze spoza okna odleglosciowego, roznia sie (poza korytarzami 0..29: 7 z 2895 par dla korytarzy 0..80)."""
    from pathlib import Path
    z15 = Path(local_paths.get("doktorat_root", "")) / "wymiana" / "wyniki" / "z15" / "Z15_temperatury_par.csv"
    b1510 = sql_root / "bazy" / "baza_odcinki_b1510off_v2.db"
    if not z15.is_file() or not b1510.is_file():
        pytest.skip("brak Z15_temperatury_par.csv albo baza_odcinki_b1510off_v2.db")
    passes, pass_rows = tsd_pass_data
    cand = PA.build_candidates(plate[plate.corridor_id <= MAX_CORRIDOR], passes, pass_rows)
    conn = sqlite3.connect(f"file:{b1510.as_posix()}?mode=ro", uri=True)
    pr2 = {}
    for pid, pr in pass_rows.items():
        d0 = {}
        ids = pr["tsd_id"].tolist()
        for i in range(0, len(ids), 20000):
            chunk = ids[i:i + 20000]
            for t, v in conn.execute("SELECT tsd_id, d_d0 FROM b1510off_measurements WHERE tsd_id IN (%s)" % ",".join(map(str, chunk))):
                d0[t] = v
        pr2[pid] = dict(pr, d0=np.array([np.nan if d0.get(t) is None else d0[t] for t in ids], float))
    conn.close()
    vals = PA.pair_values(cand, pr2)
    z = pd.read_csv(z15, encoding="utf-8-sig", usecols=["pair_id", "d0_tsd"])
    m = vals.merge(z, on="pair_id")
    assert len(m) >= 300
    a, b = m.value.to_numpy(float), m.d0_tsd.to_numpy(float)
    assert (np.isfinite(a) == np.isfinite(b)).all()
    assert (np.abs(a - b) < 1e-6).mean() >= 0.99


def test_candidates_and_null_pairs_match_golden_pairs(dbs, plate, tsd_pass_data):
    """T-N4-14: kandydaci na pary (okna +-1/2,5/5 m po s_ref, warstwy A/B/C/X, dt, same_year) i pary zerowe (+-200 m,
    permutacja z seedem 20261017) dla korytarzy 0..29 = prefiks pair_id 1..5632 w `golden_pair_candidates`."""
    passes, pass_rows = tsd_pass_data
    cand = PA.build_candidates(plate[plate.corridor_id <= MAX_CORRIDOR], passes, pass_rows)
    ref = pd.read_sql(f"SELECT * FROM golden_pair_candidates WHERE dataset = 'odcinki' AND corridor_id <= {MAX_CORRIDOR}",
                      dbs["e2b"])
    assert len(cand) == len(ref) == 5632
    assert (cand.pair_id.to_numpy() == ref.pair_id.to_numpy()).all()                    # ta sama kolejnosc
    assert (cand.station_id.to_numpy() == ref.station_id.to_numpy()).all()
    assert (cand.pass_id.to_numpy() == ref.pass_id.to_numpy()).all()
    for col in ("nearest_tsd_id", "win1_n", "win2_5_n", "win5_n", "win5_tsd_id_min", "win5_tsd_id_max", "same_year", "tsd_year",
                "fwd_year", "win1_tsd_id_min", "win2_5_tsd_id_max"):
        assert (cand[col].astype(float).fillna(-9).to_numpy() == ref[col].astype(float).fillna(-9).to_numpy()).all(), col
    for col in ("layer", "calib_interval", "era", "device", "lane_match", "recorder_group", "data_tier"):
        assert (cand[col].astype(str).to_numpy() == ref[col].astype(str).to_numpy()).all(), col
    hwd = cand.era == "hwd"
    assert (cand.loc[hwd, "layer_hwd_b"].to_numpy() == ref.loc[hwd.to_numpy(), "layer_hwd_b"].to_numpy()).all()
    for col, tol in (("s_fwd", 1e-6), ("lat_fwd", 1e-9), ("ds", 1e-6), ("win5_gof05_share", 1e-12), ("win5_lat_tsd_median", 1e-9),
                     ("dlat", 1e-9), ("sigma_long_fwd", 1e-4), ("dt_days", 0), ("v_med", 1e-9), ("win1_gof05_share", 1e-12)):
        a, b = cand[col].to_numpy(float), ref[col].to_numpy(float)
        assert (np.isfinite(a) == np.isfinite(b)).all(), col
        both = np.isfinite(a)
        assert np.abs(a[both] - b[both]).max() <= tol, col

    nulls = PA.build_null_pairs(cand, pass_rows)
    rn = pd.read_sql(f"SELECT * FROM e2b1_null_map WHERE dataset = 'odcinki' AND pair_id <= {int(ref.pair_id.max())}", dbs["e2b"])
    assert len(nulls) == len(rn) == 16659
    mn = nulls.merge(rn, on=["pair_id", "null_type"], suffixes=("", "_ref"))
    assert len(mn) == len(rn)
    assert np.abs(mn.center_s - mn.center_s_ref).max() < 1e-6                            # w tym permutacje (rng wspolny)
    assert (mn.win5_n == mn.win5_n_ref).all()
    assert (mn.win5_tsd_id_min.fillna(-1) == mn.win5_tsd_id_min_ref.fillna(-1)).all()


def test_detect_sections_reproduces_445_sections_of_v4(dbs):
    """T-N4-11: detect_sections (Tab. 3.2) na calej bazie v4 = tabela `tsd_fwd_sections`: 445 sekcji, wszystkie miary identyczne;
    167 sekcji z przegladu recznym (`confirmed`) to dokladnie sekcje o pasie same/adjacent kierunku same (87 + 80)."""
    from tsdfwd_tools.compare import sections as SEC
    v4 = dbs["v4"]
    ref = pd.read_sql("SELECT * FROM tsd_fwd_sections", v4)
    st = pd.read_sql(
        "SELECT s.station_id, s.session_pk, s.latitude AS lat, s.longitude AS lon, s.heading_deg AS heading, s.station_m, "
        "sess.date_start, sess.date_end FROM fwd_stations s JOIN fwd_sessions sess ON sess.session_pk = s.session_pk "
        "WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL ORDER BY s.session_pk, s.station_m, s.station_id", v4)
    sessions = {k: g.reset_index(drop=True) for k, g in st.groupby("session_pk", sort=True)}
    info = {k: (g.date_start.iloc[0], g.date_end.iloc[0]) for k, g in sessions.items()}
    files = pd.read_sql("SELECT file_id, file_date FROM tsd_files", v4)
    rows = pd.read_sql("SELECT file_id, latitude AS lat, longitude AS lon, heading_deg AS heading, chainage_m AS chainage "
                       "FROM tsd_measurements WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY file_id, chainage_m", v4)
    runs = {k: g.reset_index(drop=True) for k, g in rows.groupby("file_id", sort=True)}
    del rows
    mine, _, cnt = SEC.detect_sections(runs, dict(zip(files.file_id, files.file_date)), sessions, info)
    assert len(mine) == len(ref) == 445
    m = mine.merge(ref, left_on=["session_id", "run_id"], right_on=["session_pk", "tsd_file_id"], suffixes=("", "_ref"))
    assert len(m) == 445
    for col in ("direction", "lane_class", "fwd_matched", "fwd_total", "fwd_in_overlap"):
        assert (m[col].astype(str) == m[col + "_ref"].astype(str)).all(), col
    for col in ("spearman_corr", "coverage_pct", "coverage_full_pct", "station_m_min", "station_m_max", "chainage_m_min",
                "chainage_m_max", "median_xtrack_m", "mean_bearing_diff"):
        assert np.nanmax(np.abs(m[col].to_numpy(float) - m[col + "_ref"].to_numpy(float))) < 1e-9, col
    rev = pd.read_sql("SELECT section_id, status FROM tsd_fwd_section_review WHERE status = 'confirmed'", v4)
    assert len(rev) == 167
    conf = ref[ref.section_id.isin(rev.section_id)]
    assert set(conf.direction) == {"same"} and set(conf.lane_class) == {"same", "adjacent"}
    eligible = ref[(ref.direction == "same") & ref.lane_class.isin(["same", "adjacent"])]
    assert len(eligible) == 167                                       # recall i precyzja wzgledem przegladu recznego: 167/167


def test_lambda_estimator_reproduces_report_value(sql_root, dbs):
    """T-N4-09: lambda d0 = 0,11787 z powtorzen: sigma_TSD 0,296408 (2015 par binow 10 m po s_ref, |dt| <= 1 d, poza betonem) i
    sigma_FWD 0,101763 (128 par okien FWD od 2024) odtworzone z surowych tabel; wartosc = `e2b2_lambda.csv` (d0)."""
    import math
    from tsdfwd_tools.compare import lambda_est as LAM
    b15 = sql_root / "bazy" / "baza_odcinki_b1510off_v2.db"
    if not b15.is_file():
        pytest.skip("brak baza_odcinki_b1510off_v2.db")
    prod, v4 = dbs["prod"], dbs["v4"]
    p = LAM.LambdaParams()
    # --- FWD: stacje pasa 'same' z fwd_sref, D0 = srednia d1*50/F zrzutow nieosadczych, temperatura powierzchni mediana 3
    dr = pd.read_sql("SELECT station_id, d1, force_kn FROM fwd_drops WHERE is_seating = 0", v4)
    dr = dr[(dr.d1 > 0) & (dr.force_kn > 0)]
    ld0 = (dr.d1 * 50.0 / dr.force_kn).groupby(dr.station_id).mean().map(math.log)
    v4_path = v4.execute("PRAGMA database_list").fetchone()[2].replace("\\", "/")
    prod.execute(f"ATTACH DATABASE 'file:{v4_path}?mode=ro' AS v4")
    try:
        meta = pd.read_sql("SELECT s.station_id, s.session_pk AS session, pp.device, pp.fwd_date AS date, s.in_concrete_zone AS conc "
                           "FROM v4.fwd_stations s JOIN main.fwd_station_position pp ON pp.station_id = s.station_id", prod)
    finally:
        prod.execute("DETACH DATABASE v4")
    st = pd.read_sql("SELECT f.station_id AS station, f.corridor_id AS corridor, f.s_ref AS s, t.surface_temp_med3 AS temp "
                     "FROM fwd_sref f LEFT JOIN fwd_station_temp t ON t.station_id = f.station_id WHERE f.lane_match = 'same'", prod)
    st = st[st.s.notna() & st.station.isin(ld0.index)].merge(meta, left_on="station", right_on="station_id")
    st["ld0"] = st.station.map(ld0)
    st["date"] = st["date"].astype(str).str[:10]
    st["conc"] = st["conc"].fillna(0).astype(int)
    fwd = LAM.fwd_repeat_sigma(st.reset_index(drop=True), p)
    assert fwd["n_pairs"] == 128 and fwd["sigma_within"] == pytest.approx(0.101763, abs=1e-6)

    # --- TSD: biny 10 m po s_ref (n >= 5), mediana d0 B_1510off, czas biny z tsd_bin_stats (jak e1_sref), pliki ok bez align_fail
    rows = pd.read_sql("SELECT tsd_id, corridor_id, pass_id, s_ref FROM tsd_sref WHERE s_ref IS NOT NULL AND corridor_id IS NOT NULL "
                       "AND pass_id IS NOT NULL", prod)
    conn = sqlite3.connect(f"file:{b15.as_posix()}?mode=ro", uri=True)
    d0 = pd.read_sql("SELECT tsd_id, d_d0 FROM b1510off_measurements", conn)
    ok_files = {r[0] for r in conn.execute("SELECT f.file_id FROM b1510off_files f JOIN b1510off_alignment a ON a.file_id = f.file_id "
                                           "WHERE f.status = 'ok' AND a.align_fail = 0")}
    conn.close()
    rows = rows.merge(d0, on="tsd_id", how="left").sort_values("pass_id", kind="stable")
    pf = dict(prod.execute("SELECT pass_id, file_id FROM tsd_passes").fetchall())
    pass_rows, dates, corr = {}, {}, {}
    for pid, g in rows.groupby("pass_id", sort=True):
        pass_rows[int(pid)] = dict(s=g.s_ref.to_numpy(float), d0=g.d_d0.to_numpy(float))
        corr[int(pid)] = int(g.corridor_id.iloc[0])
        dates[int(pid)] = "2025-01-01"                                  # zastapione ponizej czasem biny z tsd_bin_stats
    bins = LAM.tsd_bin_table(pass_rows, dates, corr, p)
    bstat = pd.read_sql("SELECT corridor_id, bin_id, pass_id, t_med, concrete_share FROM tsd_bin_stats", prod)
    b = bins.drop(columns=["t_eff", "concrete_share"]).merge(bstat, on=["corridor_id", "bin_id", "pass_id"], how="left")
    b["t_eff"] = b["t_med"]
    b = b[b.pass_id.map(pf).isin(ok_files) & b.t_eff.notna()]
    tsd = LAM.tsd_repeat_sigma(b, p)
    assert tsd["n_pairs"] == 2015 and tsd["sigma"] == pytest.approx(0.296408, abs=1e-6)
    ref = pd.read_sql("SELECT sigma_tsd, sigma_fwd, lambda_val, n_pairs_tsd, n_fwd_pairs FROM e2b2_lambda WHERE metric = 'd0'", dbs["e2b"]).iloc[0]
    lam = LAM.lambda_from_sigmas(fwd["sigma_within"], tsd["sigma"])
    assert lam == pytest.approx(ref.lambda_val, abs=1e-9) and lam == pytest.approx(0.11786960020790811, abs=1e-9)
    assert tsd["n_pairs"] == ref.n_pairs_tsd and fwd["n_pairs"] == ref.n_fwd_pairs


@pytest.mark.parametrize("cid", [0, 1, 2, 3, 7, 8, 4])
def test_profile_alignment_reproduces_tsd_sref(dbs, cid):
    """T-N4-17: wyrownanie przejsc profilem (`align_corridor` + `apply_alignment`) na przejsciach korytarza odtwarza `tsd_passes`
    (zrodlo wyrownania, liczba blokow, centrowanie) i `s_ref` z `tsd_sref` (7 korytarzy, 100 przejsc; tol. s_ref 5 mm)."""
    from tsdfwd_tools.compare import align as AL
    prod, v4 = dbs["prod"], dbs["v4"]
    tp = pd.read_sql(f"SELECT * FROM tsd_passes WHERE corridor_id = {cid} ORDER BY pass_id", prod).set_index("pass_id")
    length = prod.execute(f"SELECT length_m FROM ref_corridors WHERE corridor_id = {cid}").fetchone()[0]
    rows = pd.read_sql(f"SELECT tsd_id, file_id, pass_id, s_ref_gps, s_ref, align_source FROM tsd_sref WHERE corridor_id = {cid} "
                       "AND pass_id IS NOT NULL ORDER BY tsd_id", prod)
    files = sorted(rows.file_id.unique())
    prof = pd.read_sql(f"SELECT tsd_id, file_id, profile1 FROM tsd_measurements WHERE file_id IN ({','.join(map(str, files))}) "
                       "ORDER BY file_id, tsd_id", v4)
    det = {}
    for _, g in prof.groupby("file_id"):
        det.update(dict(zip(g.tsd_id.to_numpy(), AL.detrend_profile(g.profile1.to_numpy(float)))))
    rows["prof"] = rows.tsd_id.map(det)
    passes = [dict(pass_id=int(pid), s=g.s_ref_gps.to_numpy(float), prof=g.prof.to_numpy(float), idx=g.index.to_numpy())
              for pid, g in rows.groupby("pass_id", sort=True)]
    cen = AL.align_corridor(passes, float(length))
    assert cen == pytest.approx(float(tp.centering_m.iloc[0]), abs=1e-4)
    for p in passes:
        ref = tp.loc[p["pass_id"]]
        sref, src, note = AL.apply_alignment(p, cen)
        assert p["align_ref"] == ref.align_ref and p["n_ok"] == ref.n_blocks_ok and p["n_blocks"] == ref.n_blocks
        assert note == (None if pd.isna(ref.align_note) else ref.align_note)
        r = rows.loc[p["idx"]]
        ok = r.align_source.to_numpy(object) != "odometer_anchor"                 # drogomierz w strefach zlego GPS: poza zakresem
        assert np.nanmax(np.abs(sref - r.s_ref.to_numpy(float))[ok]) < 0.005
        assert (src[ok] == r.align_source.to_numpy(object)[ok]).all()


def test_axis_with_lane_merging_reproduces_whole_reference_network(dbs):
    """T-N4-18: os referencyjna zbudowana od zera z 239 plikow TSD (bez pliku wykluczonego qc_gps_shifted) = baza produktow: 165
    korytarzy (te same numery i dlugosci), 43 scalenia duplikatow pasa (cel i liczba punktow), 6 956 291 wierszy (korytarz i `s_ref_gps`),
    25 219 punktow `wide`."""
    from tsdfwd_tools.compare import geo as G
    prod, v4 = dbs["prod"], dbs["v4"]
    excluded = {r[0] for r in v4.execute("SELECT DISTINCT file_id FROM tsd_gps_data_qc WHERE verdict_pair = 'PRZESUNIETY'")}
    rows = pd.read_sql("SELECT file_id, tsd_id, chainage_m, latitude, longitude FROM tsd_measurements ORDER BY file_id, tsd_id", v4)
    runs, ids = {}, {}
    for f, g in rows.groupby("file_id", sort=True):
        if f in excluded:
            continue
        runs[int(f)] = G.prepare_run(g.chainage_m.to_numpy(float), g.latitude.to_numpy(float), g.longitude.to_numpy(float))
        ids[int(f)] = g.tsd_id.to_numpy()
    del rows
    corrs, assigned, info = G.build_axis(runs, merge=True)
    ref_c = pd.read_sql("SELECT corridor_id, length_m FROM ref_corridors", prod).set_index("corridor_id")
    assert sorted(c.cid for c in corrs) == sorted(ref_c.index) and len(corrs) == 165
    assert max(abs(c.length - ref_c.length_m[c.cid]) for c in corrs) < 1e-3
    rm = pd.read_sql("SELECT dissolved_id, target_id, n_points_wide, n_points_far FROM ref_corridor_merges", prod).set_index("dissolved_id")
    mine = pd.DataFrame(info["merges"]).set_index("dissolved_id")
    assert len(mine) == len(rm) == 43 and set(mine.index) == set(rm.index)
    assert (mine.target_id == rm.target_id.reindex(mine.index)).all()
    assert (mine.n_points_wide == rm.n_points_wide.reindex(mine.index)).all() and (mine.n_points_far == rm.n_points_far.reindex(mine.index)).all()
    sref = pd.read_sql("SELECT tsd_id, corridor_id, s_ref_gps, lane_fit FROM tsd_sref", prod).set_index("tsd_id")
    n = same = wide = wide_ref = wide_both = 0
    ds_max = 0.0
    for f, (cid, s, lat, _) in assigned.items():
        r = sref.reindex(ids[f])
        rc = r.corridor_id.fillna(-1).astype(int).to_numpy()
        n += len(cid)
        ok = cid == rc
        same += int(ok.sum())
        both = ok & (cid >= 0)
        ds_max = max(ds_max, float(np.nanmax(np.abs(s[both] - r.s_ref_gps.to_numpy(float)[both]))) if both.any() else 0.0)
        w, rw = info["wide"][f], (r.lane_fit == "wide").to_numpy()
        wide, wide_ref, wide_both = wide + int(w.sum()), wide_ref + int(rw.sum()), wide_both + int((w & rw).sum())
    assert n == same == 6956291 and ds_max < 0.001
    assert wide == wide_ref == wide_both == 25219
