"""N4 tsd_fwd_compare, tryb `pairs`: miary zgodnosci TSD-FWD na gotowych parach geometrycznych.

Zasady: parowanie wylacznie geometryczne (tryb `pairs` przyjmuje pary juz zbudowane — nigdy wybor rekordu TSD wg wartosci
FWD); korekta obu stron do 20 C temperatura warstwy (T12) przed porownaniem; przedzialy — bootstrap po sesjach FWD oraz
metody dla malej liczby klastrow; kontrola zerowa i tabela warunkow; kalibracja z ocena poza proba."""

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
from ..common.config_n4 import N4Config
from ..common.stats_basic import seed_for
from .agreement import agreement_row, valid_pairs
from .calibration import calibration_table
from .conditions import conditions_table
from .corrections import correct_pair_values, default_beta_pct
from .nulls import align_null, paired_bootstrap_null
from .uncertainty import multiplier_intervals, paired_session_bootstrap

log = logging.getLogger(__name__)


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_pairs(cfg: N4Config) -> tuple[pd.DataFrame, dict]:
    """Wczytuje pary (+ temperatury, + dodatkowe kolumny) i zwraca DataFrame ze znormalizowanymi nazwami kolumn:
    pair_id, session, fwd, tsd, fwd_t12, tsd_t12 oraz opcjonalnie group, dt_days, gof_share, corridor, station,
    device, calib_interval, tsd_year, era, fwd_date, sigma_long."""
    inp, col = cfg.input, cfg.input.columns
    base = cfg.base_dir
    path = resolve_path(inp.pairs_csv, base)
    if not path.is_file():
        raise FileNotFoundError(f"brak pliku par: {path}")
    pairs = pd.read_csv(path, encoding="utf-8-sig")
    files = {"pairs_csv": str(path)}
    for key, p in (("t12_csv", inp.t12_csv), ("meta_csv", inp.meta_csv)):
        if p:
            pp = resolve_path(p, base)
            if not pp.is_file():
                raise FileNotFoundError(f"brak pliku {key}: {pp}")
            extra = pd.read_csv(pp, encoding="utf-8-sig")
            if col.pair_id not in extra or col.pair_id not in pairs:
                raise ConfigError(f"{key}: wymagana kolumna {col.pair_id!r} (klucz pair_id) w obu plikach")
            new = [c for c in extra.columns if c not in pairs.columns]
            pairs = pairs.merge(extra[[col.pair_id] + new], on=col.pair_id, how="left", validate="m:1")
            files[key] = str(pp)
    required = {"pair_id": col.pair_id, "session": col.session, "fwd": col.fwd, "tsd": col.tsd,
                "fwd_t12": col.fwd_t12, "tsd_t12": col.tsd_t12}
    missing = [v for v in required.values() if v not in pairs.columns]
    if missing:
        raise ConfigError(f"brak wymaganych kolumn w danych par: {missing} (dostepne: {list(pairs.columns)})")
    optional = {"group": col.group, "dt_days": col.dt_days, "gof_share": col.gof_share, "corridor": col.corridor,
                "station": col.station, "device": col.device, "calib_interval": col.calib_interval,
                "tsd_year": col.tsd_year, "era": col.era, "fwd_date": col.fwd_date, "sigma_long": col.sigma_long}
    out = pd.DataFrame({k: pairs[v] for k, v in required.items()})
    for k, v in optional.items():
        if v in pairs.columns:
            out[k] = pairs[v]
    for k in ("fwd", "tsd", "fwd_t12", "tsd_t12"):
        out[k] = pd.to_numeric(out[k], errors="coerce")
    return out, files


def _t12_flags(df: pd.DataFrame, lo: float, hi: float) -> np.ndarray:
    """Maska par, w ktorych T12 poza zakresem waznosci korekty (flagowane, nie usuwane)."""
    f, t = df["fwd_t12"].to_numpy(float), df["tsd_t12"].to_numpy(float)
    out = (np.isfinite(f) & ((f < lo) | (f > hi))) | (np.isfinite(t) & ((t < lo) | (t > hi)))
    return out | ~np.isfinite(f) | ~np.isfinite(t)


