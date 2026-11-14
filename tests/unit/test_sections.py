"""Odcinki wspolne TSD-FWD (Tab. 3.2): testy syntetyczne detect_sections i raportu przegladu."""

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.compare import sections as S
from tsdfwd_tools.compare.section_report import write_review

M = 111_320.0


def _run(n=3000):
    chain = np.arange(n, dtype=float)
    return pd.DataFrame(dict(lat=50.0 + chain / M, lon=19.0, chainage=chain, heading=0.0, d0=100.0 + 0.0 * chain))


def _stations(pos, offset_m=0.0, heading=0.0, station_m=None, session=1):
    lon = 19.0 + offset_m / (M * np.cos(np.radians(50.0)))
    sm = np.asarray(pos, float) / 1000.0 if station_m is None else np.asarray(station_m, float)
    return pd.DataFrame(dict(station_id=np.arange(len(pos)) + 1000 * session, lat=50.0 + np.asarray(pos, float) / M, lon=lon,
                             heading=heading, station_m=sm, fwd_d0=200.0))


def _detect(stations, run=None, run_date="2025-07-20", sess_date="2025-07-01", params=None):
    run = _run() if run is None else run
    return S.detect_sections({"r1": run}, {"r1": run_date}, {1: stations}, {1: (sess_date, sess_date)}, params)


def test_basic_section_same_direction_same_lane():
    tab, matches, cnt = _detect(_stations(np.arange(200.0, 2800.0, 100.0)))
    assert len(tab) == 1 and cnt["n_sections"] == 1
    r = tab.iloc[0]
    assert r["direction"] == "same" and r["lane_class"] == "same" and r["spearman_corr"] == pytest.approx(1.0)
    assert r["fwd_matched"] == 26 and r["coverage_pct"] == pytest.approx(100.0)
    assert r["chainage_m_max"] - r["chainage_m_min"] == pytest.approx(2500.0, abs=1)
    assert abs(r["median_xtrack_m"]) < 0.01 and len(matches[(1, "r1")]) == 26


def test_opposite_direction_and_decreasing_station_m_are_accepted():
    pos = np.arange(200.0, 2800.0, 100.0)
    tab, _, _ = _detect(_stations(pos, heading=180.0, station_m=pos[::-1] / 1000.0))
    r = tab.iloc[0]
    assert r["direction"] == "opposite" and r["spearman_corr"] == pytest.approx(-1.0)      # znak Spearmana bez znaczenia


@pytest.mark.parametrize("offset, lane", [(0.5, "same"), (1.2, "adjacent"), (5.0, "far")])
def test_lane_class_from_median_cross_track(offset, lane):
    tab, _, _ = _detect(_stations(np.arange(200.0, 2800.0, 100.0), offset_m=offset))
    r = tab.iloc[0]
    assert r["lane_class"] == lane and abs(abs(r["median_xtrack_m"]) - offset) < 0.05
    assert r["median_xtrack_m"] > 0                                    # stacja na wschod od toru na polnoc: na PRAWO od kierunku


def test_rejections_are_counted_by_reason():
    pos = np.arange(200.0, 2800.0, 100.0)
    tab, _, cnt = _detect(_stations(pos[:4]))
    assert tab.empty and cnt["few_stations"] == 1
    tab, _, cnt = _detect(_stations(np.arange(200.0, 600.0, 50.0)))        # zakres 350 m < 500 m
    assert tab.empty and cnt["short_span"] == 1
    tab, _, cnt = _detect(_stations(pos), run_date="2024-07-20")
    assert tab.empty and cnt["diff_year"] == 1
    tab, _, cnt = _detect(_stations(pos), run_date="2025-07-20", sess_date="2024-12-31")
    assert tab.empty and cnt["diff_year"] == 1
    rng = np.random.default_rng(1)
    tab, _, cnt = _detect(_stations(pos, station_m=rng.permutation(len(pos)) / 10.0))
    assert tab.empty and cnt["noise"] == 1                                 # niemonotoniczne station_m
    tab, _, cnt = _detect(_stations(pos, heading=90.0))                    # kurs prostopadly: niejednoznaczny
    assert tab.empty and cnt["ambiguous_direction"] == 1
    tab, _, cnt = _detect(_stations(pos), params=S.SectionParams(same_year_only=False, max_days=400.0), run_date="2026-07-20")
    assert len(tab) == 1                                                   # bez zasady roku: 384 dni <= 400


def test_coverage_uses_stations_inside_tsd_bbox():
    """TSD pokrywa tylko pierwsze 1500 m trasy FWD: stacje poza obwiednia nie obnizaja pokrycia."""
    pos = np.arange(200.0, 5000.0, 100.0)
    tab, _, _ = _detect(_stations(pos), run=_run(1500))
    r = tab.iloc[0]
    assert r["coverage_pct"] == pytest.approx(100.0) and r["fwd_total"] == len(pos) and r["fwd_in_overlap"] < len(pos)
    assert r["coverage_full_pct"] < 50.0


def test_ensure_headings_fills_missing_heading_from_sequence():
    d = _run(50).drop(columns="heading")
    out = S.ensure_headings(d, ["chainage"])
    assert np.nanmax(np.abs(((out["heading"].to_numpy() + 180) % 360) - 180)) < 0.5     # kurs polnocny (0 st.)


def test_review_report_has_three_panels(tmp_path):
    tab, matches, _ = _detect(_stations(np.arange(200.0, 2800.0, 100.0)))
    out = write_review(tmp_path / "r.html", tab, matches, {"r1": _run()}, {1: _stations(np.arange(200.0, 2800.0, 100.0))})
    txt = out.read_text(encoding="utf-8")
    assert txt.count("<svg") == 3 and "linia do linii" in txt and "odcinek 1" in txt
