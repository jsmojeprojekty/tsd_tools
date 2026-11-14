"""N4 tryb `geometry`: geometria — uklad EPSG:2180, korytarze (os referencyjna pasa) i rzut punktow na korytarz.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e1_sref.py (to_2180, convergence_deg, shift_along, group_median, runs_of, split_segments,
Corridor, project_on, best_projection, try_extend, build_corridors, refine_geometry, classify_unassigned, assign_task,
gather_by_corridor, pass_groups) oraz bak\\e0b_t20_defl.py (heading_of, angdiff, corrected_xy), stan d89080a / 2026-10-18.
Przerobione: bez multiprocessing, bez zapisu do baz i bez globalnego loggera; progi w dataclass `AxisParams`.
Scalanie duplikatow pasa (parallel_close, find_merges, apply_merges; wpis 37 decyzja p. 2) jest w tym module; wyrownanie profilem w
`align.py`. Pominiety swiadomie: drogomierz zakotwiczony w strefach zlego GPS (tsd_gps_bad_segments).

Konwencje: polozenia w EPSG:2180 jako (x = E, y = N); kurs = azymut siatki [stopnie, 0 = polnoc, zgodnie z zegarem];
`lateral_m` ze znakiem: + = w lewo od kierunku korytarza; s = dlugosc luku wzdluz osi korytarza [m]."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

# GRS80 / PUWG 1992
A_GRS80 = 6378137.0
F_GRS80 = 1.0 / 298.257222101
LON0_2180 = 19.0
K0_2180 = 0.9993
FE_2180, FN_2180 = 500000.0, -5300000.0

HEAD_HALF = 5                    # polowa okna roznicy centralnej kursu [wiersze]
TSD_OFFSET_M = -4.8              # lag polozenia ugiec TSD wzgledem GPS (konwencja E0-C), +-1,5 m
TSD_OFFSET_UNC_M = 1.5

REASONS = (None, "qc_gps_shifted", "fragment", "no_corridor", "lateral", "heading", "merged_far")


@dataclass
class AxisParams:
    """Progi budowy korytarzy (stale z e1_sref.py)."""
    lane_half_m: float = 1.75        # |lateral| <= : ten sam pas
    head_tol_deg: float = 30.0       # roznica kursu <=
    new_min_m: int = 200             # minimalna dlugosc nieprzypisanego odcinka tworzacego korytarz [wiersze ~ m]
    seg_jump_m: float = 5.0          # skok polozenia dzielacy przejazd na ciagi
    seg_head_deg: float = 60.0       # zmiana kursu oznaczajaca zawracanie
    seg_head_rows: int = 10
    seg_min_m: int = 20              # ciagi krotsze (w wierszach) odpadaja
    ext_gap_m: float = 15.0          # maks. przerwa przy przedluzaniu korytarza
    loose_m: float = 10.0            # promien klasyfikacji przyczyny nieprzypisania
    ref_smooth_m: int = 20           # wygladzenie mediany poprzecznej osi [m]
    fwd_adj_m: float = 5.0           # pas sasiedni dla stacji FWD
    pass_gap_rows: int = 50          # przerwa dzielaca przejscia
    pass_back_m: float = 5.0         # cofniecie s dzielace przejscia
    merge_max_len_m: float = 2000.0  # scalanie duplikatow pasa: rozwiazywane sa tylko korytarze krotsze
    merge_min_share: float = 0.5     # udzial dlugosci <= parallel_close_m od dluzszego korytarza tego samego kierunku
    parallel_close_m: float = 2.5    # rozstaw osi uznawany za duplikat pasa (zgodny kurs)

    @property
    def merge_wide_m(self) -> float:
        """Maks. odleglosc punktu rozwiazanego korytarza od osi celu (lane_half + parallel_close)."""
        return self.lane_half_m + self.parallel_close_m


DEFAULT_AXIS = AxisParams()


# ---------------------------------------------------------------------------
# Uklad EPSG:2180
# ---------------------------------------------------------------------------

def to_2180(lat, lon):
    """(lat, lon) GRS80 [stopnie] -> (E, N) w EPSG:2180 [m]: odwzorowanie poprzeczne Mercatora, szereg Krugera do n^4
    (dokladnosc ponizej mm w pasie Polski). Kolejnosc (E, N) = (x, y) matematyczna (w geodezji PUWG X = N, Y = E)."""
    lat = np.radians(np.asarray(lat, float))
    dl = np.radians(np.asarray(lon, float) - LON0_2180)
    f, a = F_GRS80, A_GRS80
    n = f / (2 - f)
    A = a / (1 + n) * (1 + n ** 2 / 4 + n ** 4 / 64)
    alpha = (n / 2 - 2 * n ** 2 / 3 + 5 * n ** 3 / 16 + 41 * n ** 4 / 180,
             13 * n ** 2 / 48 - 3 * n ** 3 / 5 + 557 * n ** 4 / 1440,
             61 * n ** 3 / 240 - 103 * n ** 4 / 140,
             49561 * n ** 4 / 161280)
    e = np.sqrt(f * (2 - f))
    with np.errstate(invalid="ignore"):
        t = np.sinh(np.arctanh(np.sin(lat)) - e * np.arctanh(e * np.sin(lat)))
        xi = np.arctan2(t, np.cos(dl))
        eta = np.arctanh(np.sin(dl) / np.sqrt(1 + t * t))
    E, N = eta.copy(), xi.copy()
    for j, aj in enumerate(alpha, 1):
        E = E + aj * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
        N = N + aj * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
    return FE_2180 + K0_2180 * A * E, FN_2180 + K0_2180 * A * N


def convergence_deg(lat, lon):
    """Zbieznosc poludnikow EPSG:2180 [stopnie] (1. rzad): azymut siatki = azymut geograficzny - gamma."""
    return np.degrees(np.radians(np.asarray(lon, float) - LON0_2180) * np.sin(np.radians(np.asarray(lat, float))))


def shift_along(lat, lon, hd_deg, dist_m):
    """Punkt przesuniety o dist_m wzdluz azymutu geograficznego hd_deg (lokalne promienie krzywizny GRS80)."""
    lat = np.asarray(lat, float)
    e2 = F_GRS80 * (2 - F_GRS80)
    ph = np.radians(lat)
    M = A_GRS80 * (1 - e2) / (1 - e2 * np.sin(ph) ** 2) ** 1.5
    N = A_GRS80 / np.sqrt(1 - e2 * np.sin(ph) ** 2)
    h = np.radians(hd_deg)
    return (lat + np.degrees(dist_m * np.cos(h) / M),
            np.asarray(lon, float) + np.degrees(dist_m * np.sin(h) / (N * np.cos(ph))))


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def heading_of(x, y, half=HEAD_HALF):
    """Azymut [stopnie, 0 = polnoc, zgodnie z zegarem] z roznicy centralnej +-half wierszy."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    hd = np.full(n, np.nan)
    if n > 2 * half:
        dx = x[2 * half:] - x[:-2 * half]
        dy = y[2 * half:] - y[:-2 * half]
        hd[half:n - half] = np.degrees(np.arctan2(dx, dy)) % 360.0
    return hd