def run_n4(cfg: N4Config, dry_run: bool = False) -> dict:
    df, files = load_pairs(cfg)
    m, c, u = cfg.measures, cfg.correction, cfg.uncertainty
    beta_pct = default_beta_pct() if c.beta_pct is None else c.beta_pct
    sess = df["session"].to_numpy()
    fwd0, tsd0 = df["fwd"].to_numpy(float), df["tsd"].to_numpy(float)
    ok_base = valid_pairs(fwd0, tsd0)
    log.info("pary: %d, z D0/d0 > 0: %d, sesji: %d", len(df), int(ok_base.sum()), len(np.unique(sess[ok_base])))
    outside = _t12_flags(df, *c.flag_outside_c)

    corrected = {}
    for tr in c.treatments:
        corrected[tr] = correct_pair_values(fwd0, tsd0, df["fwd_t12"], df["tsd_t12"], tr, beta_pct, c.t_ref_c)
    main_f, main_t = corrected[c.main_treatment]

    # --- miary zgodnosci: wszystkie warianty ---
    rows = []
    for tr, (f, t) in corrected.items():
        rows.append(agreement_row(f, t, sess, m.lambda_d0, m.n_boot, {"variant": tr}, m.seed_ci))
    agreement = pd.DataFrame(rows)

    # --- grupy aparat x rok: przed i po korekcie ---
    groups_df = pd.DataFrame()
    if "group" in df:
        grp = df["group"].astype(str).to_numpy()
        g_rows = []
        for g in sorted(set(grp[ok_base].tolist())):
            gm = ok_base & (grp == g)
            for tr in ("none", c.main_treatment):
                if tr not in corrected:
                    continue
                f, t = corrected[tr]
                r = agreement_row(f[gm], t[gm], sess[gm], m.lambda_d0, m.n_boot, {"group": g, "variant": tr}, m.seed_ci)
                r["n_total_group"] = int(gm.sum())
                g_rows.append(r)
        groups_df = pd.DataFrame(g_rows)

    # --- bootstrap sparowany (przed vs po korekcie, po sesjach) ---
    before_after = {}
    if "none" in corrected and c.main_treatment != "none" and "group" in df:
        fb, tb = corrected["none"]
        before_after = paired_session_bootstrap(fb, tb, main_f, main_t, df["group"].astype(str).to_numpy(), sess,
                                                m.n_boot, m.seed_paired)

    # --- przedzialy mnoznika przy malej liczbie klastrow ---
    mult_rows = []
    ok_main = valid_pairs(main_f, main_t)
    if ok_main.sum() >= 3 and u.methods:
        lr = np.log(main_f[ok_main]) - np.log(main_t[ok_main])
        mult_rows = multiplier_intervals(lr, sess[ok_main], u.replicates, u.seed_tag, seed_for, u.h0_multiplier,
                                         tuple(u.methods))
    multiplier = pd.DataFrame(mult_rows)

    # --- funkcja przeliczajaca: mnoznik, gdy Deming log-log obejmuje 1 ---
    row_main = agreement[agreement["variant"] == c.main_treatment].iloc[0]
    lo_s, hi_s = row_main["deming_loglog_slope_lo"], row_main["deming_loglog_slope_hi"]
    proportional = bool(np.isfinite(lo_s) and np.isfinite(hi_s) and lo_s <= 1.0 <= hi_s)
    if proportional:
        conversion = dict(form="proportional", description="D0_FWD,20 = factor * d0_TSD,20", factor=row_main["median_ratio"],
                          factor_lo=row_main["median_ratio_lo"], factor_hi=row_main["median_ratio_hi"], n=int(row_main["n_pairs"]))
    else:
        conversion = dict(form="deming_linear", description="D0_FWD,20 = a * d0_TSD,20 + b (Deming liniowy)",
                          slope_a=row_main["deming_linear_a"], slope_a_lo=row_main["deming_linear_a_lo"],
                          slope_a_hi=row_main["deming_linear_a_hi"], intercept_b=row_main["deming_linear_b"],
                          intercept_b_lo=row_main["deming_linear_b_lo"], intercept_b_hi=row_main["deming_linear_b_hi"],
                          n=int(row_main["n_pairs"]))
    conversion["deming_loglog_slope_includes_1"] = proportional
    conversion["caveat"] = ("mnoznik policzony takze dla par z T12 poza zakresem waznosci korekty (flagowane w pairs_corrected.csv)"
                            if outside.any() else "")

    # --- tabela warunkow ---
    conditions = pd.DataFrame()
    if cfg.conditions.enabled:
        conditions = conditions_table(main_f, main_t, fwd0, df, tuple(cfg.conditions.group_by), cfg.conditions.cv_unit,
                                      receiver_cutoff=cfg.conditions.receiver_cutoff)

    # --- kalibracja z ocena poza proba (z pominieciem sesji) ---
    calib = pd.DataFrame()
    if cfg.calibration.enabled:
        cf, ct = corrected.get(cfg.calibration.treatment) or correct_pair_values(
            fwd0, tsd0, df["fwd_t12"], df["tsd_t12"], cfg.calibration.treatment, beta_pct, c.t_ref_c)
        calib = calibration_table(ct, cf, sess, tuple(cfg.calibration.models), label=cfg.calibration.treatment)

    # --- kontrola zerowa ---
    null_rows, null_delta = [], []
    inp = cfg.input
    if inp.null_pairs_csv:
        npath = resolve_path(inp.null_pairs_csv, cfg.base_dir)
        if not npath.is_file():
            raise FileNotFoundError(f"brak pliku par zerowych: {npath}")
        nd = pd.read_csv(npath, encoding="utf-8-sig")
        files["null_pairs_csv"] = str(npath)
        real_row = agreement_row(main_f, main_t, sess, m.lambda_d0, cfg.null_checks.n_boot,
                                 {"pair_kind": "real"}, cfg.null_checks.seed)
        null_rows.append(real_row)
        for nt in sorted(nd[inp.null_type_col].dropna().unique()):
            tn = align_null(df.assign(pair_id=df["pair_id"]), nd, nt, inp.null_type_col, inp.null_tsd_col,
                            inp.null_valid_col, "pair_id").to_numpy(float)
            f_n, t_n = correct_pair_values(fwd0, tn, df["fwd_t12"], df["tsd_t12"], c.main_treatment, beta_pct, c.t_ref_c)
            null_rows.append(agreement_row(f_n, t_n, sess, m.lambda_d0, cfg.null_checks.n_boot,
                                           {"pair_kind": nt}, cfg.null_checks.seed))
            null_delta.append({"null_type": nt, **paired_bootstrap_null(f_n, main_t, t_n, sess, cfg.null_checks.n_boot,
                                                                       cfg.null_checks.seed)})
    nulls = pd.DataFrame(null_rows)
    null_delta_df = pd.DataFrame(null_delta)

    pairs_out = df.copy()
    pairs_out["t12_outside_or_missing"] = outside
    pairs_out["valid_pair"] = ok_base
    pairs_out[f"fwd_{c.main_treatment}"] = main_f
    pairs_out[f"tsd_{c.main_treatment}"] = main_t

    meta = {
        "tool": "tsd_fwd_compare", "mode": "pairs", "version": __version__,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {k: {"file": v, "md5": _md5(Path(v))} for k, v in files.items()},
        "config": {"correction": asdict(c), "measures": asdict(m), "uncertainty": asdict(u),
                   "conditions": asdict(cfg.conditions), "calibration": asdict(cfg.calibration)},
        "beta_pct_used": beta_pct,
        "n_pairs": int(len(df)), "n_valid_pairs": int(ok_base.sum()), "n_sessions": int(len(np.unique(sess[ok_base]))),
        "n_t12_outside_or_missing": int(outside.sum()),
        "before_after": {k: (list(v) if isinstance(v, tuple) else v) for k, v in before_after.items()},
        "conversion": conversion,
        "note": ("Parowanie wylacznie geometryczne; korekta obu stron do 20 C temperatura warstwy (T12). "
                 "Mnoznik jest wazny dla wartosci odcinkowych (>= 100 m) i wymaga weryfikacji dla danego aparatu FWD "
                 "i okresu kalibracji TSD; krzywizn (SCI300/BDI/BCI) tryb pairs nie przelicza."),
    }
    result = {"agreement": agreement, "groups": groups_df, "multiplier": multiplier, "conditions": conditions,
              "calibration": calib, "nulls": nulls, "null_delta": null_delta_df, "pairs": pairs_out,
              "conversion": pd.DataFrame([conversion]), "before_after": before_after, "meta": meta, "outputs": []}
    if not dry_run:
        from .output import write_n4
        result["outputs"] = write_n4(cfg, result)
    return result
