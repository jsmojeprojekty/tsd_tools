"""N4 tryb `geometry`: pary TSD-FWD zbudowane z geometrii (wspolna os, polozenie plyty FWD, okna po s_ref) i pary zerowe.

Przeplyw: wiersze TSD (eksport B_1510off, np. `*_rows.csv` z N3) -> ciagi i korytarze (os referencyjna pasa, GPS skorygowany o lag
-4,8 m) -> przypisanie wierszy (s_ref, lateral) -> stacje FWD (antena, dystansomierz, plyta) -> kandydaci na pary i warstwy
jakosci polozenia -> pary zerowe -> wartosci okien W5 (mediana d0, >= 3 wiersze). Wynik ma format wejscia trybu `pairs`.

Zasada: parowanie wylacznie geometryczne; wartosci (d0) nie biora udzialu w wyborze rekordu (okna wskazuje polozenie).
Ograniczenia wzgledem procedury referencyjnej (patrz DZIENNIK E2b): s_ref = s_ref_gps (bez wyrownania profilem), bez scalania
duplikatow pasa, bez wykrywania odcinkow wspolnych wg Tab. 3.2 i flagi `in_stage1`."""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..common.config import ConfigError, resolve_path
from ..common.config_n4 import N4Config
from ..tsd.io import date_from_name
from . import geo as G
from . import fwd_position as FP
from . import pairing as PA
from . import sections as SEC
from . import lambda_est as LAM

log = logging.getLogger(__name__)


def _read_csv(path, what: str) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"brak pliku {what}: {p}")
    return pd.read_csv(p, encoding="utf-8-sig")


def _to_epoch(col: pd.Series) -> np.ndarray:
    """Czas wiersza (liczba = sekundy epoki albo tekst ISO) -> sekundy epoki (czas lokalny zapisany jak UTC)."""
    num = pd.to_numeric(col, errors="coerce")
    if num.notna().mean() > 0.5:
        return num.to_numpy(float)
    dt = pd.to_datetime(col, errors="coerce")
    return np.where(dt.isna(), np.nan, dt.astype("datetime64[s]").astype("int64").astype(float))


def _run_name(path: Path) -> str:
    stem = path.name.split(".")[0]
    return stem[:-5] if stem.endswith("_rows") else stem


def load_tsd_rows(cfg: N4Config) -> tuple[dict, dict]:
    """Wiersze TSD pogrupowane po przejezdzie: {run_id: DataFrame(chainage, lat, lon, d0, gof, t12, speed)} + {pliki: sciezki}."""
    g, c = cfg.geometry, cfg.geometry.tsd_columns
    runs, files = {}, {}
    for pth in g.tsd_rows:
        p = resolve_path(pth, cfg.base_dir)
        df = _read_csv(p, "wierszy TSD")
        files[f"tsd_rows:{p.name}"] = str(p)
        need = [c.chainage, c.lat, c.lon, c.d0]
        missing = [n for n in need if n not in df.columns]
        if missing:
            raise ConfigError(f"{p.name}: brak wymaganych kolumn {missing} (dostepne: {list(df.columns)})")
        keys = df[c.run_id].astype(str) if c.run_id in df else pd.Series(_run_name(p), index=df.index)
        for rid, sub in df.groupby(keys, sort=False):
            out = pd.DataFrame({
                "chainage": pd.to_numeric(sub[c.chainage], errors="coerce").to_numpy(float),
                "lat": pd.to_numeric(sub[c.lat], errors="coerce").to_numpy(float),
                "lon": pd.to_numeric(sub[c.lon], errors="coerce").to_numpy(float),
                "d0": pd.to_numeric(sub[c.d0], errors="coerce").to_numpy(float),
                "gof": pd.to_numeric(sub[c.gof], errors="coerce").to_numpy(float) if c.gof in sub else np.nan,
                "t12": pd.to_numeric(sub[c.t12], errors="coerce").to_numpy(float) if c.t12 in sub else np.nan,
                "speed": pd.to_numeric(sub[c.speed], errors="coerce").to_numpy(float) if c.speed in sub else np.nan,
                "t": _to_epoch(sub[c.time]) if c.time in sub else np.nan,
                "conc": pd.to_numeric(sub[c.concrete], errors="coerce").fillna(0).to_numpy(float) if c.concrete in sub else 0.0})
            ch = out["chainage"].to_numpy()
            if np.isfinite(ch).sum() > 1 and not (np.diff(ch[np.isfinite(ch)]) >= 0).all():
                raise ConfigError(f"przejazd {rid}: pikietaz ({c.chainage}) musi byc niemalejacy; podaj SUROWY pikietaz pliku, "
                                  "nie pozycje po przesunieciu")
            if rid in runs:
                raise ConfigError(f"powtorzony przejazd {rid!r} w plikach wierszy TSD")
            runs[str(rid)] = out
    return runs, files


