"""Demonstracja narzedzi N1-N4 na danych przykladowych: uruchamia kazde narzedzie i buduje strone `demo\\wyniki\\PODSUMOWANIE.html`.

Uzycie (z katalogu repozytorium):
    C:\\ENV\\narzedzia_tsd_fwd\\python.exe demo\\uruchom_demo.py

Dane: N1 — wycinek XLSX z repozytorium (tests\\data); N2 — 30 pomiarow z `demo\\dane` + cache pogody Open-Meteo (tryb offline, tylko odczyt);
N3 — prawdziwy plik B_1510off z projektu bazy (tylko odczyt) z temperatura warstwy 18 C wpisana na stale (demonstracja);
N4 `pairs` — 5511 par z raportu (tylko odczyt); N4 `geometry` — dane SYNTETYCZNE (znany wynik: iloraz FWD/TSD = 2).
Wyniki zapisuja sie w `demo\\wyniki` (katalog poza git). Zadne dane zrodlowe nie sa zmieniane."""

from __future__ import annotations

import html
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tsdfwd_tools.cli.main import main as cli  # noqa: E402

DEMO = ROOT / "demo"
OUT = DEMO / "wyniki"
CFG = OUT / "konfiguracje"
LOCAL = yaml.safe_load((ROOT / "tests" / "local_paths.yaml").read_text(encoding="utf-8")) if (ROOT / "tests" / "local_paths.yaml").is_file() else {}
SQL = Path(LOCAL.get("sql_tsd_fwd_root", "C:/projects/sql_tsd_fwd"))
DOK = Path(LOCAL.get("doktorat_root", "C:/WORK/DOKTORAT"))


def run(tool: str, name: str, cfg: dict) -> float:
    CFG.mkdir(parents=True, exist_ok=True)
    p = CFG / f"{name}.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    t0 = time.time()
    code = cli([tool, "--config", str(p)])
    dt = time.time() - t0
    print(f"[{name}] kod wyjscia {code}, {dt:.1f} s")
    if code not in (0, 2):
        raise SystemExit(f"{name}: blad (kod {code})")
    return dt


