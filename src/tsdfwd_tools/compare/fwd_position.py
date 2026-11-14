"""N4 tryb `geometry`: polozenie plyty FWD z anteny GPS i dystansomierza (stacje FWD -> s_fwd na korytarzu).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b1_geometry.py (project_antenna_k1, direction_from_data, plate_offset, compute_k2,
split_runs, fit_run_robust, compute_k3_k4; stan d89080a / 2026-10-18) oraz bak\\e2a1b_position.py (unit_factor, anchor_of).
Zasada nadrzedna zrodla zachowana: modul NIE czyta wartosci ugiec (tylko polozenie, czas, aparat).

Kroki: K1 rzut anteny GPS na korytarz (pas 'same' <= 1,75 m, 'adjacent' <= 5 m), kierunek sesji Z DANYCH (znak ilorazu
ds_ant / d station_m); K2 przesuniecie anteny przed plyte WYLACZNIE wzdluz korytarza wg tabeli regul aparatu (jedna, jawna
tabela z konfiguracji; domyslnie regula P043b: 8002-367 5,5 m do 2025-10-09, potem 0); K3 podzial sesji na ciagi i odporna
regresja dystansomierza (wariant `short_zero`: eps = 0 dla ciagow < 1000 m lub < 10 stacji); K4 s_fwd = s_dmi (ciag >= 5
stacji, dopasowanie poprawne) albo s_plate_gps, oraz sigma_long = sqrt(sigma_a^2 + sigma_era^2)."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .geo import (DEFAULT_AXIS, AxisParams, best_projection, convergence_deg, robust_sd, sequence_headings, to_2180)

RUN_JUMP_FACTOR = 3.0        # skok station_m > tyle x mediana kroku sesji -> nowy ciag
MIN_RUN_N = 5                # ciag krotszy -> s_fwd = s_plate_gps (pos_source = 'plate_gps')
GROSS_MIN_M = 5.0
GROSS_MAD_MULT = 4.0
EPS_MIN_LEN_M = 1000.0       # wariant 'short_zero': ciag krotszy -> eps = 0 (tylko dopasowanie wyrazu wolnego)
EPS_MIN_N = 10

# sigma_era [m]: niepewnosc polozenia plyty zalezna od ery aparatu/odbiornika GPS (zrodlo: e2b1_params.csv, P043b wpis 164)
DEFAULT_SIGMA_ERA = {"new": 0.379914, "old": 1.93146, "hwd": 0.195144, "hwd_cautious": 1.93146,
                     "unconfirmed": 1.93146, "unknown": float("nan")}


@dataclass
class AntennaRule:
    """Regula przesuniecia anteny przed plyte dla aparatu: obowiazuje dla dat z [from_date, until_date) (napisy RRRR-MM-DD)."""
    device: str
    d_m: float
    era: str
    confirmed: int = 1
    from_date: str | None = None
    until_date: str | None = None


def default_antenna_rules() -> list:
    """Regula P043b: 8002-367 stary odbiornik 5,5 m do 2025-10-09, potem 0; HWD 8082-119 1,0 m; 8002-369 1,0 m (niepotwierdzone)."""
    return [AntennaRule("8002-367", 5.5, "old", 1, None, "2025-10-09"),
            AntennaRule("8002-367", 0.0, "new", 1, "2025-10-09", None),
            AntennaRule("8082-119", 1.0, "hwd", 1),
            AntennaRule("8002-369", 1.0, "unconfirmed", 0)]


def plate_offset(device, date, rules=None):
    """d [m], era i potwierdzenie na dany dzien: (d, era, confirmed). Brak daty traktowany jak data najpozniejszej reguly aparatu
    (jak w zrodle: 'new' dla 8002-367). Aparat bez reguly: (0, 'unknown', 0)."""
    rules = default_antenna_rules() if rules is None else rules
    cand = [r for r in rules if r.device == device]
    for r in cand:
        if r.until_date is not None and not (date and date < r.until_date):
            continue
        if r.from_date is not None and date and date < r.from_date:
            continue
        return float(r.d_m), r.era, int(r.confirmed)
    return 0.0, "unknown", 0


@dataclass
class PositionParams:
    rules: list = field(default_factory=default_antenna_rules)
    sigma_era: dict = field(default_factory=lambda: dict(DEFAULT_SIGMA_ERA))
    eps_variant: str = "short_zero"          # short_zero (wybrany w P043b) | full
    axis: AxisParams = field(default_factory=AxisParams)


# ---------------------------------------------------------------------------
# K1: rzut anteny, kierunek z danych
# ---------------------------------------------------------------------------

def unit_factor(station_m, s_ref):
    """Wspolczynnik jednostek station_m -> metry i kierunek jazdy z ilorazu ds_ref / d station_m (stacje posortowane po
    station_m, kroki > 0). Zwraca (factor 1000 | 1 | None, direction +1 | -1 | 0, mediana |iloraz|)."""
    sm, s = np.asarray(station_m, float), np.asarray(s_ref, float)
    ok = np.isfinite(sm) & np.isfinite(s)
    sm, s = sm[ok], s[ok]
    if len(sm) < 2:
        return None, 0, float("nan")
    o = np.argsort(sm, kind="stable")
    sm, s = sm[o], s[o]
    dsm, ds = np.diff(sm), np.diff(s)
    k = dsm > 1e-9
    if not k.any():
        return None, 0, float("nan")
    med = float(np.median(ds[k] / dsm[k]))
    a = abs(med)
    factor = 1000 if 300 < a < 3000 else (1 if 0.3 < a < 3 else None)
    return factor, (1 if med > 0 else -1 if med < 0 else 0), a


def anchor_of(station_m, s_ref, factor, direction):
    """Kotwica GPS - DMI: mediana (s_ref - kierunek x wspolczynnik x station_m) i reszty wokol niej."""
    sm, s = np.asarray(station_m, float), np.asarray(s_ref, float)
    ok = np.isfinite(sm) & np.isfinite(s)
    if ok.sum() == 0 or not factor or not direction:
        return float("nan"), np.array([])
    base = s[ok] - direction * factor * sm[ok]
    a = float(np.median(base))
    return a, base - a


def project_antenna(corridors, st: pd.DataFrame, p: PositionParams):
    """K1: rzut anteny GPS na korytarz (te same reguly pasa co w korytarzach: lane_half_m, potem fwd_adj_m).
    Zwraca DataFrame z kolumnami corridor_id (-1 = brak), s_ant, lat_ant, lane_match, gx, gy."""
    ax = p.axis
    lat = pd.to_numeric(st["lat"], errors="coerce").to_numpy(float)
    lon = pd.to_numeric(st["lon"], errors="coerce").to_numpy(float)
    hd = (pd.to_numeric(st["heading_deg"], errors="coerce").to_numpy(float) if "heading_deg" in st
          else np.full(len(st), np.nan))
    gx, gy = to_2180(lat, lon)
    hd_grid = (hd - convergence_deg(lat, lon)) % 360.0
    live = list(corridors)
    cid, s, lat_ant = best_projection(live, gx, gy, hd_grid, ax.lane_half_m, True, ax)
    lane = np.where(cid >= 0, "same", "none").astype(object)
    m = np.nonzero(cid < 0)[0]
    if len(m):
        c2, s2, l2 = best_projection(live, gx[m], gy[m], hd_grid[m], ax.fwd_adj_m, True, ax)
        cid[m], s[m], lat_ant[m] = c2, s2, l2
        lane[m] = np.where(c2 >= 0, "adjacent", "none")
    return pd.DataFrame({"corridor_id": cid.astype(int), "s_ant": s, "lat_ant": lat_ant, "lane_match": lane,
                         "gx": gx, "gy": gy}, index=st.index)


def direction_from_data(st: pd.DataFrame):
    """K1: kierunek sesji (+1/-1/0) Z DANYCH (unit_factor na s_ant vs station_m stacji w pasie 'same'/'adjacent' korytarza
    dominujacego w sesji), NIE z heading_deg. Zwraca (kolumny direction/factor dla stacji, tabela sesji)."""
    sessions = {}
    direction = pd.Series(0, index=st.index, dtype=int)
    factor = pd.Series(1, index=st.index, dtype=int)
    for sp, v in st.groupby("session_id", sort=False):
        ok_c = v["corridor_id"] >= 0
        cnt = v.loc[ok_c, "corridor_id"].value_counts()
        main_corr = int(cnt.idxmax()) if len(cnt) else None          # remis: pierwszy napotkany (jak max po slowniku)
        if len(cnt):
            top = cnt[cnt == cnt.max()].index
            order = [c for c in v["corridor_id"].tolist() if c >= 0]
            main_corr = next(c for c in order if c in set(top))
        sub = v[(v["corridor_id"] == main_corr) & v["s_ant"].notna()] if main_corr is not None else v.iloc[0:0]
        sm = pd.to_numeric(sub["station_m"], errors="coerce").to_numpy(float)
        sa = sub["s_ant"].to_numpy(float)
        fac, dirn, ratio = unit_factor(sm, sa)
        guessed = 0
        if fac is None:
            fac = 1000 if len(sm) and np.nanmax(np.abs(sm)) <= 5.0 else 1
            guessed = 1
        anchor, resid = anchor_of(sm, sa, fac, dirn) if dirn else (float("nan"), np.array([]))
        sessions[sp] = dict(session_id=sp, main_corridor=main_corr, n_main=len(sub), factor=fac,
                            units=("km" if fac == 1000 else "m" if fac == 1 else "?"), factor_guessed=guessed,
                            ratio_med=ratio, direction=dirn, anchor_m=anchor,
                            resid_mad=robust_sd(resid) if len(resid) > 1 else None)
        direction.loc[v.index] = dirn
        factor.loc[v.index] = fac
    return direction, factor, sessions


# ---------------------------------------------------------------------------
# K3: ciagi i regresja dystansomierza
# ---------------------------------------------------------------------------

def split_runs(sm, cid, direction):
    """Podzial sesji na ciagi: zmiana korytarza, skok station_m > 3x mediana kroku, zawracanie, powtorzona wartosc station_m
    (awaria DMI). Zwraca tablice run_id (0, 1, 2, ...)."""
    n = len(sm)
    run = np.zeros(n, dtype=np.int64)
    if n == 0:
        return run
    d = np.diff(sm)
    fd = d[np.isfinite(d) & (d != 0)]
    step = float(np.median(np.abs(fd))) if len(fd) else 1.0
    cur = 0
    for i in range(1, n):
        br = False
        if cid[i] != cid[i - 1]:
            br = True
        elif not (np.isfinite(sm[i]) and np.isfinite(sm[i - 1])):
            br = True
        else:
            dd = sm[i] - sm[i - 1]
            if dd == 0:
                br = True
            elif abs(dd) > RUN_JUMP_FACTOR * step:
                br = True
            elif direction and np.sign(dd) != np.sign(direction):
                br = True
        if br:
            cur += 1
        run[i] = cur
    return run


def fit_run_robust(sm, y, direction, factor, force_eps_zero=False):
    """Odporna regresja y = a + slope*sm (odrzucenie iteracyjne |reszta| > 4*sigma_MAD). Zwraca None, gdy < 2 skonczone pary.
    eps_ppm = (slope / (kierunek*factor) - 1) * 1e6. force_eps_zero=True (ciagi krotkie): slope USTALONE na kierunek*factor
    (eps = 0), dopasowywany tylko wyraz wolny 'a' (odporna mediana reszt, te same odrzucenia 4*sigma_MAD)."""
    sm = np.asarray(sm, float)
    y = np.asarray(y, float)
    ok = np.isfinite(sm) & np.isfinite(y)
    n_tot = int(ok.sum())
    if n_tot < 2:
        return None
    idx = np.nonzero(ok)[0]
    sm_o, y_o = sm[idx], y[idx]
    keep = np.ones(len(idx), dtype=bool)
    a = slope = float("nan")
    sigma_mad = float("nan")
    if force_eps_zero:
        slope = float(direction * factor) if (direction and factor) else float("nan")
        if not np.isfinite(slope):
            return None
        for _ in range(8):
            if keep.sum() < 1:
                break
            resid0 = y_o - slope * sm_o
            a = float(np.median(resid0[keep]))
            resid = y_o - (a + slope * sm_o)
            sigma_mad = robust_sd(resid[keep])
            if not np.isfinite(sigma_mad) or sigma_mad <= 0:
                break
            new_keep = np.abs(resid) <= GROSS_MAD_MULT * sigma_mad
            if np.array_equal(new_keep, keep):
                break
            keep = new_keep
    else:
        for _ in range(8):
            if keep.sum() < 2:
                break
            A = np.vstack([np.ones(int(keep.sum())), sm_o[keep]]).T
            coef, *_ = np.linalg.lstsq(A, y_o[keep], rcond=None)
            a, slope = float(coef[0]), float(coef[1])
            resid = y_o - (a + slope * sm_o)
            sigma_mad = robust_sd(resid[keep])
            if not np.isfinite(sigma_mad) or sigma_mad <= 0:
                break
            new_keep = np.abs(resid) <= GROSS_MAD_MULT * sigma_mad
            if np.array_equal(new_keep, keep):
                break
            keep = new_keep
    resid_all = y_o - (a + slope * sm_o) if np.isfinite(a) else np.full(len(idx), np.nan)
    n_used = int(keep.sum())
    eps_ppm = (0.0 if force_eps_zero else
               ((slope / (direction * factor) - 1) * 1e6) if (direction and factor and np.isfinite(slope)) else float("nan"))
    return dict(a=a, slope=slope, eps_ppm=eps_ppm, sigma_mad=sigma_mad, n=n_tot, n_used=n_used,
                n_rejected=n_tot - n_used, idx=idx, resid=resid_all, keep=keep)


def compute_positions(st: pd.DataFrame, p: PositionParams):
    """K3/K4: podzial na ciagi, regresja dystansomierza, s_fwd + sigma_long. st: kolumny session_id, station_id, station_m, time,
    corridor_id, s_ant, direction, factor, s_plate_gps, era. Zwraca (kolumny wynikowe DataFrame, lista wierszy ciagow)."""
    out_cols = ["run_id", "pos_source", "s_dmi", "s_fwd", "residual_gps_m", "gross_gps", "sigma_a", "sigma_long",
                "sigma_long_hwd_b"]
    res = pd.DataFrame({c: np.nan for c in out_cols}, index=st.index)
    res["pos_source"] = None
    run_rows = []
    sigma_era = p.sigma_era
    sig_hwd_b = sigma_era.get("hwd_cautious", float("nan"))
    for sp, v0 in st.groupby("session_id", sort=False):
        v = v0.assign(_t=v0["time"].fillna("").astype(str)).sort_values(["_t", "station_id"], kind="stable")
        sm = pd.to_numeric(v["station_m"], errors="coerce").to_numpy(float)
        cid = v["corridor_id"].to_numpy(int)
        direction = int(v["direction"].iloc[0])
        factor = int(v["factor"].iloc[0])
        run_id = split_runs(sm, cid, direction)
        idx_all = v.index.to_numpy()
        for rid in sorted(set(run_id.tolist())):
            sel = run_id == rid
            ix = idx_all[sel]
            members = v.loc[ix]
            sm_r = sm[sel]
            y_r = members["s_plate_gps"].to_numpy(float)
            n_m = len(members)
            ok_len = np.isfinite(sm_r)
            length_m = (float(np.nanmax(sm_r[ok_len]) - np.nanmin(sm_r[ok_len])) * factor) if (ok_len.sum() >= 2 and factor) else 0.0
            force_zero = p.eps_variant == "short_zero" and (length_m < EPS_MIN_LEN_M or n_m < EPS_MIN_N)
            fit = fit_run_robust(sm_r, y_r, direction, factor, force_eps_zero=force_zero) if (direction and factor) else None
            valid = bool(fit and n_m >= MIN_RUN_N and np.isfinite(fit.get("a", float("nan"))))
            era_counts = members["era"].value_counts()
            main_era = None
            if len(era_counts):
                top = era_counts[era_counts == era_counts.max()].index
                main_era = next(e for e in members["era"].tolist() if e in set(top))
            sig_era = sigma_era.get(main_era, float("nan"))
            res.loc[ix, "run_id"] = rid
            if valid:
                resid_map = np.full(n_m, np.nan)
                resid_map[fit["idx"]] = fit["resid"]
                sigma_a = fit["sigma_mad"] / math.sqrt(max(fit["n_used"], 1))
                s_dmi = fit["a"] + fit["slope"] * sm_r
                resid_ok = np.isfinite(resid_map)
                if np.isfinite(fit["sigma_mad"]):
                    gross = resid_ok & (np.abs(resid_map) > max(GROSS_MIN_M, GROSS_MAD_MULT * fit["sigma_mad"]))
                else:
                    gross = np.zeros(n_m, dtype=bool)
                sig_long = math.sqrt(sigma_a ** 2 + sig_era ** 2) if np.isfinite(sig_era) else sigma_a
                sig_long_b = (math.sqrt(sigma_a ** 2 + sig_hwd_b ** 2)
                              if (main_era == "hwd" and np.isfinite(sig_hwd_b)) else sig_long)
                res.loc[ix, "pos_source"] = "dmi"
                res.loc[ix, "s_dmi"] = np.where(np.isfinite(sm_r), s_dmi, np.nan)
                res.loc[ix, "s_fwd"] = np.where(np.isfinite(sm_r), s_dmi, np.nan)
                res.loc[ix, "residual_gps_m"] = resid_map
                res.loc[ix, "gross_gps"] = gross.astype(int)
                res.loc[ix, "sigma_a"] = sigma_a
                res.loc[ix, "sigma_long"] = sig_long
                res.loc[ix, "sigma_long_hwd_b"] = sig_long_b
                run_rows.append(dict(session_id=sp, run_id=rid, n=n_m, n_used=fit["n_used"], n_rejected=fit["n_rejected"],
                                     direction=direction, factor=factor, a=fit["a"], slope=fit["slope"],
                                     eps_ppm=fit["eps_ppm"], sigma_mad=fit["sigma_mad"], fit_valid=1, main_era=main_era,
                                     length_m=length_m, eps_forced_zero=int(force_zero), n_gross=int(gross.sum())))
            else:
                anchor, resid = (anchor_of(sm_r, y_r, factor, direction) if (direction and factor)
                                 else (float("nan"), np.array([])))
                sigma_mad_fb = robust_sd(resid) if len(resid) > 1 else float("nan")
                sigma_a = (sigma_mad_fb / math.sqrt(max(n_m, 1))) if np.isfinite(sigma_mad_fb) else float("nan")
                if np.isfinite(anchor):
                    resid_k = np.where(np.isfinite(y_r), y_r - (anchor + direction * factor * sm_r), np.nan)
                else:
                    resid_k = np.full(n_m, np.nan)
                if np.isfinite(sigma_mad_fb):
                    gross = np.isfinite(resid_k) & (np.abs(resid_k) > max(GROSS_MIN_M, GROSS_MAD_MULT * sigma_mad_fb))
                else:
                    gross = np.zeros(n_m, dtype=bool)
                if np.isfinite(sig_era) and np.isfinite(sigma_a):
                    sig_long = math.sqrt(sigma_a ** 2 + sig_era ** 2)
                else:
                    sig_long = sig_era if np.isfinite(sig_era) else sigma_a
                sig_long_b = (math.sqrt(sigma_a ** 2 + sig_hwd_b ** 2)
                              if (main_era == "hwd" and np.isfinite(sig_hwd_b) and np.isfinite(sigma_a)) else sig_long)
                res.loc[ix, "pos_source"] = "plate_gps"
                res.loc[ix, "s_fwd"] = y_r
                res.loc[ix, "residual_gps_m"] = resid_k
                res.loc[ix, "gross_gps"] = gross.astype(int)
                res.loc[ix, "sigma_a"] = sigma_a
                res.loc[ix, "sigma_long"] = sig_long
                res.loc[ix, "sigma_long_hwd_b"] = sig_long_b
                run_rows.append(dict(session_id=sp, run_id=rid, n=n_m,
                                     n_used=int(np.isfinite(resid).sum()) if len(resid) else 0, n_rejected=0,
                                     direction=direction, factor=factor, a=anchor if np.isfinite(anchor) else None,
                                     length_m=length_m, eps_forced_zero=int(force_zero),
                                     slope=(direction * factor) if direction and factor else None,
                                     eps_ppm=0.0 if direction and factor else None, sigma_mad=sigma_mad_fb, fit_valid=0,
                                     main_era=main_era, n_gross=int(gross.sum())))
    return res, run_rows


def fwd_plate_positions(corridors, stations: pd.DataFrame, p: PositionParams | None = None):
    """Polozenie plyty FWD na korytarzach. stations: kolumny station_id, session_id, station_m, lat, lon, time, device, date
    [, heading_deg]. Zwraca (tabela stacji z kolumnami K1-K4, tabela sesji, tabela ciagow)."""
    p = p or PositionParams()
    st = stations.copy()
    for need in ("station_id", "session_id", "station_m", "lat", "lon", "device", "date"):
        if need not in st:
            raise ValueError(f"stacje FWD: brak kolumny {need!r}")
    st["date"] = st["date"].fillna("").astype(str).str[:10]
    if "time" not in st:
        st["time"] = ""
    st = st.sort_values(["session_id", "time", "station_id"], kind="stable").reset_index(drop=True)
    if "heading_deg" not in st:
        st["heading_deg"] = np.nan
    miss = pd.to_numeric(st["heading_deg"], errors="coerce").isna()
    if miss.any():                                  # brak kursu: z kolejnosci stacji w sesji (jak compute_headings w bazie)
        hd = pd.to_numeric(st["heading_deg"], errors="coerce").to_numpy(float).copy()
        for _, ix in st.groupby("session_id", sort=False).indices.items():
            h = sequence_headings(pd.to_numeric(st["lat"], errors="coerce").to_numpy(float)[ix],
                                  pd.to_numeric(st["lon"], errors="coerce").to_numpy(float)[ix])
            fill = np.isnan(hd[ix])
            hd[ix[fill]] = h[fill]
        st["heading_deg"] = hd
    k1 = project_antenna(corridors, st, p)
    st = pd.concat([st, k1], axis=1)
    direction, factor, sessions = direction_from_data(st)
    st["direction"], st["factor"] = direction, factor
    d_era = [plate_offset(dev, dt, p.rules) for dev, dt in zip(st["device"], st["date"])]
    st["d_m"] = [x[0] for x in d_era]
    st["era"] = [x[1] for x in d_era]
    st["antenna_offset_confirmed"] = [x[2] for x in d_era]
    have = st["s_ant"].notna() & (st["direction"] != 0)
    st["s_plate_gps"] = np.where(have, st["s_ant"] - st["direction"] * st["d_m"], np.nan)
    k34, run_rows = compute_positions(st, p)
    st = pd.concat([st, k34], axis=1)
    return st, pd.DataFrame(sessions.values()), pd.DataFrame(run_rows)
