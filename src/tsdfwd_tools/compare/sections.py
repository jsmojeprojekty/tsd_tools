"""N4 tryb `geometry`: wykrywanie wspolnych odcinkow TSD-FWD (kryteria Tab. 3.2 raportu PW.S-1063).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\build_road_db.py (detect_sections, bboxes_overlap, bearing_diff_deg, cross_track_m,
haversine_m, _as_datetime; stan d89080a / 2026-10-18; progi Tab. 3.2 z rebuild_sections.py).
Przerobione: wejscie to DataFrame'y (bez bazy), zapytania do drzewa KD wektorowo (te same kryteria i te same wartosci co petla po stacjach),
progi w dataclass `SectionParams` (domyslne = Tab. 3.2), licznik odrzuconych par wg przyczyny.

Odcinek wspolny to para (sesja FWD, przejazd TSD) spelniajaca: ten sam rok kalendarzowy (i odstep <= max_days), >= min_matched stacji FWD
w promieniu radius_m od najblizszego punktu TSD, pokrycie >= min_coverage_pct (wzgledem stacji FWD lezacych w obwiedni TSD), zakres
pikietazu dopasowanych punktow >= min_overlap_len_m, |Spearman(station_m, chainage_m)| >= min_abs_spearman (MONOTONICZNOSC polozenia stacji
wzgledem pikietazu TSD — to NIE jest korelacja ugiec), kierunek wg sredniej roznicy kursow (<= bearing_tol: 'same', >= 180 - bearing_tol:
'opposite', reszta odrzucona), klasa pasa wg |mediana odleglosci poprzecznej| (<= 0,75 m 'same', <= 2,0 m 'adjacent', reszta 'far').
Uwaga: polozenie stacji to GPS anteny (bez przesuniecia na plyte), polozenie TSD to GPS wiersza (bez lagu -4,8 m) — jak w zrodle;
przyblizenie plaskie 111320 m/stopien (jak w zrodle)."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

from .geo import sequence_headings

log = logging.getLogger(__name__)

M_PER_DEG = 111_320.0
R_EARTH = 6_371_000.0


@dataclass
class SectionParams:
    radius_m: float = 8.0
    min_coverage_pct: float = 30.0
    min_abs_spearman: float = 0.80
    bearing_tol_deg: float = 30.0
    max_days: float = 400.0
    lane_same_max_m: float = 0.75
    lane_adjacent_max_m: float = 2.0
    same_year_only: bool = True
    min_overlap_len_m: float = 500.0
    min_matched_stations: int = 5


def as_datetime(v):
    """str/datetime/None -> datetime albo None (formaty jak w zrodle)."""
    if v is None or (isinstance(v, float) and np.isnan(v)) or v == "":
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _haversine_vec(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    a = np.sin(np.radians(lat2 - lat1) / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return R_EARTH * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def _cross_track_vec(p_lat, p_lon, ref_lat, ref_lon, ref_heading):
    """Skladowa prostopadla do kursu ref [m]; + = punkt na PRAWO od kierunku (UWAGA: odwrotnie niz `lateral_m` w osi korytarza)."""
    dlat = (p_lat - ref_lat) * M_PER_DEG
    dlon = (p_lon - ref_lon) * M_PER_DEG * np.cos(np.radians(ref_lat))
    th = np.radians(ref_heading)
    ux, uy = np.sin(th), np.cos(th)
    return dlon * uy + dlat * (-ux)


def _bearing_diff_vec(a, b):
    d = np.abs(a - b) % 360.0
    return np.where(d <= 180.0, d, 360.0 - d)


def _bbox(lat, lon):
    return (float(np.min(lat)), float(np.max(lat)), float(np.min(lon)), float(np.max(lon)))


def _bboxes_overlap(bb1, bb2, margin_m=200):
    margin_lat = margin_m / M_PER_DEG
    mid_lat = (bb1[0] + bb1[1] + bb2[0] + bb2[1]) / 4
    margin_lon = margin_m / (M_PER_DEG * math.cos(math.radians(mid_lat)))
    return not (bb1[1] + margin_lat < bb2[0] or bb2[1] + margin_lat < bb1[0] or
                bb1[3] + margin_lon < bb2[2] or bb2[3] + margin_lon < bb1[2])


def ensure_headings(df: pd.DataFrame, order_cols, lat="lat", lon="lon", heading="heading") -> pd.DataFrame:
    """Uzupelnia brakujacy kurs z kolejnosci punktow (centralna roznica, sasiad >= 1 m), jak compute_headings w bazie."""
    df = df.copy()
    if heading not in df:
        df[heading] = np.nan
    h = pd.to_numeric(df[heading], errors="coerce").to_numpy(float)
    if np.isnan(h).any():
        order = df.sort_values(order_cols, kind="stable").index
        pos = df.index.get_indexer(order)
        hs = sequence_headings(pd.to_numeric(df[lat], errors="coerce").to_numpy(float)[pos],
                               pd.to_numeric(df[lon], errors="coerce").to_numpy(float)[pos])
        filled = h.copy()
        sel = np.isnan(filled[pos])
        filled[pos[sel]] = hs[sel]
        h = filled
    df[heading] = h
    return df


def detect_sections(runs: dict, run_dates: dict, sessions: dict, session_info: dict,
                    p: SectionParams | None = None):
    """Wspolne odcinki TSD-FWD.

    runs: {run_id: DataFrame(lat, lon, chainage [, heading])} (wiersze z waznym GPS, posortowane po pikietazu);
    run_dates: {run_id: data przejazdu}; sessions: {session_id: DataFrame(station_id, lat, lon, station_m [, heading])}
    (posortowane po station_m, station_id); session_info: {session_id: (date_start, date_end)}.
    Zwraca (DataFrame sekcji, slownik {(session_id, run_id): DataFrame dopasowanych stacji}, liczniki odrzuconych par)."""
    p = p or SectionParams()
    index = {}
    for rid, d in runs.items():
        d = d[np.isfinite(d["lat"]) & np.isfinite(d["lon"])]
        if len(d) == 0:
            continue
        lat0 = float(d["lat"].mean())
        cos_lat0 = math.cos(math.radians(lat0))
        xy = np.column_stack([d["lon"].to_numpy(float) * M_PER_DEG * cos_lat0, d["lat"].to_numpy(float) * M_PER_DEG])
        index[rid] = dict(tree=cKDTree(xy), d=d.reset_index(drop=True), cos_lat0=cos_lat0,
                          bbox=_bbox(d["lat"].to_numpy(float), d["lon"].to_numpy(float)), date=run_dates.get(rid))
    rows, matches = [], {}
    cnt = dict(low_coverage=0, few_stations=0, short_span=0, noise=0, ambiguous_direction=0, diff_year=0)
    section_id = 0
    for sid, fw in sessions.items():
        fw = fw[np.isfinite(fw["lat"]) & np.isfinite(fw["lon"])]
        if len(fw) == 0:
            continue
        fwd_total = len(fw)
        sess_bb = _bbox(fw["lat"].to_numpy(float), fw["lon"].to_numpy(float))
        ds, de = session_info.get(sid, (None, None))
        flat, flon = fw["lat"].to_numpy(float), fw["lon"].to_numpy(float)
        fhead = fw["heading"].to_numpy(float) if "heading" in fw else np.full(len(fw), np.nan)
        sm_all = fw["station_m"].to_numpy(float)
        for rid, tx in index.items():
            if not _bboxes_overlap(sess_bb, tx["bbox"], margin_m=max(p.radius_m * 2, 50)):
                continue
            ds_dt, tf_dt = as_datetime(ds), as_datetime(tx["date"])
            if p.same_year_only and (not (ds_dt and tf_dt) or ds_dt.year != tf_dt.year):
                cnt["diff_year"] += 1
                continue
            if ds_dt and tf_dt and abs((tf_dt - ds_dt).total_seconds()) / 86400.0 > p.max_days:
                continue
            d, cos_lat0 = tx["d"], tx["cos_lat0"]
            tbb = tx["bbox"]
            margin_lat = p.radius_m / M_PER_DEG
            margin_lon = p.radius_m / (M_PER_DEG * max(cos_lat0, 0.1))
            fwd_in_overlap = int(((tbb[0] - margin_lat <= flat) & (flat <= tbb[1] + margin_lat) &
                                  (tbb[2] - margin_lon <= flon) & (flon <= tbb[3] + margin_lon)).sum())
            q = np.column_stack([flon * M_PER_DEG * cos_lat0, flat * M_PER_DEG])
            dist, idx = tx["tree"].query(q, distance_upper_bound=p.radius_m + 0.5)
            found = np.isfinite(dist) & (idx < len(d))
            ii = np.where(found, idx, 0)
            tlat, tlon = d["lat"].to_numpy(float)[ii], d["lon"].to_numpy(float)[ii]
            thead = d["heading"].to_numpy(float)[ii] if "heading" in d else np.full(len(ii), np.nan)
            cm = d["chainage"].to_numpy(float)[ii]
            real_d = _haversine_vec(tlat, tlon, flat, flon)
            ref_head = np.where(np.isfinite(thead), thead, fhead)
            ok = found & (real_d <= p.radius_m) & np.isfinite(ref_head) & np.isfinite(sm_all) & np.isfinite(cm)
            m = np.nonzero(ok)[0]
            n_m = len(m)
            coverage_pct = 100.0 * n_m / max(fwd_in_overlap, 1)
            coverage_full_pct = 100.0 * n_m / max(fwd_total, 1)
            if n_m < p.min_matched_stations:
                if n_m > 0:
                    cnt["few_stations"] += 1
                continue
            if coverage_pct < p.min_coverage_pct:
                cnt["low_coverage"] += 1
                continue
            sm_arr, cm_arr = sm_all[m], cm[m]
            overlap_len = float(cm_arr.max() - cm_arr.min())
            if overlap_len < p.min_overlap_len_m:
                cnt["short_span"] += 1
                continue
            try:
                corr = float(spearmanr(sm_arr, cm_arr)[0])
            except Exception:                                   # noqa: BLE001 — jak w zrodle
                corr = 0.0
            if not np.isfinite(corr):
                corr = 0.0
            if abs(corr) < p.min_abs_spearman:
                cnt["noise"] += 1
                continue
            xtrack = _cross_track_vec(flat[m], flon[m], tlat[m], tlon[m], ref_head[m])
            median_xtrack = float(np.median(xtrack))
            bd = _bearing_diff_vec(thead[m], fhead[m])
            bd = bd[np.isfinite(bd)]
            mean_bdiff = float(np.mean(bd)) if len(bd) else None
            if mean_bdiff is None:
                direction = "same" if corr > 0 else "opposite"      # zapas jak w zrodle (brak kursow po obu stronach)
            elif mean_bdiff <= p.bearing_tol_deg:
                direction = "same"
            elif mean_bdiff >= 180.0 - p.bearing_tol_deg:
                direction = "opposite"
            else:
                cnt["noise"] += 1
                cnt["ambiguous_direction"] += 1
                continue
            ax = abs(median_xtrack)
            lane = "same" if ax <= p.lane_same_max_m else ("adjacent" if ax <= p.lane_adjacent_max_m else "far")
            section_id += 1
            rows.append(dict(section_id=section_id, session_id=sid, run_id=rid, direction=direction, spearman_corr=corr,
                             coverage_pct=coverage_pct, coverage_full_pct=coverage_full_pct, fwd_matched=n_m,
                             fwd_total=fwd_total, fwd_in_overlap=fwd_in_overlap, station_m_min=float(sm_arr.min()),
                             station_m_max=float(sm_arr.max()), chainage_m_min=float(cm_arr.min()), chainage_m_max=float(cm_arr.max()),
                             median_xtrack_m=median_xtrack, mean_bearing_diff=mean_bdiff, lane_class=lane,
                             tsd_date=tx["date"], fwd_date_start=ds, fwd_date_end=de))
            matches[(sid, rid)] = pd.DataFrame(dict(station_id=fw["station_id"].to_numpy()[m], station_m=sm_arr, chainage_m=cm_arr,
                                                    xtrack_m=xtrack, bearing_diff=_bearing_diff_vec(thead[m], fhead[m]),
                                                    distance_m=real_d[m], lat=flat[m], lon=flon[m]))
    cnt["n_sections"] = len(rows)
    return pd.DataFrame(rows), matches, cnt