def run_table(cfg: N4Config, runs: dict, files: dict) -> pd.DataFrame:
    """Tabela przejazdow TSD: run_id, date, calib_interval, data_tier, recorder_group (z pliku, nazwy lub daty wspolnej)."""
    g = cfg.geometry
    meta = {}
    if g.tsd_runs_csv:
        p = resolve_path(g.tsd_runs_csv, cfg.base_dir)
        t = _read_csv(p, "przejazdow TSD")
        files["tsd_runs_csv"] = str(p)
        if "run_id" not in t:
            raise ConfigError("geometry.tsd_runs_csv: wymagana kolumna run_id")
        meta = {str(r["run_id"]): r for r in t.to_dict("records")}
    rows = []
    for rid in runs:
        m = meta.get(rid, {})
        d = m.get("date")
        if d is None or (isinstance(d, float) and np.isnan(d)):
            d = g.date_override
        if d is None:
            nd = date_from_name(rid)
            d = nd.isoformat() if nd else None
        if d is None:
            raise ConfigError(f"przejazd {rid!r}: brak daty (geometry.tsd_runs_csv, nazwa pliku z data albo geometry.date_override)")
        ci = m.get("calib_interval")
        if ci is None or (isinstance(ci, float) and np.isnan(ci)):
            ci = next((name for name, (a, b) in g.calib_intervals.items() if str(a) <= str(d)[:10] <= str(b)), None)
        rows.append(dict(run_id=rid, date=str(d)[:10], calib_interval=ci, data_tier=m.get("data_tier"),
                         recorder_group=m.get("recorder_group")))
    return pd.DataFrame(rows)


def load_stations(cfg: N4Config, files: dict) -> pd.DataFrame:
    g, c = cfg.geometry, cfg.geometry.fwd_columns
    p = resolve_path(g.fwd_stations_csv, cfg.base_dir)
    df = _read_csv(p, "stacji FWD")
    files["fwd_stations_csv"] = str(p)
    need = {"station_id": c.station_id, "session_id": c.session, "station_m": c.station_m, "lat": c.lat, "lon": c.lon,
            "device": c.device, "date": c.date, "fwd_d0": c.d0, "fwd_t12": c.t12}
    missing = [v for v in need.values() if v not in df.columns]
    if missing:
        raise ConfigError(f"stacje FWD: brak wymaganych kolumn {missing} (dostepne: {list(df.columns)})")
    out = pd.DataFrame({k: df[v] for k, v in need.items()})
    out["time"] = df[c.time].astype(str) if c.time in df else ""
    out["heading_deg"] = pd.to_numeric(df[c.heading], errors="coerce") if c.heading in df else np.nan
    if c.in_concrete_zone in df:
        out["in_concrete_zone"] = df[c.in_concrete_zone]
    out["t_surface"] = pd.to_numeric(df[c.t_surface], errors="coerce") if c.t_surface in df else np.nan
    for k in ("station_m", "lat", "lon", "fwd_d0", "fwd_t12"):
        out[k] = pd.to_numeric(out[k], errors="coerce")
    out["date"] = out["date"].astype(str).str[:10]
    out["station_id"] = out["station_id"].astype(int)
    return out


def load_corridors_file(path) -> list:
    pts = _read_csv(path, "osi")
    need = {"corridor_id", "s", "x_2180", "y_2180", "heading_deg"}
    if not need <= set(pts.columns):
        raise ConfigError(f"os: wymagane kolumny {sorted(need)}")
    out = []
    for cid, grp in pts.sort_values(["corridor_id", "s"]).groupby("corridor_id"):
        c = G.Corridor(int(cid), grp.x_2180.to_numpy(), grp.y_2180.to_numpy(), [])
        c.set_geom(grp.x_2180.to_numpy(), grp.y_2180.to_numpy(), hd=grp.heading_deg.to_numpy())
        out.append(c)
    return out


