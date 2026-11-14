"""N4: estymator lambdy do regresji Deminga (lambda = Var(blad FWD) / Var(blad TSD) na skali log) z powtorzen pomiarow.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b2_values.py (compute_lambda_d0_and_curv, build_lambda_rows, mad_robust_sd: sigma_TSD z roznic
log(d0) w tych samych binach 10 m po s_ref w przejazdach z jednego dnia), bak\\e1_sref.py (krok 6: biny pokryte przejsciem przy >= 5
punktach, pary przejsc w binie, dt, beton), bak\\e12_noise.py (fwd_scales: sigma_FWD z powtorzen stacji FWD w oknach floor(s_ref / L);
fwd_pair_set/station_pairs/sigma_decomp, mad_sigma), stan d89080a / 2026-10-18.
Przerobione: wejscie to tablice/DataFrame'y (bez bazy), progi w dataclass `LambdaParams`.

sigma_TSD  = 1,4826 * MAD(ln d_i - ln d_j) / sqrt(2) po parach przejazdow w tym samym binie korytarza (|dt| <= 1 dzien, poza betonem);
sigma_FWD  = 1,4826 * MAD(D - mu_ij) / sqrt(2) ("within") po parach sesji FWD tego samego aparatu w oknie 10 m, |dT powierzchni| < 3 C,
             od 2024 r., poza betonem (mu_ij = mediana roznic pary sesji; pary z jednym oknem pomijane);
lambda     = sigma_FWD^2 / sigma_TSD^2.
Raport PW.S-1063: lambda d0 = 0,11787 (sigma_TSD 0,296408 z 2015 par binow, sigma_FWD 0,101763 z 128 par okien)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

SQRT2 = math.sqrt(2.0)


@dataclass
class LambdaParams:
    bin_m: float = 10.0                  # skala binow/okien [m]
    cover_min_n: int = 5                 # bin pokryty przez przejazd TSD, gdy >= tyle punktow
    tsd_max_dt_days: float = 1.0         # pary przejazdow TSD z jednego dnia (|dt| <= 1 d)
    fwd_from_date: str | None = "2024-01-01"   # stacje FWD od tej daty (era rejestratora 2.0); None = wszystkie
    fwd_max_dtemp_c: float = 3.0         # |dT powierzchni| pary okien FWD
    fwd_min_stations: int = 1            # min. stacji sesji w oknie FWD
    exclude_concrete: bool = True        # poza betonem (gdy dane maja znacznik betonu)
    mu_min_n: int = 3                    # min. okien pary sesji do rozkladu mu_ij (statystyka pomocnicza)


def mad_sigma(x) -> float:
    """1,4826 * MAD wokol mediany (wartosci skonczone); NaN, gdy brak."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else float("nan")


