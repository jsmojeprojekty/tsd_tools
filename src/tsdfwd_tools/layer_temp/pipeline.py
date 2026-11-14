"""N2 layer_temp: wczytanie tabeli pomiarow, obliczenie temperatury warstwy (fizyka 1-D + kalibracja do pirometru), zapis wynikow.

Wejscie: CSV z kolumnami czasu (lokalny, naiwny z DST), pozycji (WGS84) i odczytu pirometru; opcjonalnie id i kolumny
przepisywane do wyniku (np. `chainage_m`, `file` - wtedy wynik jest wejsciem temperatury warstwy dla N3).
Dokladnosc: RMSE 1,75 C na zbiorze eksploracyjnym H (549 obs.), 2,73 C na niezaleznym zbiorze C; wartosc u95 jest heurystyka."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from datetime import datetime

import numpy as np
import pandas as pd

from .. import __version__
from ..common.config import ConfigError, resolve_path
from ..common.config_n2 import N2Config, effective_depth_cm
from .constants import PROTOCOL_VERSION
from .flags import LayerFlag, flags_to_text
from .meteo import MeteoStore
from .params import load_params
from .predict import QcSettings, run_survey

log = logging.getLogger(__name__)

ACCURACY_NOTE = ("RMSE 1,75 C na zbiorze eksploracyjnym H (549 obserwacji, 226 sesji; to test powtarzalnosci); na niezaleznym "
                 "zbiorze C RMSE 2,73 C. Model TN (teren otwarty) nie obejmuje terenu zacienionego (bias +3..+5 C). "
                 "u95 = 2*RMSE wg pory doby (nie mniej niz 2,2 C) jest heurystyka narzedzia, nie gwarantowanym przedzialem.")


def read_survey(cfg: N2Config) -> pd.DataFrame:
    i = cfg.input
    path = resolve_path(i.survey_csv, cfg.base_dir)
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku pomiarow: {path}")
    df = pd.read_csv(path, encoding=i.encoding, sep=i.sep)
    need = [i.time_column, i.lat_column, i.lon_column, i.ir_column]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ConfigError(f"{path.name}: brak kolumn {miss} (dostepne: {list(df.columns)}); nazwy ustawia sekcja input")
    for c in ([i.id_column] if i.id_column else []) + list(i.passthrough):
        if c not in df.columns:
            raise ConfigError(f"{path.name}: brak kolumny {c!r} (id_column/passthrough)")
    return df.reset_index(drop=True)


def _params_path(cfg: N2Config):
    pf = cfg.model.params_file
    return pf if pf.startswith("builtin:") else resolve_path(pf, cfg.base_dir)


def run_n2(cfg: N2Config, dry_run: bool = False, *, http_get=None) -> dict:
    t0 = time.time()
    i, m = cfg.input, cfg.model
    raw = read_survey(cfg)
    depth_cm = effective_depth_cm(cfg)
    params = load_params(_params_path(cfg))
    store = MeteoStore(resolve_path(cfg.meteo.cache_dir, cfg.base_dir), offline=cfg.meteo.offline,
                       grid_deg=cfg.meteo.grid_deg, http_get=http_get)
    surv = pd.DataFrame({
        "measured_at_local": pd.to_datetime(raw[i.time_column], errors="coerce"),
        "latitude": pd.to_numeric(raw[i.lat_column], errors="coerce"),
        "longitude": pd.to_numeric(raw[i.lon_column], errors="coerce"),
        "t_surface": pd.to_numeric(raw[i.ir_column], errors="coerce")})
    valid = surv["measured_at_local"].notna() & np.isfinite(surv["latitude"]) & np.isfinite(surv["longitude"])
    if (~valid).any():
        log.warning("N2: %d wierszy bez poprawnego czasu lub pozycji - wynik NaN (flagi METEO_GAP, CALIB_NOSIM)", int((~valid).sum()))
    qc = QcSettings(season_months=tuple(int(x) for x in cfg.qc.season_months), snow_depth_max_m=cfg.qc.snow_depth_max_m,
                    night_sw_wm2=cfg.qc.night_sw_wm2)
    res = run_survey(surv[valid], store, params, depth_cm=depth_cm, calibration=m.calibration, qc=qc,
                     with_bells3=cfg.comparators.bells3, grid_deg=cfg.meteo.grid_deg, history_days=cfg.meteo.history_days)
    res = res.reindex(surv.index)
    bad = ~valid
    if bad.any():
        res.loc[bad, "calib_flag"] = "nosim"
        res.loc[bad, "qc_flags"] = int(LayerFlag.METEO_GAP | LayerFlag.CALIB_NOSIM)
    res["qc_flags"] = res["qc_flags"].astype(int)

    table = pd.DataFrame(index=surv.index)
    table["id"] = raw[i.id_column] if i.id_column else np.arange(1, len(raw) + 1)
    table["measured_at_local"] = surv["measured_at_local"]
    table["latitude"] = surv["latitude"]
    table["longitude"] = surv["longitude"]
    table["t_surface"] = surv["t_surface"]
    if i.air_column and i.air_column in raw.columns:
        table["t_air"] = pd.to_numeric(raw[i.air_column], errors="coerce")
    table["depth_cm"] = depth_cm
    for c in ("t_layer", "u95", "a_sw", "ts_sim", "calib_flag", "grid_lat", "grid_lon", "sw_ma6", "qc_flags"):
        table[c] = res[c]
    table["flags_text"] = [flags_to_text(x) for x in res["qc_flags"]]
    table["t_layer_uncal"] = res["t_layer_uncal"]
    table["ir_masa"] = res["ir_masa"]
    if "bells3_c" in res:
        table["bells3_c"] = res["bells3_c"]
    if abs(depth_cm - 12.0) < 1e-9:
        table["t12_c"] = res["t_layer"]                      # nazwa kolumny oczekiwana domyslnie przez N3 (layer_temp.column)
    for c in i.passthrough:
        if c not in table:
            table[c] = raw[c]

    flag_counts = {f.name: int(((table["qc_flags"].to_numpy() & f.value) > 0).sum()) for f in LayerFlag if f.name != "NONE"}
    meta = {
        "tool": "layer_temp", "version": __version__, "protocol": PROTOCOL_VERSION, "created": datetime.now().isoformat(timespec="seconds"),
        "n_rows": int(len(table)), "n_valid_t_layer": int(table["t_layer"].notna().sum()),
        "depth_cm": depth_cm, "calibration": m.calibration, "terrain_class": m.terrain_class,
        "calib_flags": {k: int(v) for k, v in table["calib_flag"].value_counts().items()},
        "qc_flag_counts": {k: v for k, v in flag_counts.items() if v},
        "params": {"name": params.name, "hash_sha256": params.hash, "source": params.meta.get("source")},
        "meteo": {"provider": cfg.meteo.provider, "offline": cfg.meteo.offline, "n_requests_made": store.n_fetched,
                  "time_basis": "local_Europe_Warsaw_DST_from_UTC", "api_timezone_param": "UTC",
                  "grid_deg": cfg.meteo.grid_deg, "history_days": cfg.meteo.history_days,
                  "n_grid_cells": int(table[["grid_lat", "grid_lon"]].dropna().drop_duplicates().shape[0])},
        "accuracy_note": ACCURACY_NOTE, "config": asdict(cfg), "elapsed_s": round(time.time() - t0, 2),
    }
    out = {"table": table, "meta": meta, "outputs": []}
    if not dry_run:
        from .output import write_n2
        out["outputs"] = write_n2(cfg, table, meta)
    return out
