"""Testy syntetyczne geometrii N4 (tryb geometry): EPSG:2180, lag polozenia, rzut na korytarz, ciagi, budowa korytarzy.

Odpowiadaja testom T1-T7 ze zrodla (C:\\projects\\sql_tsd_fwd\\bak\\test_e1.py, stan d89080a / 2026-10-18); bez danych zewnetrznych."""

import numpy as np
import pytest
from scipy.integrate import quad

from tsdfwd_tools.compare import geo as G

E2 = G.F_GRS80 * (2 - G.F_GRS80)


def meridian_arc(lat_deg):
    return quad(lambda p: G.A_GRS80 * (1 - E2) / (1 - E2 * np.sin(p) ** 2) ** 1.5, 0.0, np.radians(lat_deg),
                epsabs=1e-9, epsrel=1e-12)[0]


@pytest.mark.parametrize("lat", [49.0, 52.0, 54.8])
def test_to_2180_central_meridian(lat):
    e0, n0 = G.to_2180(lat, 19.0)
    assert abs(e0 - 500000.0) < 1e-6
    assert abs(n0 - (G.FN_2180 + G.K0_2180 * meridian_arc(lat))) < 1e-4


def test_to_2180_symmetry_scale_and_convergence():
    ea, na = G.to_2180(51.3, 23.7)
    eb, nb = G.to_2180(51.3, 14.3)
    assert abs((ea - 500000) + (eb - 500000)) < 1e-6 and abs(na - nb) < 1e-6
    for lon in (15.0, 19.0, 22.0, 24.0):
        lat, h = 52.0, 1e-4
        p1, p2 = G.to_2180(lat - h, lon), G.to_2180(lat + h, lon)
        k_n = np.hypot(p2[0] - p1[0], p2[1] - p1[1]) / (meridian_arc(lat + h) - meridian_arc(lat - h))
        q1, q2 = G.to_2180(lat, lon - h), G.to_2180(lat, lon + h)
        nu = G.A_GRS80 / np.sqrt(1 - E2 * np.sin(np.radians(lat)) ** 2)
        k_e = np.hypot(q2[0] - q1[0], q2[1] - q1[1]) / (nu * np.cos(np.radians(lat)) * np.radians(2 * h))
        eta2 = E2 / (1 - E2) * np.cos(np.radians(lat)) ** 2
        lc = np.radians(lon - 19.0) * np.cos(np.radians(lat))
        k_th = G.K0_2180 * (1 + lc ** 2 / 2 * (1 + eta2))
        assert abs(k_n - k_th) < 3e-6 and abs(k_e - k_n) < 1e-7           # skala i konforemnosc
    for lon in (16.0, 22.0):
        lat = 52.0
        p1, p2 = G.to_2180(lat, lon), G.to_2180(lat + 0.001, lon)
        az = np.degrees(np.arctan2(p2[0] - p1[0], p2[1] - p1[1]))
        assert abs(az + float(G.convergence_deg(lat, lon))) < 0.01


def test_lag_convention_row_gets_gps_from_ahead():
    s = np.arange(0.0, 1000.0)
    x = np.full(1000, 500000.0)
    y = 400000.0 + s
    xc, yc = G.corrected_xy(s, x, y, G.TSD_OFFSET_M)
    assert abs(yc[100] - y[100] - 4.8) < 1e-9 and abs(xc[100] - x[100]) < 1e-9
    assert np.isnan(yc[-1])                                                   # koniec pliku bez GPS


@pytest.mark.parametrize("hd", [90.0, 0.0, 225.0])
def test_shift_along_backwards_by_d(hd):
    lat, lon = 52.0, 19.0
    la, lo = G.shift_along(lat, lon, hd + 180.0, 5.0)
    x0, y0 = G.to_2180(lat, lon)
    x1, y1 = G.to_2180(la, lo)
    exp = -5.0 * G.K0_2180 * np.array([np.sin(np.radians(hd)), np.cos(np.radians(hd))])
    assert np.hypot(x1 - x0 - exp[0], y1 - y0 - exp[1]) < 2e-3


def test_project_on_sign_station_and_heading():
    x = np.full(1001, 500000.0)
    y = 400000.0 + np.arange(1001.0)
    c = G.Corridor(0, x, y, [])
    s, lat, dh, ok = G.project_on(c, np.array([499998.5, 500001.0, 500000.5]), np.array([400100.3, 400200.0, 400300.0]),
                                  np.array([0.0, 0.0, 170.0]), 1.75)
    assert abs(s[0] - 100.3) < 1e-9 and abs(lat[0] - 1.5) < 1e-9 and ok[0]          # + = w lewo od kierunku
    assert abs(lat[1] + 1.0) < 1e-9 and ok[1] and not ok[2] and abs(abs(dh[2]) - 170) < 1e-6


def _track(headings, start=(500000.0, 400000.0)):
    hd = np.radians(np.asarray(headings, float))
    x = start[0] + np.concatenate([[0.0], np.cumsum(np.sin(hd[:-1]))])
    y = start[1] + np.concatenate([[0.0], np.cumsum(np.cos(hd[:-1]))])
    return x, y