def angdiff(a, b):
    """Roznica katow [stopnie] w [-180, 180)."""
    return (np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0


def corrected_xy(s, x, y, lag_m):
    """Polozenie skorygowane o lag: wiersz o pikietazu s dostaje polozenie GPS z pikietazu s - lag (lag < 0 => GPS z przodu
    o |lag| m, czyli punkt pomiaru lezy o |lag| m dalej wzdluz toru niz GPS tego samego wiersza). Interpolacja liniowa po
    pikietazu; poza zakresem pliku NaN."""
    s, x, y = np.asarray(s, float), np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(s) & np.isfinite(x) & np.isfinite(y)
    q = s - lag_m
    xs = np.interp(q, s[ok], x[ok], left=np.nan, right=np.nan)
    ys = np.interp(q, s[ok], y[ok], left=np.nan, right=np.nan)
    return xs, ys


def haversine_m(lat1, lon1, lat2, lon2):
    """Odleglosc po kuli o promieniu 6371 km [m] (zrodlo: build_road_db.py, stan d89080a)."""
    import math
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Azymut poczatkowy z punktu 1 do punktu 2 [stopnie, 0 = polnoc, [0, 360)]."""
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def sequence_headings(lat, lon, min_gap_m: float = 1.0):
    """Kurs geograficzny w kazdym punkcie sekwencji (lat, lon) metoda centralnej roznicy: bearing miedzy poprzednim a nastepnym
    sasiadem; sasiad blizszy niz min_gap_m jest pomijany (szum GPS, postoj); na brzegach roznica jednostronna. NaN, gdy punkt nie ma
    sensownego sasiada (zrodlo: build_road_db.compute_headings — kurs stacji FWD liczony z KOLEJNOSCI stacji w sesji)."""
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    n = len(lat)
    hs = np.full(n, np.nan)
    if n < 2:
        return hs
    valid = np.isfinite(lat) & np.isfinite(lon)

    def _next(i, step):
        j = i + step
        while 0 <= j < n:
            if valid[i] and valid[j] and haversine_m(lat[i], lon[i], lat[j], lon[j]) >= min_gap_m:
                return j
            j += step
        return None

    for i in range(n):
        if not valid[i]:
            continue
        pi, ni = _next(i, -1), _next(i, +1)
        if pi is not None and ni is not None:
            a, b = pi, ni
        elif ni is not None:
            a, b = i, ni
        elif pi is not None:
            a, b = pi, i
        else:
            continue
        hs[i] = bearing_deg(lat[a], lon[a], lat[b], lon[b])
    return hs


def robust_sd(x):
    """1,4826 * MAD (NaN pomijane)."""
    x = np.asarray([v for v in np.asarray(x, float).ravel() if v is not None and np.isfinite(v)], float)
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else float("nan")


def group_median(gid, vals, G):
    """Mediana w grupach (gid 0..G-1), NaN pomijane; zwraca (mediana, liczba wartosci)."""
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


def runs_of(mask):
    """Ciagi True w masce: lista (i_od, i_do) wlacznie."""
    m = np.concatenate([[0], np.asarray(mask).astype(np.int8), [0]])
    d = np.diff(m)
    return [(int(a), int(b)) for a, b in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1)]


def fill_edges(h):
    """Kurs na brzegach ciagu: najblizsza wartosc skonczona (zmienia tablice w miejscu)."""
    f = np.isfinite(h)
    if f.any() and not f.all():
        idx = np.arange(len(h))
        h[~f] = h[f][np.clip(np.searchsorted(idx[f], idx[~f]), 0, f.sum() - 1)]
    return h


def split_segments(xc, yc, p: AxisParams = DEFAULT_AXIS):
    """Podzial przejazdu na ciagi: przerwa przy braku polozenia albo skoku > seg_jump_m miedzy kolejnymi wierszami; w kawalkach
    bez skokow dodatkowo usuwane wiersze strefy zawracania (zmiana kursu > seg_head_deg na seg_head_rows wierszach).
    Zwraca liste (i_od, i_do) wlacznie; ciagi krotsze niz seg_min_m wierszy pomijane."""
    n = len(xc)
    ok = np.isfinite(xc) & np.isfinite(yc)
    brk = np.zeros(n, dtype=bool)                 # brk[i]: przerwa miedzy wierszem i - 1 a i
    if n > 1:
        with np.errstate(invalid="ignore"):
            brk[1:] = ~(np.hypot(np.diff(xc), np.diff(yc)) <= p.seg_jump_m)
    pieces = []
    for a, b in runs_of(ok):
        cut = [a] + (np.nonzero(brk[a + 1:b + 1])[0] + a + 1).tolist() + [b + 1]
        pieces += [(cut[k], cut[k + 1] - 1) for k in range(len(cut) - 1)]
    h = p.seg_head_rows
    segs = []
    for a, b in pieces:
        m = b - a + 1
        bad = np.zeros(m, dtype=bool)             # wiersze strefy zawracania
        if m > h:
            hd = heading_of(xc[a:b + 1], yc[a:b + 1])
            with np.errstate(invalid="ignore"):
                dh = np.abs(angdiff(hd[h:], hd[:-h]))
            bad[np.nonzero(dh > p.seg_head_deg)[0] + h // 2] = True
        for ra, rb in runs_of(~bad):
            if rb - ra + 1 >= p.seg_min_m:
                segs.append((a + ra, a + rb))
    return segs


# ---------------------------------------------------------------------------
# Korytarze
# ---------------------------------------------------------------------------

class Corridor:
    """Korytarz: lamana (x, y) co ~1 m, pikietaz luku s, kurs hd (azymut siatki), drzewo KD, obwiednia."""

    def __init__(self, cid, x, y, src=()):
        self.cid = cid
        self.src = list(src)
        self.set_geom(x, y)

    def set_geom(self, x, y, hd=None):
        ok = np.isfinite(x) & np.isfinite(y)
        self.x, self.y = np.asarray(x, float)[ok], np.asarray(y, float)[ok]
        d = np.hypot(np.diff(self.x), np.diff(self.y))
        self.s = np.concatenate([[0.0], np.cumsum(d)])
        h = heading_of(self.x, self.y) if hd is None else np.asarray(hd, float)[ok]
        self.hd = fill_edges(np.array(h, float))
        self.tree = cKDTree(np.column_stack([self.x, self.y]))
        self.bbox = (self.x.min(), self.y.min(), self.x.max(), self.y.max())
        self.length = float(self.s[-1])

    def near(self, bb, margin=DEFAULT_AXIS.loose_m):
        return not (bb[0] > self.bbox[2] + margin or bb[2] < self.bbox[0] - margin or
                    bb[1] > self.bbox[3] + margin or bb[3] < self.bbox[1] - margin)

    def end_dir(self, which):
        """Punkt koncowy i kierunek (wektor jednostkowy) na koncu ('end') albo poczatku ('start')."""
        k = min(10, len(self.x) - 1)
        if which == "end":
            p, q = np.array([self.x[-1 - k], self.y[-1 - k]]), np.array([self.x[-1], self.y[-1]])
            base = q
        else:
            p, q = np.array([self.x[0], self.y[0]]), np.array([self.x[k], self.y[k]])
            base = p
        d = q - p
        nd = np.hypot(*d)
        return base, (d / nd if nd > 0 else np.array([0.0, 1.0]))


def project_on(c: Corridor, px, py, phd, max_lat, heading=True, p: AxisParams = DEFAULT_AXIS):
    """Rzut punktow na korytarz c (drzewo KD zbudowane raz): najblizszy wierzcholek + rzut na 2 sasiednie odcinki.
    Zwraca (s, lateral, dh, ok): lateral ze znakiem (+ = w lewo), dh = roznica kursu [stopnie], ok = stopa na odcinku,
    |lateral| <= max_lat i (gdy heading) |dh| <= head_tol_deg."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    n = len(px)
    s_out = np.full(n, np.nan)
    lat_out = np.full(n, np.nan)
    dh_out = np.full(n, np.nan)
    ok_out = np.zeros(n, dtype=bool)
    mg = max_lat + 25.0
    with np.errstate(invalid="ignore"):
        qv = (np.isfinite(px) & np.isfinite(py) & (px >= c.bbox[0] - mg) & (px <= c.bbox[2] + mg) &
              (py >= c.bbox[1] - mg) & (py <= c.bbox[3] + mg))
    if not qv.any() or len(c.x) < 2:
        return s_out, lat_out, dh_out, ok_out
    qi = np.nonzero(qv)[0]
    _, k = c.tree.query(np.column_stack([px[qi], py[qi]]), distance_upper_bound=mg)
    found = k < len(c.x)
    qi, k = qi[found], k[found]
    if len(qi) == 0:
        return s_out, lat_out, dh_out, ok_out
    nt = len(c.x)
    best_d = np.full(len(qi), np.inf)
    best_s = np.full(len(qi), np.nan)
    best_lat = np.full(len(qi), np.nan)
    for a_off in (-1, 0):
        a = np.clip(k + a_off, 0, nt - 2)
        b = a + 1
        ax, ay, vx, vy = c.x[a], c.y[a], c.x[b] - c.x[a], c.y[b] - c.y[a]
        L2 = vx * vx + vy * vy
        px_, py_ = px[qi] - ax, py[qi] - ay
        with np.errstate(invalid="ignore", divide="ignore"):
            t = (px_ * vx + py_ * vy) / L2
            inside = (t >= -1e-6) & (t <= 1 + 1e-6) & (L2 > 1e-12)
            tc = np.clip(t, 0, 1)
            dd = np.hypot(px_ - tc * vx, py_ - tc * vy)
            lat = (vx * py_ - vy * px_) / np.sqrt(L2)
        cand = inside & (dd < best_d)
        best_d = np.where(cand, dd, best_d)
        best_s = np.where(cand, c.s[a] + tc * (c.s[b] - c.s[a]), best_s)
        best_lat = np.where(cand, lat, best_lat)
    dh = angdiff(phd[qi], c.hd[k]) if phd is not None else np.zeros(len(qi))
    ok = np.isfinite(best_s) & (np.abs(best_lat) <= max_lat)
    if heading and phd is not None:
        ok &= np.isfinite(dh) & (np.abs(dh) <= p.head_tol_deg)
    s_out[qi], lat_out[qi], dh_out[qi], ok_out[qi] = best_s, best_lat, dh, ok
    return s_out, lat_out, dh_out, ok_out


def bbox_of(x, y):
    return (np.nanmin(x), np.nanmin(y), np.nanmax(x), np.nanmax(y))


def best_projection(corrs, px, py, phd, max_lat, heading=True, p: AxisParams = DEFAULT_AXIS):
    """Najblizszy korytarz spelniajacy warunki: (cid, s, lateral); cid = -1, gdy brak."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    n = len(px)
    cid = np.full(n, -1, dtype=np.int32)
    s_out = np.full(n, np.nan)
    lat_out = np.full(n, np.nan)
    if n == 0 or not np.isfinite(px).any():
        return cid, s_out, lat_out
    best = np.full(n, np.inf)
    bb = bbox_of(px, py)
    for c in corrs:
        if not c.near(bb):
            continue
        s, lat, dh, ok = project_on(c, px, py, phd, max_lat, heading, p)
        better = ok & (np.abs(lat) < best)
        cid[better] = c.cid
        s_out[better] = s[better]
        lat_out[better] = lat[better]
        best[better] = np.abs(lat[better])
    return cid, s_out, lat_out


def try_extend(corrs, sx, sy, p: AxisParams = DEFAULT_AXIS):
    """Czy odcinek (sx, sy) przedluza korytarz: poczatek odcinka przy koncu korytarza albo koniec odcinka przy poczatku
    korytarza (<= ext_gap_m wzdluz, <= lane_half_m poprzecznie, kierunek zgodny <= head_tol_deg).
    Zwraca (korytarz, 'append' / 'prepend') albo (None, None)."""
    p0, p1 = np.array([sx[0], sy[0]]), np.array([sx[-1], sy[-1]])
    k = min(10, len(sx) - 1)
    d0 = np.array([sx[k] - sx[0], sy[k] - sy[0]])
    d1 = np.array([sx[-1] - sx[-1 - k], sy[-1] - sy[-1 - k]])
    cmin = np.cos(np.radians(p.head_tol_deg))
    for c in corrs:
        if len(c.x) < 3:
            continue
        for which, pt, dseg in (("end", p0, d0), ("start", p1, d1)):
            base, dc = c.end_dir(which)
            v = pt - base
            along = v @ dc
            lat = dc[0] * v[1] - dc[1] * v[0]
            ok_along = (0 <= along <= p.ext_gap_m) if which == "end" else (-p.ext_gap_m <= along <= 0)
            nd = np.hypot(*dseg)
            if ok_along and abs(lat) <= p.lane_half_m and nd > 0 and (dseg @ dc) / nd >= cmin:
                return c, ("append" if which == "end" else "prepend")
    return None, None


def build_corridors(runs: dict, p: AxisParams = DEFAULT_AXIS):
    """Budowa zachlanna korytarzy na ciagach sortowanych malejaco wg dlugosci. runs: {run_id: dict(xc, yc, hd, segs)}."""
    segs = []
    for fid, d in runs.items():
        for k, (a, b) in enumerate(d["segs"]):
            segs.append((b - a + 1, fid, k, a, b))
    segs.sort(key=lambda t: (-t[0], t[1], t[2]))      # run_id jednego typu (liczby albo napisy), jak file_id w zrodle
    corrs = []
    n_new = n_ext = 0
    for length, fid, k, a, b in segs:
        d = runs[fid]
        px, py, phd = d["xc"][a:b + 1], d["yc"][a:b + 1], d["hd"][a:b + 1]
        cid, _, _ = best_projection(corrs, px, py, phd, p.lane_half_m, True, p)
        for ra, rb in runs_of(cid < 0):
            if rb - ra + 1 < p.new_min_m:
                continue
            sx, sy = px[ra:rb + 1], py[ra:rb + 1]
            c, how = try_extend(corrs, sx, sy, p)
            if c is not None:
                if how == "append":
                    c.set_geom(np.concatenate([c.x, sx]), np.concatenate([c.y, sy]))
                else:
                    c.set_geom(np.concatenate([sx, c.x]), np.concatenate([sy, c.y]))
                c.src.append((fid, k, a + ra, a + rb, how))
                n_ext += 1
            else:
                corrs.append(Corridor(len(corrs), sx, sy, [(fid, k, a + ra, a + rb, "new")]))
                n_new += 1
    return corrs, dict(n_segments=len(segs), n_new=n_new, n_ext=n_ext)


def refine_geometry(c: Corridor, pts_s, pts_lat, p: AxisParams = DEFAULT_AXIS):
    """Linia referencyjna: os tymczasowa c + mediana poprzeczna punktow w binach 1 m (luki interpolowane), wygladzona srednia
    centralna ref_smooth_m, przeprobkowana co 1 m. Zwraca (x, y, |poprawka| maks., mediana |poprawki|)."""
    nb = int(np.floor(c.length)) + 1
    med = np.full(nb, np.nan)
    ok = np.isfinite(pts_s) & np.isfinite(pts_lat)
    if ok.any():
        b = np.clip(np.floor(pts_s[ok]).astype(np.int64), 0, nb - 1)
        med = group_median(b, pts_lat[ok], nb)[0]
    f = np.isfinite(med)
    idx = np.arange(nb)
    med = np.interp(idx, idx[f], med[f]) if f.sum() >= 2 else np.zeros(nb)
    h = p.ref_smooth_m // 2
    pad = np.concatenate([np.full(h, med[0]), med, np.full(h, med[-1])])
    sm = np.convolve(pad, np.ones(2 * h + 1) / (2 * h + 1), mode="valid")
    off = np.interp(c.s, idx, sm)
    hr = np.radians(c.hd)
    x2, y2 = c.x - off * np.cos(hr), c.y + off * np.sin(hr)     # normalna w lewo od (sin h, cos h)
    d = np.hypot(np.diff(x2), np.diff(y2))
    s2 = np.concatenate([[0.0], np.cumsum(d)])
    grid = np.arange(0.0, s2[-1] + 1e-9, 1.0)
    return np.interp(grid, s2, x2), np.interp(grid, s2, y2), float(np.abs(sm).max()), float(np.median(np.abs(sm)))


def classify_unassigned(corrs, px, py, p: AxisParams = DEFAULT_AXIS):
    """Kod przyczyny braku przypisania (indeks w REASONS): 3 no_corridor - brak korytarza <= loose_m; 5 heading - korytarz
    <= lane_half_m, ale kurs > head_tol_deg; 4 lateral - najblizszy korytarz w (lane_half_m, loose_m]."""
    best = np.full(len(px), np.inf)
    bb = bbox_of(px, py)
    for c in corrs:
        if c.near(bb):
            _, lat, _, ok = project_on(c, px, py, None, p.loose_m, heading=False, p=p)
            upd = ok & (np.abs(lat) < best)
            best[upd] = np.abs(lat[upd])
    return np.where(~np.isfinite(best), 3, np.where(best <= p.lane_half_m, 5, 4)).astype(np.int8)


def assign_run(corrs, d: dict, classify: bool = False, p: AxisParams = DEFAULT_AXIS):
    """Przypisanie punktow ciagow jednego przejazdu do korytarzy. Zwraca (cid, s, lateral, reason_code)."""
    xc, yc, hd, segs = d["xc"], d["yc"], d["hd"], d["segs"]
    n = len(xc)
    cid = np.full(n, -1, dtype=np.int32)
    s = np.full(n, np.nan)
    lat = np.full(n, np.nan)
    rc = np.full(n, 2, dtype=np.int8)                # poza ciagami: fragment
    for a, b in segs:
        sl = slice(a, b + 1)
        ci, si, li = best_projection(corrs, xc[sl], yc[sl], hd[sl], p.lane_half_m, True, p)
        cid[sl], s[sl], lat[sl] = ci, si, li
        r = np.zeros(b - a + 1, dtype=np.int8)
        m = ci < 0
        if classify and m.any():
            r[m] = classify_unassigned(corrs, xc[sl][m], yc[sl][m], p)
        rc[sl] = r
    return cid, s, lat, rc


def gather_by_corridor(assigned: dict, G: int):
    """Punkty przypisane pogrupowane wg korytarza: lista (s, lateral) dla korytarzy 0..G-1."""
    keys = sorted(assigned)
    cid = np.concatenate([assigned[f][0] for f in keys]) if keys else np.zeros(0, dtype=np.int32)
    s = np.concatenate([assigned[f][1] for f in keys]) if keys else np.zeros(0)
    lat = np.concatenate([assigned[f][2] for f in keys]) if keys else np.zeros(0)
    m = cid >= 0
    cid, s, lat = cid[m], s[m], lat[m]
    o = np.argsort(cid, kind="stable")
    cid, s, lat = cid[o], s[o], lat[o]
    b = np.searchsorted(cid, np.arange(G + 1))
    return [(s[b[g]:b[g + 1]], lat[b[g]:b[g + 1]]) for g in range(G)]


def pass_groups(cid, s, p: AxisParams = DEFAULT_AXIS):
    """Przejscia pliku przez korytarze: lista (korytarz, indeksy wierszy). Nowe przejscie przy przerwie > pass_gap_rows wierszy
    (krotsze wtracenia innego korytarza nie dziela przejscia) albo cofnieciu s > pass_back_m."""
    out = []
    for c in np.unique(cid[cid >= 0]):
        idx = np.nonzero(cid == c)[0]
        brk = (np.diff(idx) > p.pass_gap_rows) | (np.diff(s[idx]) < -p.pass_back_m)
        out += [(int(c), g) for g in np.split(idx, np.nonzero(brk)[0] + 1)]
    out.sort(key=lambda t: t[1][0])
    return out


# ---------------------------------------------------------------------------
# Scalanie duplikatow pasa
# ---------------------------------------------------------------------------

def parallel_close(corrs, p: AxisParams = DEFAULT_AXIS):
    """Udzial punktow korytarza <= parallel_close_m od innego korytarza o zgodnym kursie (podejrzenie duplikatu pasa)."""
    out = {}
    for c in corrs:
        close = np.zeros(len(c.x), dtype=bool)
        for o in corrs:
            if o.cid != c.cid and o.near(c.bbox, p.parallel_close_m + 1):
                close |= project_on(o, c.x, c.y, c.hd, p.parallel_close_m, heading=True, p=p)[3]
        out[c.cid] = float(close.mean())
    return out


def find_merges(corrs, p: AxisParams = DEFAULT_AXIS):
    """Regula scalania duplikatow pasa: korytarz krotszy niz merge_max_len_m, ktory na >= merge_min_share dlugosci lezy <= parallel_close_m od
    dluzszego, nierozwiazanego korytarza tego samego kierunku (kurs <= head_tol_deg), zostaje rozwiazany do korytarza o najwiekszym udziale
    bliskosci. Kandydaci przegladani od najdluzszego, wiec status dluzszych jest juz ostateczny, a lancuchy duplikatow trafiaja do korytarza
    glownego. Zwraca liste slownikow (dissolved_id, target_id, length_m, close_share, sep_med_m)."""
    by_len = sorted(corrs, key=lambda c: (-c.length, c.cid))
    dissolved, out = set(), []
    for c in by_len:
        if c.length >= p.merge_max_len_m:
            continue
        best = None
        for o in by_len:
            if o.length <= c.length:
                break
            if o.cid in dissolved or not o.near(c.bbox, p.parallel_close_m + 1):
                continue
            _, lat, _, ok = project_on(o, c.x, c.y, c.hd, p.parallel_close_m, heading=True, p=p)
            share = float(ok.mean())
            if share >= p.merge_min_share and (best is None or share > best[1]):
                best = (o.cid, share, float(np.median(np.abs(lat[ok]))))
        if best is not None:
            dissolved.add(c.cid)
            out.append(dict(dissolved_id=c.cid, target_id=best[0], length_m=float(c.length), close_share=best[1], sep_med_m=best[2]))
    return out


def apply_merges(runs: dict, corrs, assigned: dict, merges, p: AxisParams = DEFAULT_AXIS):
    """Punkty rozwiazanych korytarzy -> korytarz docelowy (rzut na jego geometrie, <= merge_wide_m, kurs <= head_tol_deg), znacznik `wide`;
    punkty, ktorych nie da sie rzutowac, zostaja nieprzypisane z przyczyna 'merged_far'. assigned: {run_id: (cid, s, lateral, reason)};
    zwraca (assigned zmienione w miejscu, wide {run_id: maska bool}, liczba przeniesionych per korytarz, liczba merged_far per korytarz)."""
    by_id = {c.cid: c for c in corrs}
    tgt = {m["dissolved_id"]: m["target_id"] for m in merges}
    moved, far = {}, {}
    code_far = REASONS.index("merged_far")
    wide = {}
    for rid, d in runs.items():
        cid, s, lat, rc = assigned[rid]
        w = np.zeros(len(cid), dtype=bool)
        for k in np.unique(cid[cid >= 0]):
            k = int(k)
            if k not in tgt:
                continue
            idx = np.nonzero(cid == k)[0]
            t = by_id[tgt[k]]
            s2, lat2, _, ok = project_on(t, d["xc"][idx], d["yc"][idx], d["hd"][idx], p.merge_wide_m, heading=True, p=p)
            i_ok, i_far = idx[ok], idx[~ok]
            cid[i_ok], s[i_ok], lat[i_ok], w[i_ok] = t.cid, s2[ok], lat2[ok], True
            cid[i_far], s[i_far], lat[i_far], rc[i_far] = -1, np.nan, np.nan, code_far
            moved[k] = moved.get(k, 0) + len(i_ok)
            far[k] = far.get(k, 0) + len(i_far)
        wide[rid] = w
    return assigned, wide, moved, far


# ---------------------------------------------------------------------------
# Przejazd TSD -> ciagi
# ---------------------------------------------------------------------------

def prepare_run(chainage_m, lat, lon, lag_m: float = TSD_OFFSET_M, p: AxisParams = DEFAULT_AXIS) -> dict:
    """Przejazd TSD: polozenie EPSG:2180 skorygowane o lag, ciagi i kurs ciagow (jak `load_geometry` w e1_sref.py, bez bazy).
    chainage_m rosnacy z jazda; wiersze bez wspolrzednych (lat/lon = NaN lub |lat| <= 1) bez polozenia."""
    s = np.asarray(chainage_m, float)
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    n = len(s)
    ok = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) > 1)
    x, y = to_2180(np.where(ok, lat, np.nan), np.where(ok, lon, np.nan))
    if (np.isfinite(s) & np.isfinite(x) & np.isfinite(y)).sum() >= 2:
        xc, yc = corrected_xy(s, x, y, lag_m)
    else:
        xc, yc = np.full(n, np.nan), np.full(n, np.nan)
    segs = split_segments(xc, yc, p)
    seg_id = np.full(n, -1, dtype=np.int32)
    hd = np.full(n, np.nan)
    for k, (a, b) in enumerate(segs):
        seg_id[a:b + 1] = k
        hd[a:b + 1] = fill_edges(heading_of(xc[a:b + 1], yc[a:b + 1]))
    return dict(s=s, xc=xc, yc=yc, hd=hd, seg_id=seg_id, segs=segs)


def build_axis(runs: dict, p: AxisParams = DEFAULT_AXIS, merge: bool = False):
    """Os referencyjna z przejazdow (GPS): budowa korytarzy, jedna iteracja wygladzenia osi i ponowne rzutowanie wszystkich przejazdow;
    przy merge=True dodatkowo scalanie duplikatow pasa (rozwiazane korytarze znikaja z listy, ich punkty trafiaja do celu jako `wide`).
    Zwraca (korytarze zywe, przypisania {run_id: (cid, s_ref_gps, lateral, reason)}, info); info['wide'] = {run_id: maska}, info['merges'] = lista."""
    corrs, info = build_corridors(runs, p)
    assigned0 = {fid: assign_run(corrs, d, False, p) for fid, d in runs.items()}
    grp = gather_by_corridor(assigned0, len(corrs))
    for c in corrs:
        x2, y2, fmax, fmed = refine_geometry(c, *grp[c.cid], p=p)
        c.fix = (fmax, fmed)
        c.set_geom(x2, y2)
    assigned = {fid: assign_run(corrs, d, True, p) for fid, d in runs.items()}
    info["n_corridors"] = len(corrs)
    info["wide"] = {rid: np.zeros(len(a[0]), dtype=bool) for rid, a in assigned.items()}
    info["merges"] = []
    if merge:
        merges = find_merges(corrs, p)
        assigned, wide, moved, far = apply_merges(runs, corrs, assigned, merges, p)
        dissolved = {m["dissolved_id"] for m in merges}
        for m in merges:
            m.update(n_points_wide=moved.get(m["dissolved_id"], 0), n_points_far=far.get(m["dissolved_id"], 0))
        corrs = [c for c in corrs if c.cid not in dissolved]
        info.update(wide=wide, merges=merges, n_corridors=len(corrs), n_dissolved=len(dissolved))
    return corrs, assigned, info
