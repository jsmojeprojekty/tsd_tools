"""N3 tsd_network: przetwarzanie eksportu TSD B_1510off na sieci.

Kolejnosc (raport 7.3, decyzje Jacka 2026-11-14): wiersz 1 m -> korekta d0 do 20 C (T12 warstwy z N2/modelu; NIGDY pirometr)
-> Hampel na d0_20 z odrzutem calej czaszy -> mediana w oknie +-5 m (mediana CALEK, nie calka z mediany) -> agregacja
50/100 m -> eksport XML DSN (UC, zal. H p. 4.2). Calki P0 nie sa korygowane temperaturowo (raport 6.1). Skala wartosci: TSD
(przeliczenie na skale FWD tylko opcjonalnie)."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .. import __version__
from ..common.config import ConfigError, resolve_path
from ..common.config_n3 import N3Config
from .constants import CHANNELS_9, INTEGRAL_NAMES
from .filters import hampel_outliers, window_rows
from .flags import TsdFlag, flags_to_text
from .integrals import p0_integrals
from .io import TsdRun, read_b1510off
from .qc import gps_gyro_qc, gps_valid
from .fwd_scale import fwd_factor
from .tempcorr import correct_d0, default_beta_pct, to_fwd_scale
from .uc_export import write_uc_xml
from .window import aggregate_bins, window_medians

log = logging.getLogger(__name__)

INT_COLS = ["a020", "a030", "a031", "a061", "a090", "a091", "a0361", "a6191"]
WIN_VALUE_COLS = ["d0_20", "d0", "t12_c", "speed_kmh", "temp_road", "temp_air", "strain_right_kg"] + INT_COLS


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _stem(name: str) -> str:
    return name.split(".")[0]


def load_layer_temperature(cfg: N3Config, run_name: str, chain: np.ndarray) -> tuple[np.ndarray, str]:
    """T12 [C] interpolowana liniowo wzdluz pikietazu (NaN poza zakresem danych); zwraca (t12, etykieta zrodla)."""
    lt = cfg.layer_temp
    if lt.source == "constant":
        return np.full(len(chain), float(lt.constant_c)), "constant"
    if lt.source == "none":
        return np.full(len(chain), np.nan), "none"
    path = resolve_path(lt.csv, cfg.base_dir)
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku z temperatura warstwy: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    for need in (lt.pos_column, lt.column):
        if need not in df:
            raise ConfigError(f"{path.name}: brak kolumny {need!r} (dostepne: {list(df.columns)})")
    if lt.file_column in df:
        df = df[df[lt.file_column].astype(str).map(_stem) == _stem(run_name)]
        if df.empty:
            raise ConfigError(f"{path.name}: brak wierszy dla pliku {run_name!r} (kolumna {lt.file_column!r})")
    df = df.dropna(subset=[lt.pos_column, lt.column]).sort_values(lt.pos_column)
    if df.empty:
        raise ConfigError(f"{path.name}: brak waznych wartosci temperatury")
    x = df[lt.pos_column].to_numpy(float)
    y = df[lt.column].to_numpy(float)
    t = np.interp(chain, x, y, left=np.nan, right=np.nan)
    return t, f"csv:{path.name}:{lt.column}"


def process_run(cfg: N3Config, path: Path) -> dict:
    p = cfg.processing
    run: TsdRun = read_b1510off(path, cfg.input.expected_step_m)
    if run.file_flags & int(TsdFlag.FILE_NOT_RECALIBRATED):
        # pusty 'Re-calibrationfile' = eksport nominalny (z czujnikiem 1,51 m); jego d0 nie jest zrodlem ugiecia w N3 (decyzja Jacka)
        raise ConfigError(f"{path.name}: eksport nominalny (pusty 'Re-calibrationfile'); N3 przyjmuje wylacznie eksport B_1510off "
                          "(d0 przeliczone z 9 czujnikow nachylen, bez czujnika 1,51 m)")
    ff = fwd_factor(cfg)                                     # przelicznik TSD->FWD (None, gdy nie podano)
    d = run.data.copy().reset_index(drop=True)
    n = len(d)
    chain = d["chainage_m"].to_numpy(float)
    d["pos_m"] = chain - p.position_offset_m          # konwencja lagu (tsd_position_offset = -4,8): punkt pomiaru lezy o 4,8 m dalej niz pikietaz wiersza
    d["speed_kmh"] = d["speed_ms"] * 3.6

    t12, t_source = load_layer_temperature(cfg, path.name, chain)
    d["t12_c"] = t12
    beta_pct = p.correction.beta_pct if p.correction.beta_pct is not None else default_beta_pct()
    d0 = d["d0"].to_numpy(float)
    d0_ok = np.isfinite(d0) & (d0 > 0)
    d0_20, tflags = correct_d0(np.where(d0_ok, d0, np.nan), t12, beta_pct, tuple(p.correction.range_c), p.correction.t_ref_c)
    if cfg.layer_temp.source == "none":
        d0_20 = np.where(d0_ok, d0, np.nan)                      # d0 bez korekty (allow_uncorrected)
    flags = tflags.copy()
    flags[~d0_ok] |= int(TsdFlag.D0_INVALID)
    d["d0_20"] = d0_20

    # calki P0 z 9 nachylen (bez 1,51 m); bez korekty temperaturowej
    slopes = d[[f"slope_{c}" for c in CHANNELS_9]].to_numpy(float)
    integ = p0_integrals(slopes, step_m=p.integral_step_m)
    for name in INT_COLS:
        d[name] = integ[name]
    flags[~np.isfinite(slopes).all(axis=1)] |= int(TsdFlag.SLOPE_MISSING)
    nonpos = np.zeros(n, dtype=bool)
    for name in ("a031", "a0361", "a6191"):
        nonpos |= np.isfinite(integ[name]) & (integ[name] <= 0)
    flags[nonpos] |= int(TsdFlag.INTEGRAL_NONPOSITIVE)
    flags[np.isfinite(integ["a031"])] |= int(TsdFlag.P0_UNCORRECTED)

    # Hampel na d0_20: odrzut calej czaszy (d0 i calki)
    step = float(np.nanmedian(np.diff(chain))) if n > 2 else 1.0
    rej = np.zeros(n, dtype=bool)
    if p.hampel.enabled and n > 3:
        rej = hampel_outliers(d0_20, window_rows(p.hampel.window_m, step), p.hampel.k)
    flags[rej] |= int(TsdFlag.D0_HAMPEL_REJECTED)
    d["hampel_rejected"] = rej
    for col in ["d0_20"] + INT_COLS:
        d.loc[rej, col] = np.nan

    gv = gps_valid(d["lat"], d["lon"])
    flags[~gv] |= int(TsdFlag.GPS_INVALID)
    qc = {}
    if cfg.qc.gps_gyro:
        qc = gps_gyro_qc(d, tuple(cfg.qc.window_rows), cfg.qc.r_min, cfg.qc.omega_std_min)
        if qc.get("verdict") != "OK":
            run.file_flags |= int(TsdFlag.GYRO_GPS_NOT_OK)
    flags |= run.file_flags
    d["flags"] = flags
    d["flags_text"] = [flags_to_text(m) for m in flags]
    if p.to_fwd_scale_enabled:
        d["d0_fwd20"] = to_fwd_scale(d["d0_20"], ff["factor"])

    # okno +-5 m: mediana kolumn (centra co step_m XML lub co 10 m)
    step_xml = cfg.xml_uc.step_m
    lo_c, hi_c = np.nanmin(d["pos_m"]), np.nanmax(d["pos_m"])
    centers = np.arange(np.ceil(max(lo_c, step_xml) / step_xml) * step_xml, hi_c + 1e-9, step_xml)
    wins = window_medians(d.assign(chainage_m=d["pos_m"]), centers, p.window_m, WIN_VALUE_COLS, "chainage_m", "d0_20", "gof",
                          p.gof_threshold, p.min_rows_in_window)
    wins = _window_flags(wins, p.correction.range_c, p.gof_threshold)
    aggs = {}
    for a in p.aggregate_m:
        agg = aggregate_bins(d.assign(chainage_m=d["pos_m"]), float(a), ["d0_20", "t12_c", "speed_kmh"] + INT_COLS,
                             "chainage_m", "d0_20", "gof", p.gof_threshold, p.min_rows_in_window)
        if p.to_fwd_scale_enabled:
            agg["d0_fwd20"] = to_fwd_scale(agg["d0_20"], ff["factor"])
        agg["flags_text"] = [flags_to_text(m) for m in _bin_flags(agg, p.correction.range_c, p.gof_threshold)]
        aggs[int(a)] = agg

    summary = {
        "file": path.name, "n_rows": int(n), "date": run.date.isoformat() if run.date else "",
        "step_m": step, "n_valid_d0": int(d0_ok.sum()), "n_hampel_rejected": int(rej.sum()),
        "t_source": t_source, "n_t12_missing": int(np.isnan(t12).sum()),
        "gyro_gps_verdict": qc.get("verdict", ""), "gyro_gps_r": qc.get("r_max", np.nan), "gyro_gps_lag_rows": qc.get("lag_max"),
        "d0_20_median": float(np.nanmedian(d["d0_20"])) if np.isfinite(d["d0_20"]).any() else np.nan,
    }
    for f in TsdFlag:
        if f.name != "NONE":
            summary[f"share_{f.name.lower()}"] = float(np.mean((flags & int(f)) != 0)) if n else 0.0
    meta = {
        "tool": "tsd_network", "version": __version__, "created_at": datetime.now().isoformat(timespec="seconds"),
        "input": {"file": str(path), "md5": _md5(path)}, "header": run.meta, "notes": run.notes,
        "layer_temperature": t_source,
        "correction": {"form": "exponential", "beta_pct": beta_pct, "range_c": p.correction.range_c, "t_ref_c": p.correction.t_ref_c},
        "hampel": asdict(p.hampel), "window_m": p.window_m, "min_rows_in_window": p.min_rows_in_window,
        "integral": {"method": "pchip_dense_trapezoid", "step_m": p.integral_step_m, "channels": list(CHANNELS_9),
                     "integrals_corrected": False},
        "position_offset_m": p.position_offset_m, "scale": "tsd", "fwd_scale": ff, "qc_gps_gyro": {k: v for k, v in qc.items()},
        "note": ("Calki P0 nie sa korygowane temperaturowo (raport 6.1); D_x = d0_20 - P0(x) (d0 skorygowane, calka nie). "
                 "Wartosci DSN (XML) w skali FWD: D_0 jest przeliczone mnoznikiem z N4 (zweryfikowanym dla d0); dla D_200, D_300 i SCI mnoznik jest niezweryfikowany."),
    }
    return {"run": run, "rows": d, "windows": wins, "aggs": aggs, "summary": summary, "meta": meta, "qc": qc}


def _window_flags(wins: pd.DataFrame, range_c, gof_min: float) -> pd.DataFrame:
    flags = np.zeros(len(wins), dtype=np.int64)
    flags[~wins["window_ok"].to_numpy(bool)] |= int(TsdFlag.WINDOW_FEW_ROWS)
    share = wins["gof_share_ge05"].to_numpy(float)
    flags[np.isfinite(share) & (share < 0.5)] |= int(TsdFlag.LOW_GOF_SHARE)
    t = wins["t12_c"].to_numpy(float)
    lo, hi = range_c
    flags[~np.isfinite(t)] |= int(TsdFlag.T_MISSING)
    flags[np.isfinite(t) & (t < lo)] |= int(TsdFlag.T_BELOW_5C)
    flags[np.isfinite(t) & (t > hi)] |= int(TsdFlag.T_ABOVE_RANGE)
    flags[np.isfinite(wins["a031"].to_numpy(float))] |= int(TsdFlag.P0_UNCORRECTED)
    nonpos = np.zeros(len(wins), dtype=bool)
    for c in ("a031", "a0361", "a6191"):
        v = wins[c].to_numpy(float)
        nonpos |= np.isfinite(v) & (v <= 0)
    flags[nonpos] |= int(TsdFlag.INTEGRAL_NONPOSITIVE)
    out = wins.copy()
    out["flags"] = flags
    out["flags_text"] = [flags_to_text(m) for m in flags]
    return out


def _bin_flags(agg: pd.DataFrame, range_c, gof_min: float) -> np.ndarray:
    return _window_flags(agg.assign(a0361=agg["a0361"], a6191=agg["a6191"]), range_c, gof_min)["flags"].to_numpy()


def build_xml_records(cfg: N3Config, result: dict) -> pd.DataFrame:
    """Rekordy pola DSN `UC` (profil dsn_h42) z okien +-5 m co step_m: D_0 = d0_20 (mediana), D_x = D_0 - P0(x) (mediany),
    SCI_200 = D_0 - D_200 (calka 0-0,20 m), SCI_300 = D_0 - D_300 (calka 0-0,31 m, podawane jako 300); SCI_SUB zostaje pustym elementem (decyzja Jacka: pole pomijane);
    wartosci w skali FWD (xml_uc.scale: fwd, domyslnie; mnoznik z N4) albo TSD (xml_uc.scale: tsd)."""
    x = cfg.xml_uc
    run, d, w = result["run"], result["rows"], result["windows"]
    date = x.date_override or (run.date.isoformat() if run.date else None)
    if not date:
        raise ConfigError(f"{Path(run.source).name}: brak daty w nazwie pliku - podaj xml_uc.date_override (RRRR-MM-DD)")
    pos = d["pos_m"].to_numpy(float)
    order = np.argsort(pos, kind="stable")
    pos_s = pos[order]
    sign = 1.0 if x.km_direction == "increasing" else -1.0
    recs = []
    mult = fwd_factor(cfg)["factor"] if x.scale == "fwd" else 1.0
    for _, r in w.iterrows():
        c = r["center_m"]
        j = order[int(np.clip(np.searchsorted(pos_s, c), 0, len(pos_s) - 1))]
        j2 = order[max(int(np.searchsorted(pos_s, c)) - 1, 0)]
        if abs(pos[j2] - c) < abs(pos[j] - c):
            j = j2
        d0m = r["d0_20"]
        sci200, sci300 = r["a020"], r["a031"]            # SCI_300 / D_300: calka 0-0,31 m (polozenie czujnika), podawana jako 300 (Q-N3-16)
        sec = d["gps_time_s"].iloc[j]
        godz = ""
        if np.isfinite(sec):
            s = int(round(sec)) % 86400
            godz = f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
        recs.append({
            "KM": x.km_start + sign * (c - x.chainage_start_m) / 1000.0,
            "DYSTANS": int(round(c)), "DROGA": str(x.droga), "JEZDNIA": x.jezdnia, "PAS": x.pas,
            "LAT": d["lat"].iloc[j], "LON": d["lon"].iloc[j], "DATA": date, "GODZ": godz, "IRI_1": None, "PROFIL_1": None,
            "PREDKOSC": r["speed_kmh"], "STRAIN_GAUGE": r["strain_right_kg"], "T_DROGI": r["temp_road"], "T_POW": r["temp_air"],
            "SCI_200": sci200 * mult, "SCI_300": sci300 * mult, "SCI_SUB": None,
            "D_0": d0m * mult, "D_200": (d0m - sci200) * mult, "D_300": (d0m - sci300) * mult,
        })
    return pd.DataFrame(recs)


def run_n3(cfg: N3Config, dry_run: bool = False) -> dict:
    results = []
    for f in cfg.input.tsd_files:
        path = resolve_path(f, cfg.base_dir)
        log.info("przetwarzam %s", path.name)
        res = process_run(cfg, path)
        if cfg.xml_uc.enabled:
            res["xml_records"] = build_xml_records(cfg, res)
        results.append(res)
    out = {"runs": results, "outputs": []}
    if not dry_run:
        from .output import write_n3
        out["outputs"] = write_n3(cfg, results)
    return out