# ---------------------------------------------------------------- dane syntetyczne dla N4 geometry
def synthetic_geometry(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    n = 3000
    chain = np.arange(n, dtype=float)
    lat = 50.0 + chain / 111200.0
    rng = np.random.default_rng(7)
    prof = lambda pos: 100.0 + 12.0 * np.sin(pos / 350.0)               # noqa: E731
    for name, fac in (("T4202507200001_rows.csv", 1.0), ("T4202507200002_rows.csv", 1.0)):
        e = rng.normal(0, 0.12, n // 10 + 1)
        pd.DataFrame(dict(chainage_m=chain, lat=lat, lon=19.0, d0=fac * prof(chain) * np.exp(e[(chain // 10).astype(int)]), gof=0.9,
                          t12_c=22.0, speed_kmh=72.0)).to_csv(dst / name, index=False)
    recs, sid = [], 0
    for k in range(5):
        for i, pos in enumerate(np.arange(300.0, 2700.0, 200.0)):
            sid += 1
            recs.append(dict(station_id=sid, session_id=k + 1, station_m=(pos - 300.0) / 1000.0, latitude=50.0 + (pos + 1.0) / 111200.0,
                             longitude=19.0 + (1.0 if i == 4 else 0.0) / (111200.0 * np.cos(np.radians(50.0))),
                             measured_at=f"2025-07-01T10:{i:02d}:00", device="8082-119", date="2025-07-01",
                             D0=2.0 * prof(pos) * (1 + rng.normal(0, 0.04)), t_mid_c=22.0, t_surface=24.0))
    pd.DataFrame(recs).to_csv(dst / "stacje_fwd.csv", index=False)


# ---------------------------------------------------------------- SVG
def _svg_wrap(body, w=420, h=260):
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="background:#fff;border:1px solid #ddd">{body}</svg>'


def _axes(xr, yr, xl, yl, w=420, h=260, pad=(46, 14, 14, 38)):
    L, T, R, B = pad
    s = [f'<rect x="{L}" y="{T}" width="{w - L - R}" height="{h - T - B}" fill="none" stroke="#999"/>',
         f'<text x="{(L + w - R) / 2:.0f}" y="{h - 6}" font-size="11" text-anchor="middle">{html.escape(xl)}</text>',
         f'<text x="12" y="{(T + h - B) / 2:.0f}" font-size="11" text-anchor="middle" transform="rotate(-90 12 {(T + h - B) / 2:.0f})">{html.escape(yl)}</text>']
    for k in range(5):
        fx = k / 4
        vx, vy = xr[0] + fx * (xr[1] - xr[0]), yr[0] + fx * (yr[1] - yr[0])
        s.append(f'<text x="{L + fx * (w - L - R):.0f}" y="{h - B + 13}" font-size="9" text-anchor="middle">{vx:.4g}</text>')
        s.append(f'<text x="{L - 4}" y="{h - B - fx * (h - T - B) + 3:.0f}" font-size="9" text-anchor="end">{vy:.4g}</text>')
        s.append(f'<line x1="{L}" x2="{w - R}" y1="{h - B - fx * (h - T - B):.0f}" y2="{h - B - fx * (h - T - B):.0f}" stroke="#eee"/>')
    return "".join(s)


def _rng(v, m=0.04):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    lo, hi = float(v.min()), float(v.max())
    d = (hi - lo) * m or 1.0
    return lo - d, hi + d


def scatter(x, y, xl, yl, diag=False, color="#1f77b4", err=None, w=420, h=260, pad=(46, 14, 14, 38)):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    xr = yr = _rng(np.concatenate([x, y])) if diag else None
    if not diag:
        xr, yr = _rng(x), _rng(y if err is None else np.concatenate([y - err[ok], y + err[ok]]))
    L, T, R, B = pad
    px = lambda v: L + (v - xr[0]) / (xr[1] - xr[0]) * (w - L - R)        # noqa: E731
    py = lambda v: h - B - (v - yr[0]) / (yr[1] - yr[0]) * (h - T - B)     # noqa: E731
    body = _axes(xr, yr, xl, yl, w, h, pad)
    if diag:
        body += f'<line x1="{px(xr[0]):.0f}" y1="{py(yr[0]):.0f}" x2="{px(xr[1]):.0f}" y2="{py(yr[1]):.0f}" stroke="#d62728" stroke-dasharray="4 3"/>'
    if err is not None:
        for a, b, e in zip(x, y, np.asarray(err, float)[ok]):
            body += f'<line x1="{px(a):.1f}" x2="{px(a):.1f}" y1="{py(b - e):.1f}" y2="{py(b + e):.1f}" stroke="#aec7e8"/>'
    body += "".join(f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="2.2" fill="{color}" fill-opacity="0.65"/>' for a, b in zip(x, y))
    return _svg_wrap(body, w, h)


def line(x, ys, xl, yl, colors=("#1f77b4", "#ff7f0e"), w=620, h=260, pad=(46, 14, 14, 38)):
    x = np.asarray(x, float)
    xr = _rng(x, 0.0)
    yr = _rng(np.concatenate([np.asarray(v, float) for v in ys]))
    L, T, R, B = pad
    body = _axes(xr, yr, xl, yl, w, h, pad)
    for v, c in zip(ys, colors):
        v = np.asarray(v, float)
        ok = np.isfinite(v) & np.isfinite(x)
        pts = " ".join(f"{L + (a - xr[0]) / (xr[1] - xr[0]) * (w - L - R):.1f},{h - B - (b - yr[0]) / (yr[1] - yr[0]) * (h - T - B):.1f}" for a, b in zip(x[ok], v[ok]))
        body += f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="1.2"/>'
    return _svg_wrap(body, w, h)


def table(df: pd.DataFrame, cols=None, n=6, fmt="{:.4g}") -> str:
    d = df[cols] if cols else df
    d = d.head(n).copy()
    d = d.astype(object).where(d.notna(), "")
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(fmt.format(v) if isinstance(v, (float, np.floating)) else str(v))}</td>" for v in r) + "</tr>"
                   for r in d.itertuples(index=False))
    return f"<table><tr>{head}</tr>{rows}</table>"


def files_list(d: Path, names=None) -> str:
    items = sorted(p for p in d.iterdir() if p.is_file()) if names is None else [d / n for n in names if (d / n).is_file()]
    return "<ul class='files'>" + "".join(f"<li><a href='{p.relative_to(OUT).as_posix()}'>{html.escape(p.name)}</a> <span>{p.stat().st_size / 1024:.0f} kB</span></li>"
                                          for p in items) + "</ul>"


def section(title, intro, cmd, body) -> str:
    return (f"<section><h2>{html.escape(title)}</h2><p>{intro}</p><pre>{html.escape(cmd)}</pre>{body}</section>")


# ---------------------------------------------------------------- scenariusze
def demo_n1() -> str:
    d = OUT / "n1"
    run("fwd_tempcorr", "n1", {"tool": "fwd_tempcorr", "schema_version": 1,
                                "input": {"files": [str(ROOT / "tests/data/Drops50_1M_1.xlsx")], "stations_files": [str(ROOT / "tests/data/stations50_1M_1.xlsx")],
                                          "format": "auto", "drop_rule": "mean_nonseating"},
                                "temperature": {"source": "column", "column": "asphalt_temp", "depth_cm": 12},
                                "correction": {"variant": "B", "coefficient_set": "e2a3_full"},
                                "output": {"dir": str(d), "formats": ["csv"], "overwrite": True}})
    df = pd.read_csv(d / "Drops50_1M_1_tempcorr.csv")
    summ = pd.read_csv(d / "summary.csv")
    from tsdfwd_tools.fwd.tempcorr import correct_deflections
    base = df.iloc[0]
    cols = ["D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800"]
    temps = np.arange(5.0, 35.1, 1.0)
    d_um = pd.DataFrame([base[cols].to_numpy(float)] * len(temps), columns=cols)
    corr = correct_deflections(d_um, temps, variant="B")
    ratio = corr.d20["D0_20"].to_numpy() / d_um["D0"].to_numpy()
    svg = line(temps, [ratio], "temperatura warstwy T_mid [°C]", "D0 po korekcie / D0 przed", colors=("#2ca02c",), w=420)
    fl = df["flags_text"].fillna("").replace("", "(brak flag)").value_counts().head(6).rename_axis("flagi").reset_index(name="stacji")
    return section("N1 — korekta temperaturowa FWD",
                   f"Ugięcia z {len(df)} stacji sprowadzone do 20 °C i 50 kN (wariant wykładniczy B, współczynniki z raportu); wskaźniki SCI300, BDI, BCI liczone dopiero z ugięć skorygowanych. Wykres: współczynnik korekty D0 w funkcji temperatury. Im zimniej, tym zmierzone ugięcia są mniejsze, więc korekta je zwiększa; im cieplej, tym je zmniejsza (powyżej 30 °C wynik jest oznaczany flagą, poniżej 5 °C korekta nie ma zastosowania).",
                   "python -m tsdfwd_tools fwd_tempcorr --config konfiguracje\\n1.yaml",
                   f"<div class='row'>{svg}<div>{table(df, ['station_id', 't_mid_c', 'force_kn', 'D0', 'D0_20', 'SCI300_20', 'BDI_20', 'BCI_20', 'flags_text'], 8)}"
                   f"<h4>Flagi</h4>{table(fl, None, 6)}</div></div><h4>Pliki wynikowe</h4>{files_list(d)}")


def demo_n2() -> str:
    d = OUT / "n2"
    cache = DOK / "temp_model/output/z14lite/openmeteo_cache_utc"
    run("layer_temp", "n2", {"tool": "layer_temp", "schema_version": 1,
                             "input": {"survey_csv": str(DEMO / "dane/pomiary_pirometr_demo.csv")},
                             "meteo": {"cache_dir": str(cache), "offline": True},
                             "comparators": {"bells3": True}, "output": {"dir": str(d), "overwrite": True}})
    df = pd.read_csv(d / "layer_temp.csv")
    meta = json.loads((d / "layer_temp_meta.json").read_text(encoding="utf-8"))
    ref = pd.read_csv(DEMO / "dane/pomiary_pirometr_demo.csv")
    svg = scatter(ref["t_layer"].to_numpy(), df["t_layer"].to_numpy(), "temperatura warstwy zmierzona sondą [°C]", "model N2 [°C]", diag=True, err=df["u95"].to_numpy())
    err = df["t_layer"].to_numpy() - ref["t_layer"].to_numpy()
    flags = df["flags_text"].fillna("").replace("", "(brak flag)").value_counts().rename_axis("flagi").reset_index(name="pomiarów")
    return section("N2 — temperatura warstwy asfaltowej",
                   f"Fizyczny model 1-D z jednorazową kalibracją do pirometru i pogodą z Open-Meteo (tu: tryb offline z zapisanego cache). 30 pomiarów demonstracyjnych z sondą jako odniesieniem — "
                   f"RMSE {np.sqrt(np.mean(err ** 2)):.2f} °C, błąd średni {err.mean():+.2f} °C. To mały zbiór pokazowy; rzetelna dokładność to 1,75 °C (zbiór eksploracyjny) i 2,73 °C (niezależny).",
                   "python -m tsdfwd_tools layer_temp --config konfiguracje\\n2.yaml",
                   f"<div class='row'>{svg}<div>{table(df, ['measured_at_local', 't_surface', 't_layer', 'u95', 'a_sw', 'calib_flag', 'flags_text'], 8)}"
                   f"<h4>Flagi</h4>{table(flags, None, 6)}</div></div><p class='note'>Pionowe kreski: niepewność u95. Linia czerwona: zgodność idealna. {meta.get('accuracy_note', '')}</p>"
                   f"<h4>Pliki wynikowe</h4>{files_list(d)}")


def demo_n3() -> str:
    d = OUT / "n3"
    src = SQL / "baza_TSD_FWD_odcinki/TSD/B_1510off/T4202504230012.raw.sup.txt"
    run("tsd_network", "n3", {"tool": "tsd_network", "schema_version": 1, "input": {"tsd_files": [str(src)]},
                              "layer_temp": {"source": "constant", "constant_c": 18.0},
                              "processing": {"window_m": 5.0, "aggregate_m": [50, 100]}, "qc": {"gps_gyro": False},
                              "xml_uc": {"enabled": True, "kod_oddz": "WA", "rok": 2025, "droga": "50", "jezdnia": 1, "pas": 1, "km_start": 40.0, "km_direction": "increasing"},
                              "output": {"dir": str(d), "rows_csv": False, "overwrite": True}})
    w = pd.read_csv(d / "T4202504230012_windows_10m.csv")
    summ = pd.read_csv(d / "summary.csv").iloc[0]
    xml = (d / "UC_T4202504230012.xml").read_text(encoding="utf-8").splitlines()
    ok = w["window_ok"].astype(bool)
    svg = line(w.loc[ok, "center_m"], [w.loc[ok, "d0_20"], w.loc[ok, "a031"]], "pikietaż [m]", "niebieska: d0 po korekcie; pomarańczowa: całka 0-0,31 m [µm]")
    return section("N3 — TSD na sieci i plik XML DSN",
                   f"Prawdziwy przejazd TSD (eksport B_1510off, {int(summ['n_rows'])} wierszy co 1 m, {summ['date']}), temperatura warstwy 18 °C wpisana na stałe (w produkcji: wynik N2). "
                   f"Narzędzie koryguje d0 do 20 °C, filtruje odstające wiersze (Hampel), liczy całki nachyleń, uśrednia w oknach ±5 m co 10 m i zapisuje XML w układzie załącznika H.",
                   "python -m tsdfwd_tools tsd_network --config konfiguracje\\n3.yaml",
                   f"<div class='row'>{svg}<div>{table(w, ['center_m', 'n_valid_d0', 'd0_20', 'a031', 'gof_share_ge05', 'speed_kmh'], 6)}</div></div>"
                   f"<h4>Fragment pliku XML (UC_T4202504230012.xml)</h4><pre class='xml'>{html.escape(chr(10).join(xml[:32]))}\n...</pre>"
                   f"<h4>Pliki wynikowe</h4>{files_list(d)}")


def demo_n4_pairs() -> str:
    d = OUT / "n4_pairs"
    z15 = DOK / "wymiana/wyniki/z15/Z15_temperatury_par.csv"
    tab = SQL / "tabele"
    run("tsd_fwd_compare", "n4_pairs", {"tool": "tsd_fwd_compare", "schema_version": 1, "mode": "pairs",
                                        "input": {"pairs_csv": str(z15), "meta_csv": str(tab / "e2b2_pairs.csv"), "null_pairs_csv": str(tab / "e2b2_null_values.csv")},
                                        "correction": {"treatments": ["none", "main_after"], "main_treatment": "main_after"},
                                        "measures": {"n_boot": 200}, "uncertainty": {"replicates": 999}, "null_checks": {"n_boot": 200},
                                        "output": {"dir": str(d), "overwrite": True}})
    ag = pd.read_csv(d / "agreement.csv")
    pr = pd.read_csv(d / "pairs_corrected.csv")
    sub = pr.sample(1500, random_state=1)
    svg = scatter(np.log10(sub["tsd_main_after"]), np.log10(sub["fwd_main_after"]), "log10 d0 TSD po korekcie", "log10 D0 FWD po korekcie", diag=True, color="#9467bd")
    nl = pd.read_csv(d / "null_checks.csv")
    conv = pd.read_csv(d / "conversion.csv")
    return section("N4 (tryb pairs) — porównanie TSD z FWD na gotowych parach",
                   "Zbiór 5511 par z raportu: obie strony skorygowane do 20 °C temperaturą warstwy, miary zgodności, przedziały niepewności trzema metodami, kontrola zerowa (ta sama stacja FWD, ale TSD z miejsca przesuniętego o ±200 m albo losowego). "
                   "Pokazuję 1500 losowych par; liczby w tabelach dotyczą wszystkich (przedziały z 200/999 replik, w pełnym uruchomieniu 1000/9999).",
                   "python -m tsdfwd_tools tsd_fwd_compare --config konfiguracje\\n4_pairs.yaml",
                   f"<div class='row'>{svg}<div><h4>Miary zgodności</h4>{table(ag, ['variant', 'n_pairs', 'n_sessions', 'median_ratio', 'median_ratio_lo', 'median_ratio_hi', 'pearson_r', 'ccc'], 4)}"
                   f"<h4>Kontrola zerowa</h4>{table(nl, ['pair_kind', 'n_pairs', 'median_ratio', 'pearson_r'], 5)}</div></div>"
                   f"<p class='note'>Mediana ilorazu FWD/TSD po korekcie ≈ {ag.loc[ag.variant == 'main_after', 'median_ratio'].iloc[0]:.2f} (raport: 1,616). Pary zerowe zgodnością ustępują prawdziwym.</p>"
                   f"<h4>Pliki wynikowe</h4>{files_list(d)}")


def demo_n4_geometry() -> str:
    d, src = OUT / "n4_geometry", OUT / "dane_syntetyczne"
    synthetic_geometry(src)
    run("tsd_fwd_compare", "n4_geometry", {"tool": "tsd_fwd_compare", "schema_version": 1, "mode": "geometry",
                                           "geometry": {"tsd_rows": [str(src / "T4202507200001_rows.csv"), str(src / "T4202507200002_rows.csv")],
                                                        "fwd_stations_csv": str(src / "stacje_fwd.csv"), "lambda_est": {"enabled": True}},
                                           "measures": {"n_boot": 200}, "uncertainty": {"replicates": 499}, "null_checks": {"n_boot": 200},
                                           "output": {"dir": str(d), "overwrite": True}})
    gp = pd.read_csv(d / "geometry_pairs.csv")
    sec = pd.read_csv(d / "sections.csv")
    ag = pd.read_csv(d / "agreement.csv")
    pl = pd.read_csv(d / "fwd_plate_positions.csv")
    lam = pd.read_csv(d / "lambda_estimate.csv")
    svg = scatter(pl["s_ant"], pl["s_fwd"] - pl["s_ant"], "pozycja stacji na osi [m]", "przesunięcie antena → płyta [m]", color="#e377c2")
    return section("N4 (tryb geometry) — pary budowane z geometrii (dane syntetyczne)",
                   "Dwa przejazdy TSD po jednej drodze i pięć sesji FWD po 12 stacji (jedna stacja przesunięta 1 m w bok). N4 sam buduje oś pasa, wykrywa odcinki wspólne (Tab. 3.2), ustala położenie płyty FWD (antena 1 m przed płytą, aparat 8082-119), tworzy pary w oknach ±5 m, "
                   "nadaje warstwy jakości położenia i szacuje lambdę. Dane są sztuczne: prawdziwy iloraz FWD/TSD wynosi 2,0, a stacja przesunięta w bok wypada z warstwy A. Na prawdziwych danych ten sam potok odtwarza całą bazę referencyjną (testy regresji).",
                   "python -m tsdfwd_tools tsd_fwd_compare --config konfiguracje\\n4_geometry.yaml",
                   f"<div class='row'>{svg}<div><h4>Odcinki wspólne</h4>{table(sec, ['session_id', 'run_id', 'direction', 'lane_class', 'spearman_corr', 'coverage_pct', 'fwd_matched'], 4)}"
                   f"<h4>Pary (kandydaci)</h4>{table(gp, ['station_id', 'dlat', 'sigma_long_fwd', 'layer', 'win5_n', 'd0_tsd', 'fwd_d0', 'in_section'], 6)}</div></div>"
                   f"<h4>Zgodność</h4>{table(ag, ['variant', 'n_pairs', 'n_sessions', 'median_ratio', 'median_ratio_lo', 'median_ratio_hi'], 3)}"
                   f"<h4>Szacunek lambdy z powtórzeń</h4>{table(lam, ['lambda_d0', 'sigma_tsd', 'sigma_fwd', 'n_pairs_tsd', 'n_pairs_fwd'], 1)}"
                   f"<p><a href='n4_geometry/section_review.html'>Raport przeglądu odcinków „linia do linii” (section_review.html)</a></p>"
                   f"<h4>Pliki wynikowe</h4>{files_list(d)}")


CSS = """body{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;margin:20px auto;padding:0 14px;color:#222}h1{border-bottom:3px solid #444}
section{margin:26px 0;padding:10px 14px;border:1px solid #ccc;border-radius:6px}h2{margin-top:0;color:#1f4e79}pre{background:#f4f4f4;padding:6px 10px;overflow:auto}
pre.xml{font-size:11px;max-height:340px}.row{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}table{border-collapse:collapse;font-size:12px;margin:4px 0}
td,th{border:1px solid #ccc;padding:2px 7px}th{background:#eef}.note{font-size:12px;color:#555}ul.files{columns:2;font-size:12px}ul.files span{color:#888}h4{margin:10px 0 3px}"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parts, t0 = [], time.time()
    for fn in (demo_n1, demo_n2, demo_n3, demo_n4_pairs, demo_n4_geometry):
        parts.append(fn())
    page = (f"<html><head><meta charset='utf-8'><title>Demonstracja narzędzi TSD/FWD</title><style>{CSS}</style></head><body>"
            f"<h1>Narzędzia TSD/FWD — demonstracja</h1><p>Uruchomiono wszystkie narzędzia na danych przykładowych w {time.time() - t0:.0f} s. "
            f"Dane źródłowe nie są zmieniane (tylko odczyt); wyniki leżą w katalogu <code>demo\\wyniki</code>.</p>" + "".join(parts) + "</body></html>")
    (OUT / "PODSUMOWANIE.html").write_text(page, encoding="utf-8")
    print("zapisano", OUT / "PODSUMOWANIE.html")


if __name__ == "__main__":
    main()