def mad_robust_sd(x) -> float:
    """Jak mad_sigma, ale NaN przy < 2 wartosciach (zrodlo: e2b2_values.mad_robust_sd)."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return float("nan")
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


def group_median(gid, vals, G):
    ok = np.isfinite(vals)
    g, v = gid[ok], vals[ok]
    cnt = np.bincount(g, minlength=G)
    med = np.full(G, np.nan)
    if len(v) == 0:
        return med, cnt
    order = np.lexsort((v, g))
    v = v[order]
    starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    has = cnt > 0
    lo = starts + (cnt - 1) // 2
    hi = starts + cnt // 2
    med[has] = 0.5 * (v[lo[has]] + v[hi[has]])
    return med, cnt


def sigma_decomp(delta, pair_idx, mu_min_n: int = 3) -> dict:
    """Dekompozycja szumu z roznic D = ln d_i - ln d_j: mu_ij = mediana D pary sesji; sigma_total = 1,4826 MAD(D) / sqrt(2);
    sigma_within = 1,4826 MAD(D - mu_ij) / sqrt(2) (pary z jednym oknem pomijane). Zrodlo: e12_noise.sigma_decomp."""
    delta = np.asarray(delta, float)
    pair_idx = np.asarray(pair_idx)
    ok = np.isfinite(delta)
    delta, pair_idx = delta[ok], pair_idx[ok]
    out = dict(n=int(len(delta)), n_pairs=0, sigma_total_mad=float("nan"), sigma_within_mad=float("nan"), mu_sd=float("nan"))
    if len(delta) == 0:
        return out
    up, gid = np.unique(pair_idx, return_inverse=True)
    G = len(up)
    out["n_pairs"] = int(G)
    mu, cnt = group_median(gid, delta, G)
    res = delta - mu[gid]
    multi = cnt[gid] >= 2
    out["sigma_total_mad"] = mad_sigma(delta) / SQRT2
    out["sigma_within_mad"] = mad_sigma(res[multi]) / SQRT2 if multi.any() else float("nan")
    mm = mu[cnt >= mu_min_n]
    if len(mm) >= 2:
        out["mu_sd"] = float(np.std(mm, ddof=1))
    return out


# ---------------------------------------------------------------------------
# TSD: sigma z par przejazdow w tych samych binach korytarza
# ---------------------------------------------------------------------------

def _noon_epoch(date) -> float:
    return float(np.datetime64(f"{str(date)[:10]}T12:00:00", "s").astype("int64")) if date else float("nan")


def tsd_bin_table(pass_rows: dict, pass_dates: dict, pass_corridor: dict, p: LambdaParams) -> pd.DataFrame:
    """Tabela binow pokrytych przez przejazdy: (corridor, bin, pass, n, d0_med, t_eff, concrete_share).
    pass_rows[pid]: dict(s [, d0, t (sekundy epoki), conc (0/1)]); t_eff = mediana czasu wierszy binu albo poludnie daty przejazdu."""
    recs = []
    for pid in sorted(pass_rows):
        pr = pass_rows[pid]
        s = np.asarray(pr["s"], float)
        ok = np.isfinite(s)
        if not ok.any():
            continue
        bins = np.floor(s[ok] / p.bin_m).astype(np.int64)
        ub, gid = np.unique(bins, return_inverse=True)
        G = len(ub)
        n = np.bincount(gid, minlength=G)
        d0 = group_median(gid, np.asarray(pr["d0"], float)[ok], G)[0] if "d0" in pr else np.full(G, np.nan)
        t = np.asarray(pr["t"], float)[ok] if "t" in pr else np.full(ok.sum(), np.nan)
        tmed = group_median(gid, t, G)[0]
        noon = _noon_epoch(pass_dates.get(pid))
        t_eff = np.where(np.isfinite(tmed), tmed, noon)
        conc = (np.bincount(gid, weights=np.asarray(pr["conc"], float)[ok], minlength=G) / np.maximum(n, 1)) if "conc" in pr else np.zeros(G)
        for k in range(G):
            recs.append((pass_corridor[pid], int(ub[k]), pid, int(n[k]), float(d0[k]), float(t_eff[k]), float(conc[k])))
    return pd.DataFrame(recs, columns=["corridor_id", "bin_id", "pass_id", "n", "d0_med", "t_eff", "concrete_share"])


def tsd_repeat_sigma(bins: pd.DataFrame, p: LambdaParams | None = None) -> dict:
    """sigma_TSD z par przejazdow w tych samych binach (e1_bin_pairs: dt <= tsd_max_dt_days, poza betonem) i roznic ln mediany d0 biny."""
    p = p or LambdaParams()
    b = bins[bins["n"] >= p.cover_min_n]
    diffs, n_pairs_bins, n_bins = [], 0, 0
    for _, g in b.groupby(["corridor_id", "bin_id"], sort=False):
        if len(g) < 2:
            continue
        n_bins += 1
        conc_bin = g["concrete_share"].max() >= 0.5
        if p.exclude_concrete and conc_bin:
            continue
        d0, t = g["d0_med"].to_numpy(float), g["t_eff"].to_numpy(float)
        for i, j in combinations(range(len(g)), 2):
            if abs(t[i] - t[j]) / 86400.0 > p.tsd_max_dt_days:
                continue
            n_pairs_bins += 1
            if np.isfinite(d0[i]) and np.isfinite(d0[j]) and d0[i] > 0 and d0[j] > 0:
                diffs.append(math.log(d0[i]) - math.log(d0[j]))
    return dict(sigma=mad_robust_sd(diffs) / SQRT2 if diffs else float("nan"),
                median_diff_log=float(np.median(diffs)) if diffs else float("nan"),
                n_pairs=len(diffs), n_pairs_before_d0=n_pairs_bins, n_bins_repeated=n_bins)


# ---------------------------------------------------------------------------
# FWD: sigma z powtorzen stacji w oknach 10 m (rozne sesje, ten sam aparat)
# ---------------------------------------------------------------------------

def fwd_repeat_sigma(st: pd.DataFrame, p: LambdaParams | None = None) -> dict:
    """sigma_FWD (within) z par sesji w oknach floor(s / bin_m). st: kolumny station, corridor, s, session, device, date (RRRR-MM-DD),
    temp (temperatura powierzchni, IR), ld0 (ln D0), opcjonalnie conc (0/1). Stacje bez temperatury sa pomijane (jak w zrodle)."""
    p = p or LambdaParams()
    sel = np.isfinite(st["temp"].to_numpy(float))
    if p.exclude_concrete and "conc" in st:
        sel &= st["conc"].to_numpy(float) == 0
    if p.fwd_from_date:
        sel &= st["date"].astype(str).to_numpy() >= p.fwd_from_date
    d = st[sel]
    empty = dict(sigma_within=float("nan"), sigma_total=float("nan"), n_pairs=0, n_session_pairs=0, n_windows=0)
    if len(d) == 0:
        return empty
    w = np.floor(d["s"].to_numpy(float) / p.bin_m).astype(np.int64)
    key = np.column_stack([d["session"].to_numpy(np.int64), d["corridor"].to_numpy(np.int64), w])
    uk, inv = np.unique(key, axis=0, return_inverse=True)
    inv = np.ravel(inv)
    G = len(uk)
    med = group_median(inv, d["ld0"].to_numpy(float), G)[0]
    cnt = np.bincount(inv, minlength=G)
    tmp = np.bincount(inv, weights=d["temp"].to_numpy(float), minlength=G) / np.maximum(cnt, 1)
    dev = np.empty(G, dtype=object)
    dev[inv] = d["device"].to_numpy()
    date = np.empty(G, dtype=object)
    date[inv] = d["date"].astype(str).to_numpy()
    gi = np.nonzero(cnt >= p.fwd_min_stations)[0]
    kw = uk[gi][:, 1] * (1 << 32) + uk[gi][:, 2] + (1 << 30)               # korytarz x okno
    o = np.argsort(kw, kind="stable")
    gi, kw = gi[o], kw[o]
    bounds = np.concatenate([[0], np.nonzero(np.diff(kw))[0] + 1, [len(kw)]])
    dl, sp = [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < 2:
            continue
        grp = gi[a:b]
        for x in range(len(grp)):
            for y in range(x + 1, len(grp)):
                i, j = grp[x], grp[y]
                if uk[i, 0] == uk[j, 0] or dev[i] != dev[j] or abs(tmp[i] - tmp[j]) >= p.fwd_max_dtemp_c:
                    continue
                first, second = (i, j) if (date[i], uk[i, 0]) <= (date[j], uk[j, 0]) else (j, i)
                dl.append(med[second] - med[first])
                sp.append(min(uk[i, 0], uk[j, 0]) * 100000 + max(uk[i, 0], uk[j, 0]))
    if not dl:
        return dict(empty, n_windows=int(len(gi)))
    r = sigma_decomp(np.array(dl), np.array(sp), p.mu_min_n)
    return dict(sigma_within=r["sigma_within_mad"], sigma_total=r["sigma_total_mad"], n_pairs=len(dl),
                n_session_pairs=r["n_pairs"], n_windows=int(len(gi)), mu_sd=r["mu_sd"])


def lambda_from_sigmas(sigma_fwd: float, sigma_tsd: float) -> float:
    return sigma_fwd ** 2 / sigma_tsd ** 2 if (np.isfinite(sigma_fwd) and np.isfinite(sigma_tsd) and sigma_tsd > 0) else float("nan")


def estimate_lambda(pass_rows: dict, pass_dates: dict, pass_corridor: dict, fwd: pd.DataFrame, p: LambdaParams | None = None) -> dict:
    """lambda d0 = sigma_FWD^2 / sigma_TSD^2 z powtorzen: przejazdy TSD (`tsd_repeat_sigma`) i stacje FWD (`fwd_repeat_sigma`)."""
    p = p or LambdaParams()
    tsd = tsd_repeat_sigma(tsd_bin_table(pass_rows, pass_dates, pass_corridor, p), p)
    fw = fwd_repeat_sigma(fwd, p)
    return dict(lambda_d0=lambda_from_sigmas(fw["sigma_within"], tsd["sigma"]), sigma_tsd=tsd["sigma"], sigma_fwd=fw["sigma_within"],
                n_pairs_tsd=tsd["n_pairs"], n_pairs_fwd=fw["n_pairs"], n_session_pairs_fwd=fw["n_session_pairs"],
                median_diff_log_tsd=tsd["median_diff_log"], tsd=tsd, fwd=fw, scale_m=p.bin_m)
