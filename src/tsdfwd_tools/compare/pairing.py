"""N4 tryb `geometry`: pary TSD-FWD wylacznie z geometrii (okna po s_ref), warstwy jakosci polozenia, pary zerowe, wartosci okien.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b1_pairs.py (window_stats, nearest_row, layer_of, build_candidates, _dt_days,
build_null_pairs; stan d89080a / 2026-10-18) oraz bak\\e2b2_values.py (tsd_values_for_window: mediana d0 w oknie, okno
uznane gdy >= 3 wiersze z waznym d0).
Zasada nadrzedna zrodla: parowanie wylacznie GEOMETRYCZNE — funkcje budujace pary (`build_candidates`, `build_null_pairs`) nie
przyjmuja wartosci ugiec; wartosci okien (`window_value`) liczy osobny krok na wskazanych oknach, nigdy nie wybiera rekordu.
Zmiana wzgledem zrodla (S-N4-4, decyzja E0): okno wartosci = wiersze z |s_ref - s_fwd| <= promien (jedna definicja po s_ref),
a nie zakres tsd_id min..max (zrodlowy e2b2_values mial inna definicje okna niz skrypt 'lustro')."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

LANE_CLASSES = ("same", "adjacent")
WINDOWS = (("win1", 1.0), ("win2_5", 2.5), ("win5", 5.0))
NEAREST_PREFILTER_M = 100.0     # poza tym okna +-5 m i tak sa zawsze puste
YEAR_DIFF_MAX = 1               # same_year = 1 (glowny) albo +-1 rok (flagowane)
NULL_SHIFT_M = 200.0
NULL_PERM_MIN_M = 300.0
NULL_SEED = 20261017
LAYER_A = (1.0, 1.0)            # (|dlat| max, sigma_long max)
LAYER_B = (1.75, 2.5)
LAYER_C_SIGMA = 5.0
TSD_SIGMA_M_DEFAULT = 1.5       # niepewnosc polozenia TSD (lag -4,8 m +-1,5 m)
MIN_WINDOW_N = 3                # okno uznane, gdy >= tyle wierszy z waznym d0


def window_stats(s_sorted, row_id, lat, gof, center, radius):
    """Statystyki okna |s - center| <= radius (przedzial domkniety; wiersze posortowane po s)."""
    lo = np.searchsorted(s_sorted, center - radius, side="left")
    hi = np.searchsorted(s_sorted, center + radius, side="right")
    n = hi - lo
    if n <= 0:
        return dict(n=0, tsd_id_min=None, tsd_id_max=None, gof05_share=None, lat_median=None)
    g = gof[lo:hi]
    gok = np.isfinite(g)
    share = float(np.mean(g[gok] >= 0.5)) if gok.any() else None
    latw = lat[lo:hi]
    lat_med = float(np.nanmedian(latw)) if np.isfinite(latw).any() else None
    return dict(n=int(n), tsd_id_min=int(row_id[lo:hi].min()), tsd_id_max=int(row_id[lo:hi].max()),
                gof05_share=share, lat_median=lat_med)


def nearest_row(s_sorted, s0):
    i = np.searchsorted(s_sorted, s0)
    cands = [j for j in (i - 1, i) if 0 <= j < len(s_sorted)]
    if not cands:
        return None
    return min(cands, key=lambda k: abs(s_sorted[k] - s0))


def layer_of(dlat, sigma_long):
    """Warstwa jakosci polozenia: A |dlat| <= 1,0 i sigma_long <= 1,0; B |dlat| <= 1,75 i sigma_long <= 2,5; C sigma_long <= 5,0; X reszta."""
    if dlat is None or sigma_long is None or not (np.isfinite(dlat) and np.isfinite(sigma_long)):
        return "X"
    if abs(dlat) <= LAYER_A[0] and sigma_long <= LAYER_A[1]:
        return "A"
    if abs(dlat) <= LAYER_B[0] and sigma_long <= LAYER_B[1]:
        return "B"
    if sigma_long <= LAYER_C_SIGMA:
        return "C"
    return "X"


def dt_days(fwd_date, tsd_date):
    """Odstep w dniach ZE ZNAKIEM = data TSD - data FWD (ujemny: TSD przed FWD)."""
    if not fwd_date or not tsd_date:
        return None
    try:
        a = date(*(int(x) for x in str(fwd_date)[:10].split("-")))
        b = date(*(int(x) for x in str(tsd_date)[:10].split("-")))
        return float((b - a).days)
    except (ValueError, TypeError):
        return None


def _none(v):
    if v is None:
        return None
    try:
        return None if (isinstance(v, float) and not np.isfinite(v)) or pd.isna(v) else v
    except (TypeError, ValueError):
        return v


def build_candidates(stations: pd.DataFrame, passes: pd.DataFrame, pass_rows: dict, in_stage1=(),
                     tsd_sigma_m: float = TSD_SIGMA_M_DEFAULT) -> pd.DataFrame:
    """Kandydaci na pary: stacja FWD (pas same/adjacent, s_fwd niepusty) x przejazd TSD na tym samym korytarzu, ten sam rok FWD i
    TSD albo +-1 rok (flaga same_year). Najblizszy wiersz TSD do s_fwd (|ds| <= 100 m), okna +-1 / +-2,5 / +-5 m po s_ref.
    stations: wynik `fwd_plate_positions`; passes: pass_id, corridor_id, date [, file_id, v_med, calib_interval,
    calib_interval_uncertain, data_tier, recorder_group]; pass_rows: {pass_id: dict(s, tsd_id, lat, gof)} posortowane po s.
    ZADNEJ wartosci ugiec nie czyta."""
    st = stations[stations["lane_match"].isin(LANE_CLASSES) & stations["s_fwd"].notna()]
    passes_by_corr = {c: g.sort_values("pass_id", kind="stable").to_dict("records") for c, g in passes.groupby("corridor_id")}
    in_stage1 = set(in_stage1)
    rows = []
    pair_id = 0
    st_by_corr = {c: g.to_dict("records") for c, g in st.groupby("corridor_id", sort=True)}
    for corridor_id, sts in sorted(st_by_corr.items()):
        plist = passes_by_corr.get(corridor_id)
        if not plist:
            continue
        for p in plist:
            pr = pass_rows.get(p["pass_id"])
            if pr is None or len(pr["s"]) == 0:
                continue
            tsd_year = str(_none(p.get("date")) or "")[:4]
            if not tsd_year.isdigit():
                continue
            for s_ in sts:
                fwd_year = str(_none(s_.get("date")) or "")[:4]
                if not fwd_year.isdigit():
                    continue
                dy = abs(int(fwd_year) - int(tsd_year))
                if dy > YEAR_DIFF_MAX:
                    continue
                j = nearest_row(pr["s"], s_["s_fwd"])
                if j is None:
                    continue
                ds = float(s_["s_fwd"] - pr["s"][j])
                if abs(ds) > NEAREST_PREFILTER_M:
                    continue
                w = {key: window_stats(pr["s"], pr["tsd_id"], pr["lat"], pr["gof"], s_["s_fwd"], radius)
                     for key, radius in WINDOWS}
                lat_fwd = _none(s_.get("lat_ant"))
                lat_tsd5 = w["win5"]["lat_median"]
                dlat = (lat_fwd - lat_tsd5) if (lat_fwd is not None and lat_tsd5 is not None) else None
                sigma_long = _none(s_.get("sigma_long"))
                sigma_b = _none(s_.get("sigma_long_hwd_b"))
                pair_id += 1
                rec = dict(pair_id=pair_id, station_id=s_["station_id"], session_id=s_["session_id"], corridor_id=corridor_id,
                           pass_id=p["pass_id"], file_id=_none(p.get("file_id")), s_fwd=s_["s_fwd"], lat_fwd=lat_fwd,
                           lane_match=s_["lane_match"], nearest_tsd_id=int(pr["tsd_id"][j]), ds=ds)
                for key, _ in WINDOWS:
                    for k, v in w[key].items():
                        rec[f"{key}_{k}"] = v
                rec.update(win5_lat_tsd_median=lat_tsd5, dlat=dlat, sigma_long_fwd=sigma_long, sigma_long_hwd_b=sigma_b,
                           sigma_tsd_m=tsd_sigma_m, dt_days=dt_days(s_.get("date"), p.get("date")), same_year=int(dy == 0),
                           calib_interval=_none(p.get("calib_interval")),
                           calib_interval_uncertain=_none(p.get("calib_interval_uncertain")),
                           data_tier=_none(p.get("data_tier")), recorder_group=_none(p.get("recorder_group")),
                           v_med=_none(p.get("v_med")), device=s_.get("device"), era=s_.get("era"),
                           in_concrete_zone=_none(s_.get("in_concrete_zone")),
                           in_stage1=int((s_["station_id"], _none(p.get("file_id"))) in in_stage1),
                           tsd_year=int(tsd_year), fwd_year=int(fwd_year), layer=layer_of(dlat, sigma_long),
                           layer_hwd_b=(layer_of(dlat, sigma_b) if s_.get("era") == "hwd" else None))
                rows.append(rec)
    return pd.DataFrame(rows)


def build_null_pairs(candidates: pd.DataFrame, pass_rows: dict, seed: int = NULL_SEED) -> pd.DataFrame:
    """Pary zerowe (odwzorowanie, bez wartosci): (i) srodek okna +-5 m przesuniety o -200 / +200 m wzdluz TEGO SAMEGO przejazdu;
    (ii) permutacja: losowy srodek z siatki co 50 m z [min(s), max(s)] przejazdu, >= 300 m od stacji (rng wspolny dla wszystkich par
    w kolejnosci pair_id — wynik zalezy od kolejnosci pair_id). Strona FWD ta sama; zmienia sie tylko wybor TSD."""
    rng = np.random.default_rng(seed)
    out = []
    for c in candidates.sort_values("pair_id").to_dict("records"):
        pr = pass_rows.get(c["pass_id"])
        if pr is None or len(pr["s"]) == 0:
            continue
        s_sorted = pr["s"]
        for sign in (-1.0, 1.0):
            center = c["s_fwd"] + sign * NULL_SHIFT_M
            w5 = window_stats(s_sorted, pr["tsd_id"], pr["lat"], pr["gof"], center, 5.0)
            out.append(dict(pair_id=c["pair_id"], null_type=f'shift_{"plus" if sign > 0 else "minus"}200',
                            corridor_id=c["corridor_id"], pass_id=c["pass_id"], center_s=center,
                            win5_n=w5["n"], win5_tsd_id_min=w5["tsd_id_min"], win5_tsd_id_max=w5["tsd_id_max"],
                            win5_gof05_share=w5["gof05_share"]))
        lo, hi = float(s_sorted.min()), float(s_sorted.max())
        grid = [s for s in np.arange(lo, hi, 50.0) if abs(s - c["s_fwd"]) >= NULL_PERM_MIN_M]
        if grid:
            center = float(rng.choice(grid))
            w5 = window_stats(s_sorted, pr["tsd_id"], pr["lat"], pr["gof"], center, 5.0)
            out.append(dict(pair_id=c["pair_id"], null_type="permutation", corridor_id=c["corridor_id"],
                            pass_id=c["pass_id"], center_s=center, win5_n=w5["n"], win5_tsd_id_min=w5["tsd_id_min"],
                            win5_tsd_id_max=w5["tsd_id_max"], win5_gof05_share=w5["gof05_share"]))
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Wartosci okien (po wyborze okien — geometria; wartosc nigdy nie wybiera rekordu)
# ---------------------------------------------------------------------------

def window_value(s_sorted, values, center, radius=5.0, min_rows: int = MIN_WINDOW_N):
    """Mediana `values` (np. d0 [um]) wierszy z |s - center| <= radius (wiersze posortowane po s). Zwraca (mediana, liczba wazna,
    okno_ok): okno uznane, gdy >= min_rows wierszy z waznym (skonczonym) d0; inaczej mediana = NaN."""
    lo = np.searchsorted(s_sorted, center - radius, side="left")
    hi = np.searchsorted(s_sorted, center + radius, side="right")
    v = np.asarray(values[lo:hi], float)
    n = int(np.isfinite(v).sum())
    if hi <= lo or n < min_rows:
        return float("nan"), n, False
    return float(np.nanmedian(v)), n, True


def pair_values(pairs: pd.DataFrame, pass_rows: dict, value_key: str = "d0", radius: float = 5.0,
                min_rows: int = MIN_WINDOW_N) -> pd.DataFrame:
    """Wartosci TSD par: mediana `value_key` w oknie +-radius wokol s_fwd na przejezdzie pary (wiersze `pass_rows[pass_id]`
    maja klucz value_key; posortowane po s). Zwraca kolumny pair_id, value, n_valid, window_ok."""
    out = []
    for r in pairs[["pair_id", "pass_id", "s_fwd"]].itertuples(index=False):
        pr = pass_rows.get(r.pass_id)
        if pr is None:
            out.append((r.pair_id, float("nan"), 0, False))
            continue
        v, n, ok = window_value(pr["s"], pr[value_key], r.s_fwd, radius, min_rows)
        out.append((r.pair_id, v, n, ok))
    return pd.DataFrame(out, columns=["pair_id", "value", "n_valid", "window_ok"])


def null_values(nulls: pd.DataFrame, pass_rows: dict, value_key: str = "d0", radius: float = 5.0,
                min_rows: int = MIN_WINDOW_N) -> pd.DataFrame:
    """Wartosci TSD par zerowych (okno W5 wokol center_s)."""
    out = []
    for r in nulls[["pair_id", "null_type", "pass_id", "center_s"]].itertuples(index=False):
        pr = pass_rows.get(r.pass_id)
        if pr is None:
            out.append((r.pair_id, r.null_type, float("nan"), 0, False))
            continue
        v, n, ok = window_value(pr["s"], pr[value_key], r.center_s, radius, min_rows)
        out.append((r.pair_id, r.null_type, v, n, ok))
    return pd.DataFrame(out, columns=["pair_id", "null_type", "value", "n_valid", "window_ok"])
