"""N4 tryb `geometry`: wyrownanie przejazdow TSD w obrebie korytarza profilem podluznym (s_ref = s_ref_gps + delta(s)).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e1_sref.py (overlap_blocks, block_lag, align_blocks, delta_fn, loo_residuals, align_corridor,
krok 2 przebiegu: delta, centrowanie, zrodlo wyrownania), bak\\e0b_t20_defl.py (block_curve, curve_peak, running_median_nan, resample),
bak\\e0_t20_lag.py (parabola_peak), bak\\qc_gyro_gps.py (xcorr_pearson, _xc); stan d89080a / 2026-10-18.

Metoda: sygnal = profil podluzny minus mediana biegnaca 101 m (siatka 1 m). Przejscia korytarza wyrownywane do najdluzszego (odniesienie):
bloki ~1000 m, przesuniecie z maksimum korelacji Pearsona w zakresie +-15 m (parabola, srednia z wariantem polprobkowym), blok uznany przy
r >= 0,8; bloki odstajace > 3 m od mediany przejscia odrzucane; delta(s) odcinkowo-liniowa przez srodki blokow (stala poza nimi). Przejscia bez
wspolnych blokow z odniesieniem wyrownywane do szablonu (srednia przejsc wyrownanych, 2 rundy). Na korytarz odejmowana jest mediana delta
przejsc wyrownanych (rama = mediana GPS przejsc, zgodna z rama GPS stacji FWD). Przejscie bez wyrownania zostaje na s_ref_gps
(`align_source = 'gps'`; przyczyna: no_profile / short / no_block_r08).
Wymaga kanalu profilu podluznego (eksport B_1510off go nie zawiera)."""

from __future__ import annotations

import numpy as np

DETREND_W = 101            # okno mediany biegnacej profilu [wiersze = m]
RESAMPLE_GAP = 3.0         # maks. przerwa miedzy probkami przy interpolacji na siatke 1 m [m]
ALIGN_BLOCK_M = 1000
ALIGN_LMAX = 15
ALIGN_R_MIN = 0.8
ALIGN_MIN_PAIRS = 500
ALIGN_OUTLIER_M = 3.0
TEMPLATE_ROUNDS = 2


def _xc(u, v, nfft, n_u, n_v):
    """c[L] = sum_i u[i] * v[i+L] dla L = -(n_u-1) .. (n_v-1)."""
    c = np.fft.irfft(np.conj(np.fft.rfft(u, nfft)) * np.fft.rfft(v, nfft), nfft)
    return np.concatenate([c[nfft - (n_u - 1):], c[:n_v]]) if n_u > 1 else c[:n_v]


def xcorr_pearson(a, b):
    """Dokladny wspolczynnik Pearsona r(L) = corr(a[i], b[i+L]) dla wszystkich przesuniec (FFT; srednie i wariancje na wspolnych,
    niepustych wierszach). Zwraca (lags, r, n_pairs)."""
    ma, mb = np.isfinite(a), np.isfinite(b)
    a0 = np.where(ma, a - np.nanmean(a), 0.0)
    b0 = np.where(mb, b - np.nanmean(b), 0.0)
    fa, fb = ma.astype(float), mb.astype(float)
    n_a, n_b = len(a), len(b)
    nfft = 1 << (n_a + n_b - 1).bit_length()
    N = np.rint(_xc(fa, fb, nfft, n_a, n_b))
    Sa = _xc(a0, fb, nfft, n_a, n_b)
    Sb = _xc(fa, b0, nfft, n_a, n_b)
    Saa = _xc(a0 * a0, fb, nfft, n_a, n_b)
    Sbb = _xc(fa, b0 * b0, nfft, n_a, n_b)
    Sab = _xc(a0, b0, nfft, n_a, n_b)
    with np.errstate(invalid="ignore", divide="ignore"):
        den = np.sqrt(np.clip(N * Saa - Sa * Sa, 0, None) * np.clip(N * Sbb - Sb * Sb, 0, None))
        r = np.where(den > 0, (N * Sab - Sa * Sb) / den, np.nan)
    lags = np.arange(-(n_a - 1), n_b)
    return lags, r, N


def parabola_peak(r, k):
    """Wierzcholek paraboli przez (k-1, k, k+1): (przesuniecie delta, r w wierzcholku, krzywizna)."""
    y0, y1, y2 = r[k - 1], r[k], r[k + 1]
    den = y0 - 2 * y1 + y2
    if not (den < 0):
        return 0.0, float(y1), float(den)
    d = 0.5 * (y0 - y2) / den
    return float(d), float(y1 - 0.25 * (y0 - y2) * d), float(den)


