"""N4 tryb `geometry`: raport przegladu odcinkow wspolnych („linia do linii”) — HTML z wykresami SVG (bez zaleznosci graficznych).

Na kazdy odcinek: (1) slad GPS przejazdu TSD i stacje FWD sesji (dopasowane zaznaczone), (2) monotonicznosc station_m -> pikietaz TSD
(regresja liniowa; to jest kryterium |Spearman| >= 0,80 z Tab. 3.2), (3) „linia do linii”: d0 TSD gestym przebiegiem po pikietazu
i D0 FWD jako punkty na tym samym pikietazu (stacje rzutowane po GPS na najblizszy punkt TSD). Wykresy sluza do RECZNEGO przegladu;
decyzja (potwierdzony / odrzucony) wraca do N4 plikiem `geometry.sections.review_csv` (kolumny session_id, run_id, status)."""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd

W, H, PAD = 300, 200, 34


def _scale(v, lo, hi, a, b):
    if hi <= lo:
        return (a + b) / 2 * np.ones_like(np.asarray(v, float))
    return a + (np.asarray(v, float) - lo) / (hi - lo) * (b - a)


def _axes(title: str, xlab: str, ylab: str, xr, yr) -> str:
    s = [f'<rect x="{PAD}" y="10" width="{W - PAD - 6}" height="{H - PAD - 10}" fill="none" stroke="#999"/>',
         f'<text x="{W / 2:.0f}" y="{H - 4}" font-size="9" text-anchor="middle">{html.escape(xlab)}</text>',
         f'<text x="8" y="{H / 2:.0f}" font-size="9" text-anchor="middle" transform="rotate(-90 8 {H / 2:.0f})">{html.escape(ylab)}</text>',
         f'<text x="{W / 2:.0f}" y="8" font-size="10" text-anchor="middle" font-weight="bold">{html.escape(title)}</text>']
    for lo, hi, horiz in ((xr[0], xr[1], True), (yr[0], yr[1], False)):
        for frac in (0.0, 1.0):
            val = lo + frac * (hi - lo)
            if horiz:
                s.append(f'<text x="{PAD + frac * (W - PAD - 6):.0f}" y="{H - PAD + 11}" font-size="8" text-anchor="middle">{val:.4g}</text>')
            else:
                s.append(f'<text x="{PAD - 3}" y="{H - PAD - frac * (H - PAD - 10) + 3:.0f}" font-size="8" text-anchor="end">{val:.4g}</text>')
    return "".join(s)


def _svg(body: str) -> str:
    return f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="background:#fff">{body}</svg>'


def _xy(x, y, xr, yr):
    px = _scale(x, xr[0], xr[1], PAD, W - 6)
    py = _scale(y, yr[0], yr[1], H - PAD, 10)
    return px, py


def _range(*arrs, margin=0.03):
    v = np.concatenate([np.asarray(a, float)[np.isfinite(a)] for a in arrs if len(a)])
    if len(v) == 0:
        return 0.0, 1.0
    lo, hi = float(v.min()), float(v.max())
    d = (hi - lo) * margin or 1.0
    return lo - d, hi + d


def _points(px, py, color, r=2.0):
    return "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r}" fill="{color}"/>' for a, b in zip(px, py))


