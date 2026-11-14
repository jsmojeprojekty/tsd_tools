"""Testy regresji N2 (layer_temp) wzgledem wynikow referencyjnych projektu temp_model (DOKTORAT, tylko odczyt).

Referencja glowna (T-N2-01): zbior H v2 (549 obserwacji, 226 sesji), fizyka + kalibracja jednorazowa do pirometru (IR 'masa'), 12 cm,
meteo z cache referencyjnego Open-Meteo (UTC -> lokalny). To test POWTARZALNOSCI na zbiorze eksploracyjnym H, a nie deklaracja
dokladnosci produktu (na niezaleznym zbiorze C: RMSE 2,73 C)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tsdfwd_tools.layer_temp.flags import LayerFlag
from tsdfwd_tools.layer_temp.meteo import MeteoStore
from tsdfwd_tools.layer_temp.params import load_params
from tsdfwd_tools.layer_temp.predict import run_survey

pytestmark = pytest.mark.reference

TEMP_MODEL = Path("temp_model") / "output"
CACHE_REL = TEMP_MODEL / "z14lite" / "openmeteo_cache_utc"
CAND_REL = TEMP_MODEL / "z14lite" / "z14c" / "Z14c_candidates.parquet"
Z15_REL = TEMP_MODEL / "z15" / "Z15_temperatury_par.csv"
SRC_REL = Path("tabele") / "z14lite_fwd_walidacja_v3.csv"


@pytest.fixture(scope="module")
def ref_paths(local_paths, sql_root):
    root = Path(local_paths.get("doktorat_root", ""))
    p = {"cache": root / CACHE_REL, "cand": root / CAND_REL, "z15": root / Z15_REL, "src": sql_root / SRC_REL}
    for k, v in p.items():
        if not v.exists():
            pytest.skip(f"brak {k}: {v}")
    return p


@pytest.fixture(scope="module")
def store(ref_paths):
    return MeteoStore(ref_paths["cache"], offline=True)


@pytest.fixture(scope="module")
def h_set(ref_paths):
    src = pd.read_csv(ref_paths["src"], encoding="utf-8-sig")
    src["ts"] = pd.to_datetime(src.measured_at_local)
    h = src[(src.dataset == "odcinki") & src.t_surface.notna() & src.t_air.notna() & (src.t_layer_depth_cm == 12)
            & (src.asphalt_temp_trusted == 1) & src.asphalt_status.isin(["entry_first", "entry_change"])
            & src.ts.dt.month.between(4, 10) & (src.station_id != 16322)]
    return h.reset_index(drop=True)


@pytest.fixture(scope="module")
def h_result(h_set, store):
    return run_survey(h_set[["measured_at_local", "latitude", "longitude", "t_surface", "t_air"]], store, load_params(), with_bells3=True)


@pytest.fixture(scope="module")
def candidates(ref_paths, h_set):
    ref = pd.read_parquet(ref_paths["cand"])
    return ref[ref.klasa == "otwarta (TN)"].set_index("unit_id").loc[h_set.obs_group_id.values]


def _metrics(e):
    e = np.asarray(e, float)
    e = e[np.isfinite(e)]
    return len(e), float(np.sqrt(np.mean(e ** 2))), float(np.mean(np.abs(e))), float(np.mean(e))


def test_t_n2_01_main_h_v2(h_set, h_result):
    """T-N2-01: RMSE 1,7486 / MAE 1,4039 / bias +0,2653 (zrodlowa replika: 1,7488 / 1,4042 / +0,2649), 549 obs., 226 sesji."""
    assert len(h_set) == 549 and h_set.session_id.nunique() == 226
    n, rmse, mae, bias = _metrics(h_result.t_layer.to_numpy() - h_set.t_layer.to_numpy())
    assert n == 549
    assert rmse == pytest.approx(1.7486, abs=0.001)
    assert mae == pytest.approx(1.4039, abs=0.001)
    assert bias == pytest.approx(0.2653, abs=0.001)


def test_t_n2_02_counts_and_calibration_flags(h_result):
    vc = h_result.calib_flag.value_counts().to_dict()
    assert vc == {"ok": 294, "bound_hi": 244, "gate": 11}                              # bound_lo: 0
    assert int((h_result.qc_flags.to_numpy() & LayerFlag.CALIB_BOUND_HI).astype(bool).sum()) == 244


def test_t_n2_03_per_observation_vs_candidates(h_result, candidates):
    """544/549 zgodne do 1e-6 C; 5 obs. po 23:00 (ogon cache, stala ekstrapolacja) rozni sie <= 0,2 C i maja flage TAIL_EXTRAPOLATED."""
    d = np.abs(h_result.t_layer.to_numpy() - candidates.phys_single_masa.to_numpy())
    tail = (h_result.qc_flags.to_numpy() & LayerFlag.TAIL_EXTRAPOLATED).astype(bool)
    assert (d[~tail] < 1e-6).all() and int((d < 1e-6).sum()) >= 544
    assert tail.sum() == 5 and (d[tail] <= 0.2).all()
    assert (h_result.calib_flag.to_numpy()[~tail] == candidates.flag_single_masa.to_numpy()[~tail]).all()
    assert np.nanmax(np.abs(h_result.a_sw.to_numpy()[~tail] - candidates.a_single_masa.to_numpy()[~tail])) < 1e-6
    assert np.nanmax(np.abs(h_result.sw_ma6.to_numpy() - candidates.sw_ma6.to_numpy())) < 1e-6       # definicja SW_ma6 jak w zrodle


def test_t_n2_04_comparators(h_set, h_result):
    y = h_set.t_layer.to_numpy()
    n, rmse, mae, bias = _metrics(h_result.t_layer_uncal.to_numpy() - y)                # fizyka bez kalibracji
    assert n == 549
    assert rmse == pytest.approx(2.0872, abs=0.001) and mae == pytest.approx(1.6974, abs=0.001) and bias == pytest.approx(0.9455, abs=0.001)
    n, rmse, mae, bias = _metrics(h_result.bells3_c.to_numpy() - y)                    # BELLS3 klasyczny
    assert rmse == pytest.approx(2.4065, abs=0.001) and mae == pytest.approx(1.8160, abs=0.001) and bias == pytest.approx(-0.3432, abs=0.001)


def test_bells3_identical_to_source(h_result, candidates):
    assert np.nanmax(np.abs(h_result.bells3_c.to_numpy() - candidates.bells3.to_numpy())) < 1e-9


def test_t_n2_05_rmse_by_time_of_day(h_set, h_result):
    hour = pd.to_datetime(h_set.measured_at_local).dt.hour
    e = pd.Series(h_result.t_layer.to_numpy() - h_set.t_layer.to_numpy())
    got = {}
    for name, lo, hi in (("0-6", 0, 5), ("6-12", 6, 11), ("12-18", 12, 17), ("18-24", 18, 23)):
        sel = (hour >= lo) & (hour <= hi)
        got[name] = (int(sel.sum()), float(np.sqrt((e[sel] ** 2).mean())))
    assert [v[0] for v in got.values()] == [49, 226, 237, 37]
    for (name, rmse), expect in zip(((k, v[1]) for k, v in got.items()), (2.167, 1.378, 1.889, 2.167)):
        assert rmse == pytest.approx(expect, abs=0.005), name


def test_flags_in_reference_run_are_plausible(h_result):
    """W zbiorze H (IV-X, bez sniegu, sprawne meteo): brak flag sezonu/sniegu/luk/pozycji; NOC tylko dla chwil po zachodzie."""
    q = h_result.qc_flags.to_numpy()
    for f in (LayerFlag.OUT_OF_SEASON, LayerFlag.SNOW, LayerFlag.METEO_GAP, LayerFlag.CALIB_NOSIM, LayerFlag.POSITION_OUT_OF_POLAND):
        assert not (q & f).any(), f.name
    assert 0 < int((q & LayerFlag.NIGHT).astype(bool).sum()) < 100
    assert (h_result.u95 >= 2.2).all()


def test_t_n2_10_z15_pairs(ref_paths, store):
    """T-N2-10 (2. poziom): 200 par Z15 po obu stronach (FWD i TSD): T12 po kalibracji, bez kalibracji i BELLS3 zgodne z plikiem Z15."""
    z = pd.read_csv(ref_paths["z15"], encoding="utf-8-sig")
    z = z.sample(200, random_state=7)
    params = load_params()
    for side in ("fwd", "tsd"):
        df = pd.DataFrame({"measured_at_local": z[f"{side}_time"], "latitude": z[f"{side}_lat"], "longitude": z[f"{side}_lon"],
                           "t_surface": z[f"{side}_ir"]}).reset_index(drop=True)
        res = run_survey(df, store, params, with_bells3=True)
        ref_cal, ref_unc, ref_bel = (z[f"{side}_t12_{k}"].to_numpy() for k in ("cal", "uncal", "bells3"))
        tail = (res.qc_flags.to_numpy() & LayerFlag.TAIL_EXTRAPOLATED).astype(bool)
        ok = np.isfinite(ref_cal)
        assert ok.sum() >= 150, side
        for mine, ref in ((res.t_layer, ref_cal), (res.t_layer_uncal, ref_unc), (res.bells3_c, ref_bel)):
            d = np.abs(mine.to_numpy() - ref)
            assert (d[ok & ~tail] < 1e-6).all(), (side, float(np.nanmax(d[ok & ~tail])))
            assert (d[ok & tail] <= 0.25).all()
        assert (res.a_sw.to_numpy()[ok & ~tail] == pytest.approx(z[f"{side}_a_cal"].to_numpy()[ok & ~tail], abs=1e-6))