def block_curve(x, y, b0, b1, lmax=ALIGN_LMAX, min_pairs=250):
    """Krzywa r(L) = corr(y[i + L], x[i]) dla i w bloku [b0, b1) i L w [-lmax, lmax] (y z calego ciagu, stala nakladka).
    Zwraca (r, n par przy L = 0)."""
    n = len(x)
    a = x[b0:b1]
    lo, hi = b0 - lmax, b1 + lmax
    bb = np.full(hi - lo, np.nan)
    s0, s1 = max(lo, 0), min(hi, n)
    bb[s0 - lo:s1 - lo] = y[s0:s1]
    lags, r, npairs = xcorr_pearson(a, bb)
    sel = (lags >= 0) & (lags <= 2 * lmax)
    r, npairs = r[sel], npairs[sel]
    return np.where(npairs >= min_pairs, r, np.nan), int(npairs[lmax])


def curve_peak(r, lags):
    """Maksimum krzywej z parabola: (delta, r_peak, flaga 'ok' / 'edge' / 'nan')."""
    if not np.isfinite(r).any():
        return np.nan, np.nan, "nan"
    k = int(np.nanargmax(r))
    if k == 0 or k == len(r) - 1 or not (np.isfinite(r[k - 1]) and np.isfinite(r[k + 1])):
        return float(lags[k]), float(r[k]), "edge"
    d, rp, _ = parabola_peak(r, k)
    return float(lags[k] + d * (lags[1] - lags[0])), rp, "ok"