def _line(px, py, color, width=1.0):
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(px, py))
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def trace_panel(run: pd.DataFrame, sess: pd.DataFrame, match: pd.DataFrame, lo: float, hi: float) -> str:
    """Slad GPS: TSD (linia; zakres odcinka na czerwono), stacje FWD (szare), dopasowane (zielone)."""
    from .geo import to_2180
    tx, ty = to_2180(run["lat"].to_numpy(float), run["lon"].to_numpy(float))
    sx, sy = to_2180(sess["lat"].to_numpy(float), sess["lon"].to_numpy(float))
    ok = np.isfinite(tx) & np.isfinite(ty)
    inside = ok & (run["chainage"].to_numpy(float) >= lo) & (run["chainage"].to_numpy(float) <= hi)
    # zakres: okolica odcinka (stacje sesji i odcinek TSD), by szczegoly byly widoczne
    xr = _range(tx[inside], sx)
    yr = _range(ty[inside], sy)
    step = max(1, int(ok.sum() // 600))
    idx = np.nonzero(ok)[0][::step]
    px, py = _xy(tx[idx], ty[idx], xr, yr)
    body = _axes("slad GPS (EPSG:2180)", "E [m]", "N [m]", xr, yr) + _line(px, py, "#9ecae1", 1.0)
    ii = np.nonzero(inside)[0][::max(1, int(inside.sum() // 400))]
    px, py = _xy(tx[ii], ty[ii], xr, yr)
    body += _line(px, py, "#d62728", 1.8)
    matched = sess["station_id"].isin(match["station_id"]).to_numpy()
    px, py = _xy(sx[~matched], sy[~matched], xr, yr)
    body += _points(px, py, "#999999", 1.8)
    px, py = _xy(sx[matched], sy[matched], xr, yr)
    body += _points(px, py, "#2ca02c", 2.6)
    return _svg(body)


def monotonic_panel(match: pd.DataFrame, rho: float) -> str:
    x, y = match["station_m"].to_numpy(float), match["chainage_m"].to_numpy(float)
    xr, yr = _range(x), _range(y)
    px, py = _xy(x, y, xr, yr)
    body = _axes(f"station_m - pikietaz TSD (Spearman {rho:+.3f})", "station_m FWD", "chainage_m TSD", xr, yr) + _points(px, py, "#2ca02c", 2.4)
    if len(x) >= 2 and np.ptp(x) > 0:
        a, b = np.polyfit(x, y, 1)
        lx = np.array([x.min(), x.max()])
        ax_, ay_ = _xy(lx, a * lx + b, xr, yr)
        body += _line(ax_, ay_, "#d62728", 1.2)
    return _svg(body)


def line_to_line_panel(run: pd.DataFrame, match: pd.DataFrame, sess: pd.DataFrame, lo: float, hi: float) -> str:
    """d0 TSD (gesta linia) i D0 FWD (punkty) na wspolnym pikietazu TSD; brak kolumn wartosci -> panel informacyjny."""
    if "d0" not in run or "fwd_d0" not in sess:
        return _svg('<text x="20" y="100" font-size="10">brak kolumn d0 / D0 — wykres pominiety</text>')
    r = run[(run["chainage"] >= lo) & (run["chainage"] <= hi)]
    cx, cy = r["chainage"].to_numpy(float), r["d0"].to_numpy(float)
    fx = match["chainage_m"].to_numpy(float)
    fy = sess.set_index("station_id").reindex(match["station_id"])["fwd_d0"].to_numpy(float)
    xr, yr = _range(cx, fx), _range(cy[cy > 0], fy[np.isfinite(fy)], margin=0.08)
    ok = np.isfinite(cy)
    step = max(1, int(ok.sum() // 600))
    px, py = _xy(cx[ok][::step], cy[ok][::step], xr, yr)
    body = _axes("linia do linii: d0 TSD i D0 FWD", "pikietaz TSD [m]", "[um]", xr, yr) + _line(px, py, "#1f77b4", 1.0)
    px, py = _xy(fx, fy, xr, yr)
    return _svg(body + _points(px, py, "#ff7f0e", 3.0))


def write_review(path, sections: pd.DataFrame, matches: dict, runs: dict, sessions: dict, max_sections: int = 300) -> Path:
    """Zapisuje raport HTML. runs: {run_id: DataFrame(lat, lon, chainage [, d0])}; sessions: {session_id: DataFrame(station_id, lat, lon
    [, fwd_d0])}. Odcinki ponad max_sections sa pominiete w raporcie (pelna tabela jest w sections.csv)."""
    path = Path(path)
    parts = ["<html><head><meta charset='utf-8'><title>Odcinki wspolne TSD-FWD</title>",
             "<style>body{font-family:sans-serif;font-size:12px}.sec{border-top:2px solid #444;margin-top:14px;padding-top:6px}"
             ".row{display:flex;flex-wrap:wrap;gap:6px}td,th{padding:1px 6px;border:1px solid #ccc}</style></head><body>",
             f"<h1>Odcinki wspolne TSD-FWD ({len(sections)})</h1>",
             "<p>Przeglad reczny: sprawdz, czy slad TSD i stacje FWD biegna wspolnie (lewy wykres), czy polozenie stacji rosnie "
             "monotonicznie z pikietazem (srodkowy) i czy profile d0/D0 maja wspolny ksztalt (prawy). Decyzje zapisz w pliku "
             "<code>geometry.sections.review_csv</code>: <code>session_id, run_id, status</code> (confirmed / rejected).</p>"]
    shown = 0
    for r in sections.to_dict("records"):
        if shown >= max_sections:
            parts.append(f"<p>... pominieto {len(sections) - shown} odcinkow (limit raportu {max_sections}); pelna tabela: sections.csv</p>")
            break
        sid, rid = r["session_id"], r["run_id"]
        m = matches[(sid, rid)]
        run, sess = runs[rid], sessions[sid]
        lo, hi = r["chainage_m_min"], r["chainage_m_max"]
        parts.append(
            f"<div class='sec'><b>odcinek {r['section_id']}</b>: sesja FWD {html.escape(str(sid))}, przejazd TSD {html.escape(str(rid))}; "
            f"kierunek {r['direction']}, pas {r['lane_class']}, Spearman {r['spearman_corr']:+.3f}, pokrycie {r['coverage_pct']:.0f} % "
            f"({r['fwd_matched']}/{r['fwd_in_overlap']} stacji), zakres pikietazu {lo:.0f}-{hi:.0f} m, "
            f"mediana odleglosci poprzecznej {r['median_xtrack_m']:+.2f} m, srednia roznica kursow {r['mean_bearing_diff']:.1f} st."
            f"<div class='row'>{trace_panel(run, sess, m, lo, hi)}{monotonic_panel(m, r['spearman_corr'])}"
            f"{line_to_line_panel(run, m, sess, lo, hi)}</div></div>")
        shown += 1
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