def test_split_segments_and_pass_groups():
    h = np.concatenate([np.zeros(1000), np.linspace(0, 180, 26)[1:], np.full(1000, 180.0)])
    x, y = _track(h)
    x[500:] += 20.0                                                           # skok 20 m po 500 wierszach
    segs = G.split_segments(x, y)
    assert len(segs) == 3 and segs[0] == (0, 499) and segs[1][0] == 500 and segs[1][1] < 1010 and segs[2][0] > 1015
    cid = np.array([0] * 100 + [1] * 20 + [0] * 100 + [-1] * 60 + [0] * 50)
    s = np.arange(len(cid), dtype=float)
    got = [(c, int(i[0]), int(i[-1])) for c, i in G.pass_groups(cid, s)]
    assert got == [(0, 0, 219), (1, 100, 119), (0, 280, 329)]                 # wtracenie nie dzieli, przerwa 60 dzieli
    s2 = np.concatenate([np.arange(100.0), 50 + np.arange(100.0)])
    g2 = G.pass_groups(np.zeros(200, dtype=np.int32), s2)
    assert [(int(i[0]), int(i[-1])) for _, i in g2] == [(0, 99), (100, 199)]   # cofniecie s dzieli


def _road(t, off, R=2000.0):
    a = t / R
    cx, cy = 500000.0 + R * (1 - np.cos(a)), 400000.0 + R * np.sin(a)
    return cx - off * np.cos(a), cy + off * np.sin(a)


def _mk_run(t, off, rng, noise=0.15):
    x, y = _road(t, off)
    x = x + rng.normal(0, noise, len(t))
    y = y + rng.normal(0, noise, len(t))
    hd = np.full(len(t), np.nan)
    segs = G.split_segments(x, y)
    for a, b in segs:
        hd[a:b + 1] = G.fill_edges(G.heading_of(x[a:b + 1], y[a:b + 1]))
    return dict(xc=x, yc=y, hd=hd, segs=segs)


def test_build_corridors_lanes_opposite_extension_and_short_track():
    rng = np.random.default_rng(1)
    runs = {1: _mk_run(np.arange(0.0, 3000.0), -1.75, rng),          # pas prawy, 0-3 km
            2: _mk_run(np.arange(1000.0, 4000.0), -1.75, rng),       # pas prawy, 1-4 km: przedluzenie
            3: _mk_run(np.arange(500.0, 3500.0), 1.75, rng),         # pas lewy
            4: _mk_run(np.arange(3999.0, -1.0, -1.0), 15.0, rng),    # jezdnia przeciwna
            5: _mk_run(np.arange(1200.0, 1350.0), -40.0, rng)}       # 150 m obok: za krotko
    corrs, info = G.build_corridors(runs)
    assert len(corrs) == 3 and info["n_ext"] == 1
    res = {f: G.assign_run(corrs, d, True) for f, d in runs.items()}
    dom = {f: np.bincount(r[0][r[0] >= 0]).argmax() if (r[0] >= 0).any() else -1 for f, r in res.items()}
    share = {f: float(np.mean(res[f][0] == dom[f])) for f in res}
    assert dom[1] == dom[2] and len({dom[1], dom[3], dom[4]}) == 3 and min(share[f] for f in (1, 2, 3, 4)) > 0.99
    assert (res[5][0] < 0).all() and (res[5][3][res[5][0] < 0] == 3).all()    # no_corridor
    assert np.median(np.abs(res[3][2])) < 0.5


def test_refine_geometry_recovers_track_median():
    rng = np.random.default_rng(2)
    t = np.arange(0.0, 2000.0)
    ax, ay = _road(t, 0.8)
    c = G.Corridor(0, ax, ay, [])
    tt = np.concatenate([t + rng.uniform(0, 1, len(t)) for _ in range(10)])
    px, py = _road(tt, rng.normal(0, 0.3, len(tt)))
    s, lat, dh, ok = G.project_on(c, px, py, None, 1.75, heading=False)
    x2, y2, fmax, fmed = G.refine_geometry(c, s, lat)
    c2 = G.Corridor(1, x2, y2, [])
    tx, ty = _road(np.arange(100.0, 1900.0), 0.0)
    _, lat2, _, _ = G.project_on(c2, tx, ty, None, 5.0, heading=False)
    assert float(np.sqrt(np.mean(lat2 ** 2))) < 0.03 and np.abs(lat2).max() < 0.1 and abs(fmed - 0.8) < 0.05


def test_group_median_matches_numpy():
    rng = np.random.default_rng(5)
    gid = rng.integers(0, 7, 400)
    v = rng.normal(size=400)
    v[rng.integers(0, 400, 30)] = np.nan
    med, cnt = G.group_median(gid, v, 7)
    for g in range(7):
        x = v[(gid == g) & np.isfinite(v)]
        assert cnt[g] == len(x) and med[g] == pytest.approx(np.median(x), abs=1e-12)


def test_prepare_run_and_build_axis_end_to_end():
    """Przejazd po luku (lat/lon z odwrotnego rzutowania nie jest potrzebny: wspolrzedne geodezyjne wzdluz poludnika)."""
    n = 1500
    lat = 50.0 + np.arange(n) * (1.0 / 111200.0)                     # ~1 m na wiersz wzdluz poludnika 19 E
    lon = np.full(n, 19.0)
    chain = np.arange(n, dtype=float)
    run = G.prepare_run(chain, lat, lon)
    assert len(run["segs"]) == 1 and run["segs"][0][0] == 0
    corrs, assigned, info = G.build_axis({"a": run})
    assert info["n_corridors"] == 1
    cid, s, lat_m, rc = assigned["a"]
    ok = cid >= 0
    assert ok.sum() > 1400 and np.nanmax(np.abs(lat_m[ok])) < 0.05
    # lag -4,8 m: polozenie wiersza ma byc GPS z przodu, wiec s_ref_gps rosnie wzdluz toru
    assert np.all(np.diff(s[ok]) > 0)