def running_median_nan(y, w=DETREND_W):
    """Mediana biegnaca centralna okna w (NaN pominiete; NaN, gdy w oknie < w/4 wartosci)."""
    y = np.asarray(y, float)
    n = len(y)
    h = w // 2
    if n == 0:
        return y.copy()
    yp = np.concatenate([np.full(h, np.nan), y, np.full(h, np.nan)])
    out = np.full(n, np.nan)
    step = 20000
    for a in range(0, n, step):
        b = min(n, a + step)
        win = np.lib.stride_tricks.sliding_window_view(yp[a:b + 2 * h], w)
        cnt = np.isfinite(win).sum(axis=1)
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                med = np.nanmedian(win, axis=1)
        out[a:b] = np.where(cnt >= w // 4, med, np.nan)
    return out


def detrend_profile(profile):
    """Profil minus mediana biegnaca 101 m; NaN, gdy profil pusty."""
    p = np.asarray(profile, float)
    return p - running_median_nan(p) if np.isfinite(p).any() else np.full(len(p), np.nan)


def resample(s_src, v_src, s_grid, max_gap=RESAMPLE_GAP):
    """Interpolacja liniowa v(s_src) na s_grid; NaN, gdy brak sasiadow z obu stron w odleglosci <= max_gap."""
    s_src, v_src = np.asarray(s_src, float), np.asarray(v_src, float)
    ok = np.isfinite(s_src) & np.isfinite(v_src)
    out = np.full(len(s_grid), np.nan)
    if ok.sum() < 2:
        return out
    order = np.argsort(s_src[ok])
    ss, vv = s_src[ok][order], v_src[ok][order]
    idx = np.searchsorted(ss, s_grid)
    inner = (idx > 0) & (idx < len(ss))
    ic = np.clip(idx, 1, len(ss) - 1)
    gap = ss[ic] - ss[ic - 1]
    good = inner & (gap <= max_gap)
    out[good] = np.interp(s_grid[good], ss, vv)
    return out


def overlap_blocks(both, block):
    """Bloki ~block m na zakresie wspolnych probek (maska both): lista (b0, b1); ostatni nie krotszy niz ~block/2."""
    idx = np.nonzero(both)[0]
    if len(idx) == 0:
        return []
    lo, hi = int(idx[0]), int(idx[-1]) + 1
    nb = max(1, int(round((hi - lo) / block)))
    e = np.round(np.linspace(lo, hi, nb + 1)).astype(int)
    return list(zip(e[:-1], e[1:]))


def block_lag(y_ref, y_run, y_run_h, b0, b1, min_pairs, lmax=ALIGN_LMAX):
    """Przesuniecie bloku [b0, b1): L z maksimum corr(y_ref[k + L], y_run[k]) (parabola). Gdy podany y_run_h (ten sam sygnal w polozeniach
    k + 0,5 m), wynik = srednia L i L_h - 0,5 (parabola na ostrym szczycie ciagnie wynik do calkowitego lagu; przesuniecie o pol probki
    odwraca znak obciazenia). Zwraca (L, r, flaga)."""
    lags = np.arange(-lmax, lmax + 1, dtype=float)
    r, _ = block_curve(y_run, y_ref, b0, b1, lmax=lmax, min_pairs=min_pairs)
    L, rp, fl = curve_peak(r, lags)
    if y_run_h is None or fl != "ok":
        return L, rp, fl
    rh, _ = block_curve(y_run_h, y_ref, b0, b1, lmax=lmax, min_pairs=min_pairs)
    Lh, _, flh = curve_peak(rh, lags)
    if flh != "ok" or abs(Lh - 0.5 - L) > 1.0:
        return L, rp, fl
    return 0.5 * (L + Lh - 0.5), rp, fl


def align_blocks(y_ref, y_run, y_run_h=None, block=None, min_pairs=None, r_min=None, lmax=None):
    """Bloki ~1 km na zakresie wspolnym przejscia i odniesienia (siatka 1 m). Cecha przejscia w s widoczna w odniesieniu w s + L, wiec
    s_ref(przejscie) = s_gps + L. Zwraca liste (srodek, L, r, flaga, n, uzyty)."""
    block = ALIGN_BLOCK_M if block is None else block
    min_pairs = ALIGN_MIN_PAIRS if min_pairs is None else min_pairs
    r_min = ALIGN_R_MIN if r_min is None else r_min
    lmax = ALIGN_LMAX if lmax is None else lmax
    both = np.isfinite(y_ref) & np.isfinite(y_run)
    out = []
    for b0, b1 in overlap_blocks(both, block):
        m = int(both[b0:b1].sum())
        if m < min_pairs:
            continue
        L, rp, fl = block_lag(y_ref, y_run, y_run_h, b0, b1, int(0.8 * m), lmax)
        out.append(((b0 + b1) / 2.0, float(L), float(rp) if np.isfinite(rp) else None, fl, m,
                    bool(fl == "ok" and np.isfinite(rp) and rp >= r_min)))
    return out


def delta_fn(blocks):
    """delta(s): odcinkowo-liniowa przez srodki blokow uzytych (po odrzuceniu odstajacych > 3 m od mediany). Zwraca
    ((srodki, L) albo None, liczba odrzuconych, maska uzycia wg listy blokow)."""
    used = np.array([b[5] for b in blocks], dtype=bool)
    if not used.any():
        return None, 0, used
    Ls = np.array([b[1] for b in blocks])
    med = np.median(Ls[used])
    rej = used & (np.abs(Ls - med) > ALIGN_OUTLIER_M)
    used = used & ~rej
    if not used.any():
        return None, int(rej.sum()), used
    cs = np.array([b[0] for b in blocks])[used]
    o = np.argsort(cs)
    return (cs[o], Ls[used][o]), int(rej.sum()), used


def loo_residuals(fn):
    """Walidacja krzyzowa: delta bloku przewidziana z pozostalych minus zmierzona (>= 3 bloki)."""
    if fn is None or len(fn[0]) < 3:
        return []
    cs, Ls = fn
    out = []
    for k in range(len(cs)):
        m = np.ones(len(cs), dtype=bool)
        m[k] = False
        out.append(float(np.interp(cs[k], cs[m], Ls[m]) - Ls[k]))
    return out


def align_corridor(passes, L, log_rows=None):
    """Wyrownanie przejsc jednego korytarza. passes: lista slownikow (pass_id, s (s_gps), prof = profil minus mediana 101 m). Uzupelnia w
    miejscu: y, yh, fn (delta), align_ref, n_blocks, n_ok, n_rej, loo. Zwraca centrowanie c [m] (mediana delta przejsc wyrownanych)."""
    log_rows = [] if log_rows is None else log_rows
    grid = np.arange(0.0, np.floor(L) + 1.0)
    for p in passes:
        p["y"] = resample(p["s"], p["prof"], grid)
        p["yh"] = resample(p["s"], p["prof"], grid + 0.5)
        p["fn"], p["align_ref"], p["n_blocks"], p["n_ok"], p["n_rej"], p["loo"] = None, "gps", 0, 0, 0, []
    cand = [p for p in passes if np.isfinite(p["y"]).sum() >= ALIGN_MIN_PAIRS]
    if not cand:
        return 0.0
    ref = max(cand, key=lambda p: np.isfinite(p["y"]).sum())
    ref["align_ref"] = "reference"
    ref["fn"] = (np.array([0.0]), np.array([0.0]))

    def aligned_signal(p):
        s_al = p["s"] + (np.interp(p["s"], *p["fn"]) if p["fn"] is not None else 0.0)
        return resample(s_al, p["prof"], grid)

    def attempt(p, y_ref, tag):
        bl = align_blocks(y_ref, p["y"], p["yh"])
        fn, nrej, used = delta_fn(bl)
        for (cs, Lb, rb, fl, nn, _), u in zip(bl, used):
            log_rows.append(dict(pass_id=p["pass_id"], round=tag, s_center=cs, delta_m=Lb, r=rb, flag=fl, n_pairs=nn, used=int(u)))
        p["n_blocks"] += len(bl)
        if fn is not None:
            p["fn"], p["align_ref"], p["n_ok"], p["n_rej"] = fn, tag, int(used.sum()), nrej
            p["loo"] = loo_residuals(fn)
            return True
        p["n_rej"] += nrej
        return False

    for p in cand:
        if p is not ref:
            attempt(p, ref["y"], "profile_ref")
    for _ in range(TEMPLATE_ROUNDS):
        todo = [p for p in cand if p["fn"] is None]
        if not todo:
            break
        acc = np.zeros(len(grid))
        cnt = np.zeros(len(grid))
        for p in cand:
            if p["fn"] is not None:
                y = aligned_signal(p)
                f = np.isfinite(y)
                acc[f] += y[f]
                cnt[f] += 1
        T = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
        for p in todo:
            attempt(p, T, "profile_template")
    meds = [float(np.median(p["fn"][1])) for p in cand if p["fn"] is not None]
    return float(np.median(meds)) if meds else 0.0


def apply_alignment(p: dict, centering: float):
    """Przejscie po align_corridor: delta dla wierszy (dl), zrodlo wyrownania (src) i notatka. Zwraca (s_ref, src, note)."""
    s = np.asarray(p["s"], float)
    if p["fn"] is None:
        npf = int(np.isfinite(p["prof"]).sum())
        ny = int(np.isfinite(p["y"]).sum()) if "y" in p else 0
        note = "no_profile" if npf == 0 else ("short" if ny < ALIGN_MIN_PAIRS else "no_block_r08")
        return s.copy(), np.full(len(s), "gps", dtype=object), note
    cs, Lb = p["fn"]
    dl = np.interp(s, cs, Lb) - centering
    if p["align_ref"] == "reference":
        src = np.full(len(s), "reference", dtype=object)
    else:
        inside = (s >= cs[0] - ALIGN_BLOCK_M / 2) & (s <= cs[-1] + ALIGN_BLOCK_M / 2)
        src = np.where(inside, "profile", "profile_extrap").astype(object)
    return s + dl, src, None


def synthetic_alignment(seed=20260927, length=8000, shift=2.3, drift_per_km=0.8, noise=0.3):
    """Walidacja syntetyczna: profil (bladzenie losowe minus mediana biegnaca 101 m) i przejscie z przesunieciem shift [m] i dryftem
    drift_per_km [m/km]. Zwraca bledy odtworzenia delta(s) przez align_blocks + delta_fn wewnatrz zakresu srodkow blokow i na calosci."""
    rng = np.random.default_rng(seed)
    pad = 200
    n = length + 2 * pad
    base = np.cumsum(rng.normal(size=n))
    base = base - running_median_nan(base)
    pos = np.arange(n, dtype=float) - pad
    s = np.arange(length, dtype=float)
    sd = np.nanstd(base[pad:pad + length])
    y_ref = base[pad:pad + length] + noise * sd * rng.normal(size=length)
    s_gps = s + 0.37
    s_true = s_gps + shift + drift_per_km * s_gps / 1000.0
    v_run = np.interp(s_true, pos, base) + noise * sd * rng.normal(size=length)
    y_run, y_run_h = resample(s_gps, v_run, s), resample(s_gps, v_run, s + 0.5)
    delta = shift + drift_per_km * s / 1000.0
    bl = align_blocks(y_ref, y_run, y_run_h)
    fn, nrej, used = delta_fn(bl)
    out = dict(shift=shift, drift_per_km=drift_per_km, noise=noise, n_blocks=len(bl), n_used=int(used.sum()))
    if fn is None:
        return out
    est = np.interp(s, *fn)
    inner = (s >= fn[0][0]) & (s <= fn[0][-1])
    err = est - delta
    out.update(r_med=float(np.median([b[2] for b in bl if b[2] is not None])), err_max_inner=float(np.abs(err[inner]).max()),
               err_rms_inner=float(np.sqrt(np.mean(err[inner] ** 2))), err_mean_inner=float(np.mean(err[inner])),
               err_max_all=float(np.abs(err).max()))
    return out