def position_params(cfg: N4Config) -> FP.PositionParams:
    g = cfg.geometry
    rules = FP.default_antenna_rules()
    if g.antenna:
        rules = [FP.AntennaRule(device=str(r["device"]), d_m=float(r["d_m"]), era=str(r.get("era", "unknown")),
                                confirmed=int(r.get("confirmed", 1)), from_date=r.get("from"), until_date=r.get("until"))
                 for r in g.antenna]
    sigma = dict(FP.DEFAULT_SIGMA_ERA)
    sigma.update({k: float(v) for k, v in g.sigma_era.items()})
    ax = G.AxisParams(**{k: v for k, v in g.axis.items()}) if g.axis else G.AxisParams()
    return FP.PositionParams(rules=rules, sigma_era=sigma, eps_variant=g.eps_variant, axis=ax)


def detect_common_sections(cfg: N4Config, runs_df: dict, rtab: pd.DataFrame, stations: pd.DataFrame, files: dict):
    """Odcinki wspolne wg Tab. 3.2 na wejsciu trybu geometry. Zwraca (tabela odcinkow, dopasowania, liczniki, przejazdy i sesje do raportu)."""
    sc = cfg.geometry.sections
    params = SEC.SectionParams(radius_m=sc.radius_m, min_coverage_pct=sc.min_coverage_pct, min_abs_spearman=sc.min_abs_spearman,
                               bearing_tol_deg=sc.bearing_tol_deg, max_days=sc.max_days, lane_same_max_m=sc.lane_same_max_m,
                               lane_adjacent_max_m=sc.lane_adjacent_max_m, same_year_only=sc.same_year_only,
                               min_overlap_len_m=sc.min_overlap_len_m, min_matched_stations=sc.min_matched_stations)
    runs = {}
    for rid, d in runs_df.items():
        x = d.rename(columns={"chainage": "chainage"}).copy()
        x = x[np.isfinite(x["lat"]) & np.isfinite(x["lon"])].sort_values("chainage", kind="stable").reset_index(drop=True)
        runs[rid] = SEC.ensure_headings(x, ["chainage"])
    sessions, info = {}, {}
    for sid, g in stations.groupby("session_id", sort=True):
        g = SEC.ensure_headings(g.reset_index(drop=True).rename(columns={"heading_deg": "heading"}), ["time", "station_id"])
        g = g.sort_values(["station_m", "station_id"], kind="stable").reset_index(drop=True)
        sessions[sid] = g
        dates = g["date"].astype(str)
        info[sid] = (dates.min(), dates.max())
    run_dates = dict(zip(rtab["run_id"], rtab["date"]))
    tab, matches, cnt = SEC.detect_sections(runs, run_dates, sessions, info, params)
    status = {}
    if sc.review_csv:
        rp = resolve_path(sc.review_csv, cfg.base_dir)
        rv = _read_csv(rp, "przegladu odcinkow")
        files["sections_review_csv"] = str(rp)
        if not {"session_id", "run_id", "status"} <= set(rv.columns):
            raise ConfigError("geometry.sections.review_csv: wymagane kolumny session_id, run_id, status")
        status = {(r["session_id"], str(r["run_id"])): str(r["status"]).strip().lower() for r in rv.to_dict("records")}
    if len(tab):
        tab["review_status"] = [status.get((s, str(r)), "unreviewed") for s, r in zip(tab["session_id"], tab["run_id"])]
    return tab, matches, cnt, runs, sessions


def estimate_lambda_from_inputs(cfg: N4Config, plate: pd.DataFrame, stations: pd.DataFrame, passes_df: pd.DataFrame, pass_rows: dict) -> dict:
    """Estymator lambdy na danych trybu geometry: przejazdy TSD (biny korytarza po s_ref) i stacje FWD (okna po s_fwd)."""
    le = cfg.geometry.lambda_est
    params = LAM.LambdaParams(bin_m=le.bin_m, cover_min_n=le.cover_min_n, tsd_max_dt_days=le.tsd_max_dt_days,
                              fwd_from_date=le.fwd_from_date, fwd_max_dtemp_c=le.fwd_max_dtemp_c,
                              fwd_min_stations=le.fwd_min_stations, exclude_concrete=le.exclude_concrete)
    if not stations["t_surface"].notna().any():
        raise ConfigError("geometry.lambda_est: stacje FWD wymagaja kolumny temperatury powierzchni "
                          f"({cfg.geometry.fwd_columns.t_surface!r}) - potrzebna do doboru par okien |dT| < {le.fwd_max_dtemp_c:g} C")
    f = plate.drop(columns=["t_surface"], errors="ignore").merge(stations[["station_id", "t_surface"]], on="station_id", how="left")
    f = f[(f["lane_match"] == "same") & f["s_fwd"].notna() & (f["fwd_d0"] > 0)]
    conc = (pd.to_numeric(f["in_concrete_zone"], errors="coerce").fillna(0).astype(int) if "in_concrete_zone" in f
            else pd.Series(0, index=f.index))
    fw = pd.DataFrame({"station": f["station_id"].to_numpy(), "corridor": f["corridor_id"].to_numpy(), "s": f["s_fwd"].to_numpy(),
                       "session": f["session_id"].to_numpy(), "device": f["device"].to_numpy(), "date": f["date"].astype(str).to_numpy(),
                       "temp": f["t_surface"].to_numpy(float), "ld0": np.log(f["fwd_d0"].to_numpy(float)), "conc": conc.to_numpy()})
    pdates = dict(zip(passes_df["pass_id"], passes_df["date"]))
    pcorr = dict(zip(passes_df["pass_id"], passes_df["corridor_id"]))
    res = LAM.estimate_lambda(pass_rows, pdates, pcorr, fw, params)
    res["params"] = vars(params)
    res["time_basis"] = ("czas wiersza" if any("t" in v for v in pass_rows.values()) else
                         "data przejazdu (poludnie): |dt| <= 1 dzien = ta sama lub sasiednia data")
    return res


def build_geometry_pairs(cfg: N4Config) -> dict:
    """Zwraca slownik: pairs (DataFrame w formacie wejscia trybu pairs, nazwy znormalizowane), nulls (pair_id, null_type, d0_w5,
    d0_valid_w5), tabele pomocnicze (geo_pairs, geo_fwd, geo_passes, geo_corridors, geo_nulls), files i meta."""
    g = cfg.geometry
    files: dict = {}
    runs_df, f1 = load_tsd_rows(cfg)
    files.update(f1)
    rtab = run_table(cfg, runs_df, files)
    stations = load_stations(cfg, files)
    ppar = position_params(cfg)
    ax = ppar.axis

    runs = {rid: G.prepare_run(d["chainage"].to_numpy(), d["lat"].to_numpy(), d["lon"].to_numpy(), g.lag_m, ax)
            for rid, d in runs_df.items()}
    if g.corridors_csv:
        cp = resolve_path(g.corridors_csv, cfg.base_dir)
        corridors = load_corridors_file(cp)
        files["corridors_csv"] = str(cp)
        assigned = {rid: G.assign_run(corridors, r, True, ax) for rid, r in runs.items()}
        axis_info = dict(source="file", n_corridors=len(corridors))
    else:
        corridors, assigned, axis_info = G.build_axis(runs, ax)
        axis_info["source"] = "tsd_runs"
    log.info("os: %d korytarzy (%s), przejazdow TSD: %d, stacji FWD: %d", len(corridors), axis_info["source"], len(runs), len(stations))

    # przejscia (plik x korytarz) i wiersze przejsc posortowane po s_ref
    passes, pass_rows = [], {}
    rt = rtab.set_index("run_id")
    for rid, d in runs_df.items():
        cid, s, lat, _ = assigned[rid]
        for cc, idx in G.pass_groups(cid, s, ax):
            ok = np.isfinite(s[idx])
            idx = idx[ok]
            if len(idx) == 0:
                continue
            pid = len(passes) + 1
            order = np.argsort(s[idx], kind="stable")
            ix = idx[order]
            pass_rows[pid] = dict(s=s[ix], tsd_id=ix.astype(np.int64), lat=lat[ix], gof=d["gof"].to_numpy()[ix],
                                  d0=d["d0"].to_numpy()[ix], t12=d["t12"].to_numpy()[ix])
            if np.isfinite(d["t"].to_numpy()).any():
                pass_rows[pid]["t"] = d["t"].to_numpy()[ix]
            if d["conc"].to_numpy().any():
                pass_rows[pid]["conc"] = d["conc"].to_numpy()[ix]
            speeds = d["speed"].to_numpy()[ix]
            passes.append(dict(pass_id=pid, file_id=rid, corridor_id=int(cc), date=rt.loc[rid, "date"],
                               v_med=float(np.nanmedian(speeds)) if np.isfinite(speeds).any() else None,
                               calib_interval=rt.loc[rid, "calib_interval"], calib_interval_uncertain=None,
                               data_tier=rt.loc[rid, "data_tier"], recorder_group=rt.loc[rid, "recorder_group"],
                               n_points=int(len(ix)), s_start=float(s[ix].min()), s_end=float(s[ix].max())))
    passes_df = pd.DataFrame(passes)
    if passes_df.empty:
        raise ConfigError("zadne wiersze TSD nie zostaly przypisane do korytarzy (sprawdz wspolrzedne, pikietaz i kierunek)")

    plate, sessions, fwd_runs = FP.fwd_plate_positions(corridors, stations.drop(columns=["fwd_d0", "fwd_t12"]), ppar)
    plate = plate.merge(stations[["station_id", "fwd_d0", "fwd_t12"]], on="station_id", how="left")
    sec_tab, sec_matches, sec_cnt, sec_runs, sec_sessions = (pd.DataFrame(), {}, {}, {}, {})
    if g.sections.enabled:
        sec_tab, sec_matches, sec_cnt, sec_runs, sec_sessions = detect_common_sections(cfg, runs_df, rtab, stations, files)
        log.info("odcinki wspolne (Tab. 3.2): %d (odrzucone pary: %s)", len(sec_tab),
                 {k: v for k, v in sec_cnt.items() if k != "n_sections" and v})
    lam_res = None
    if g.lambda_est.enabled:
        lam_res = estimate_lambda_from_inputs(cfg, plate, stations, passes_df, pass_rows)
        log.info("lambda d0 (estymator): %.5f (sigma_TSD %.4f z %d par; sigma_FWD %.4f z %d par)", lam_res["lambda_d0"],
                 lam_res["sigma_tsd"], lam_res["n_pairs_tsd"], lam_res["sigma_fwd"], lam_res["n_pairs_fwd"])
    cand = PA.build_candidates(plate, passes_df, pass_rows)
    if cand.empty:
        raise ConfigError("brak par kandydackich: stacje FWD nie leza na wspolnych korytarzach z przejazdami TSD "
                          "(pas, rok, odleglosc <= 100 m od wiersza TSD)")
    nulls_all = PA.build_null_pairs(cand, pass_rows)

    vals = PA.pair_values(cand, pass_rows, "d0", g.window_m, g.min_rows)
    cand = cand.merge(vals.rename(columns={"value": "d0_tsd", "n_valid": "n_valid_d0", "window_ok": "d0_window_ok"}),
                      on="pair_id", how="left")
    cand = cand.merge(plate[["station_id", "fwd_d0", "fwd_t12", "date"]].rename(columns={"date": "fwd_date"}),
                      on="station_id", how="left")
    t12 = []
    for r in cand[["pass_id", "s_fwd"]].itertuples(index=False):
        pr = pass_rows[r.pass_id]
        j = PA.nearest_row(pr["s"], r.s_fwd)
        t12.append(pr["t12"][j] if j is not None else np.nan)
    cand["tsd_t12"] = t12
    cand["group"] = cand["era"].astype(str) + "_" + cand["tsd_year"].astype(str)

    if g.sections.enabled:
        if len(sec_tab):
            key = sec_tab[["session_id", "run_id", "section_id", "lane_class", "direction", "review_status"]].copy()
            key["run_id"] = key["run_id"].astype(str)
            key.columns = ["session_id", "file_id", "section_id", "section_lane", "section_direction", "section_status"]
            cand["file_id"] = cand["file_id"].astype(str)
            cand = cand.merge(key, on=["session_id", "file_id"], how="left")
        else:
            for c_ in ("section_id", "section_lane", "section_direction", "section_status"):
                cand[c_] = None
        cand["in_section"] = cand["section_id"].notna().astype(int)
    keep = cand["layer"].isin(g.layers)
    if g.sections.enabled and g.sections.require_section:
        keep &= (cand["in_section"] == 1) & (cand["section_status"] != "rejected")
    if g.same_year_only:
        keep &= cand["same_year"] == 1
    if g.require_valid_d0:
        keep &= (cand["fwd_d0"] > 0) & (cand["d0_tsd"] > 0)
    sel = cand[keep].copy()
    if sel.empty:
        raise ConfigError(f"po filtrach (warstwy {g.layers}, ten sam rok: {g.same_year_only}, wazne d0: {g.require_valid_d0}) nie zostala "
                          f"zadna para z {len(cand)} kandydatow; warstwy kandydatow: "
                          f"{ {k: int(v) for k, v in cand['layer'].value_counts().items()} }, same_year=1: {int((cand['same_year'] == 1).sum())}")
    log.info("pary: kandydaci %d, po filtrze (warstwy %s, same_year=%s, d0 wazne=%s): %d", len(cand), g.layers, g.same_year_only,
             g.require_valid_d0, len(sel))

    pairs = pd.DataFrame({
        "pair_id": sel["pair_id"], "session": sel["session_id"], "fwd": sel["fwd_d0"], "tsd": sel["d0_tsd"],
        "fwd_t12": sel["fwd_t12"], "tsd_t12": sel["tsd_t12"], "group": sel["group"], "dt_days": sel["dt_days"],
        "gof_share": sel["win5_gof05_share"], "corridor": sel["corridor_id"], "station": sel["station_id"],
        "device": sel["device"], "calib_interval": sel["calib_interval"], "tsd_year": sel["tsd_year"], "era": sel["era"],
        "fwd_date": sel["fwd_date"], "sigma_long": sel["sigma_long_fwd"]}).reset_index(drop=True)

    nulls = nulls_all[nulls_all["pair_id"].isin(sel["pair_id"])]
    nv = PA.null_values(nulls, pass_rows, "d0", g.window_m, g.min_rows)
    nulls_out = pd.DataFrame({"pair_id": nv["pair_id"], "null_type": nv["null_type"], "d0_w5": nv["value"],
                              "d0_valid_w5": nv["window_ok"].astype(int)})

    corr_tab = pd.DataFrame([dict(corridor_id=c.cid, length_m=c.length, x_start=c.x[0], y_start=c.y[0], x_end=c.x[-1], y_end=c.y[-1],
                                  n_pass=int((passes_df.corridor_id == c.cid).sum())) for c in corridors])
    meta = dict(axis=axis_info, n_runs=len(runs), n_stations=int(len(stations)), n_passes=int(len(passes_df)),
                n_candidates=int(len(cand)), n_pairs=int(len(sel)), n_null_pairs=int(len(nulls_out)),
                filters=dict(layers=g.layers, same_year_only=g.same_year_only, require_valid_d0=g.require_valid_d0,
                             window_m=g.window_m, min_rows=g.min_rows),
                lag_m=g.lag_m, eps_variant=g.eps_variant, sigma_era=ppar.sigma_era,
                antenna_rules=[asdict(r) for r in ppar.rules],
                lambda_estimate=lam_res,
                layers_count={k: int(v) for k, v in cand["layer"].value_counts().items()},
                sections=dict(enabled=g.sections.enabled, **{k: int(v) for k, v in sec_cnt.items()},
                              pairs_in_section=int(cand["in_section"].sum()) if "in_section" in cand else 0),
                note=("s_ref = s_ref_gps (bez wyrownania profilem), bez scalania duplikatow pasa; okno wartosci TSD wg s_ref "
                      "(+-%g m, >= %d wierszy z waznym d0). Polozenie TSD skorygowane o lag %+g m (jedna stala globalna)."
                      % (g.window_m, g.min_rows, g.lag_m)))
    lam_tab = (pd.DataFrame([dict(metric="d0", lambda_d0=lam_res["lambda_d0"], sigma_tsd=lam_res["sigma_tsd"], sigma_fwd=lam_res["sigma_fwd"],
                                  n_pairs_tsd=lam_res["n_pairs_tsd"], n_pairs_fwd=lam_res["n_pairs_fwd"],
                                  n_session_pairs_fwd=lam_res["n_session_pairs_fwd"], median_diff_log_tsd=lam_res["median_diff_log_tsd"],
                                  scale_m=lam_res["scale_m"], tsd_time_basis=lam_res["time_basis"],
                                  used_in_analysis=bool(g.lambda_est.apply))]) if lam_res else None)
    return dict(pairs=pairs, nulls=nulls_out, files=files, meta=meta, lambda_estimate=lam_res,
                tables=dict(geo_pairs=cand, geo_fwd=plate, geo_passes=passes_df, geo_corridors=corr_tab,
                            geo_nulls=nulls_all, geo_sessions=sessions, geo_runs=fwd_runs, geo_sections=sec_tab, lambda_estimate=lam_tab),
                section_report=(dict(sections=sec_tab, matches=sec_matches, runs=sec_runs, sessions=sec_sessions)
                                if g.sections.enabled else None))
